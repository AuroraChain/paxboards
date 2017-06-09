from __future__ import print_function

from django.db import models
from evennia.typeclasses.managers import (TypedObjectManager, TypeclassManager,
                                          returns_typeclass_list, returns_typeclass)

_GA = object.__getattribute__
_PlayerDB = None
_ObjectDB = None
_BoardDB = None
_SESSIONS = None


def is_positive_int(string):
    """
    Tests whether the given string is a plain, positive integer.

    Args:
        string (str): A string to test.

    Returns:
        True if the string is an integer greater than 0, False if not.
    """
    try:
        test = int(string)
        if test > 0:
            return True
        return False
    except ValueError:
        return False


class PostQuerySet(models.query.QuerySet):

    def by_board_all(self, board):
        """
        Returns all the posts on a board, regardless of expiry limits.

        Args:
            board (Board): The BoardDB object to use.

        Returns:
            A list of posts.

        """
        return self.filter(db_board=board)

    def by_board(self, board):
        """
        Returns all the active posts on a board, honoring expiry limits.

        Args:
            board (Board): The BoardDB object to use.

        Returns:
            A list of Post objects.

        """
        try:
            if board.db_expiry_duration:
                oldest = datetime.now() - timedelta(days=board.db_expiry_duration)
                posts = self.filter(db_board=board, db_date_created__gte=oldest)\
                    .order_by('db_date_created')
            else:
                posts = self.filter(db_board=board).order_by('db_date_created')

            if board.db_expiry_maxposts and board.db_expiry_maxposts > 0:
                posts = posts[-board.db_expiry_maxposts:]

            return posts

        except self.model.DoesNotExist:
            return []

    def by_board_for_player(self, board, player):
        """
        Returns all the active posts on a board, with an 'unread' field based on the current user's
        read or unread status.

        Args:
            board (BoardDB): The board whose posts should be checked.
            player (PlayerDB): The player whose read/unread status should be used.

        Returns:
            A list of Post objects.

        """
        posts = self.by_board(board)
        for p in posts:
            if player.read_posts.filter(pk=p.id).exists():
                setattr(p,"db_unread",False)
            else:
                setattr(p,"db_unread",True)

        return posts


class PostManager(TypedObjectManager):

    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    @returns_typeclass
    def post(self, id):
        return self.get_queryset().get(pk=id)

    @returns_typeclass_list
    def posts(self, board, player=None):
        """
        Given a board and an optional player, returns the posts

        Args:
            board:
            player:

        Returns:

        """
        if not player:
            return self.get_queryset().by_board(board)
        else:
            return self.get_queryset().by_board_for_player(board, player)

    @returns_typeclass_list
    def search(self, searchstring, board=None):
        if board:
            result = self.get_queryset().by_board(board).filter(db_text__icontains=searchstring).\
                order_by('db_date_created')
        else:
            result = self.get_queryset().filter(db_text__icontains=searchstring).order_by('db_date_created')

        return result


class BoardDBManager(TypedObjectManager):
    """
    This BoardManager implements methods for searching and
    manipulating Boards directly from the database.

    These methods will all return database objects (or QuerySets)
    directly.

    """

    @returns_typeclass_list
    def get_all_boards(self):
        """
        Returns all boards.

        Returns:
            A list of DefaultBoard objects.
        """
        return self.all()

    @returns_typeclass
    def get_board_id(self, id):
        return self.get(pk=id)

    @returns_typeclass
    def get_board(self, key):
        """
        Returns a specific board beginning with the key.

        Args:
            key (str): A string to match against board names.

        Returns:
            A DefaultBoard object, or None
        """
        board = self.get_board_exact(key)
        if board:
            return board

        try:
            boards = self.filter(db_key__istartswith=key)
            if boards:
                if len(boards) == 1:
                    return boards[0]

            return None
        except self.model.DoesNotExist:
            return None

    @returns_typeclass
    def get_board_exact(self, key):
        """
        Returns a specific board matching the key.

        Args:
            key (str): A string to match against board names.

        Returns:
            A DefaultBoard object, or None
        """
        try:
            board = self.get(db_key__iexact=key)
            if board:
                return board

            return None
        except self.model.DoesNotExist:
            return None


    @returns_typeclass_list
    def get_all_visible_boards(self, caller):
        """
        This function returns all the boards visible to a given viewer.

        Args:
            caller (Player): The player whose visibility of boards should be checked.

        Returns:
            A list of DefaultBoard objects.
        """
        filtered = []
        if caller:
            filtered = [b for b in self.all() if b.access(caller, access_type='read', default=True)]

        for b in filtered:
            all_posts = b.posts(caller)
            unread = 0
            for p in all_posts:
                if p.db_unread:
                    unread = unread + 1

            setattr(b,"db_unread_count", unread)
            setattr(b,"db_total_count", len(all_posts))

        return filtered

    @returns_typeclass
    def get_visible_board(self, viewer, key):
        """
        This function returns a single board matching the key, provided it's unique.

        Args:
            viewer (Player): The player whose visibility of boards should be checked.
            key (str): The string to match board names again.

        Returns:
            A DefaultBoard object, or None.
        """
        if is_positive_int(key):
            boards = self.get_all_visible_boards(viewer)
            boardnum = int(key)
            if 0 < boardnum <= len(boards):
                return boards[boardnum - 1]

            return None

        boards = self.filter(db_key__istartswith=key)
        if boards:
            filtered = [b for b in boards if b.access(viewer, access_type='read', default=True)]
            if len(filtered) == 1:
                b = filtered[0]

                all_posts = b.posts(viewer)
                unread = 0
                for p in all_posts:
                    if p.db_unread:
                        unread = unread + 1

                setattr(b, "db_unread_count", unread)
                setattr(b, "db_total_count", len(all_posts))

                return b

        return None

    @returns_typeclass_list
    def get_subscriptions(self, subscriber):
        """
        This function returns a list of boards a given user is subscribed to.

        Args:
            subscriber (Player): The player whose subscriptions should be checked.

        Returns:
            A list of boards subscribed to.

        """
        clsname = subscriber.__dbclass__.__name__
        if clsname == "PlayerDB":
            return subscriber.board_subscriptions_set.all()

        return []


class BoardManager(BoardDBManager, TypeclassManager):
    """
    Wrapper class to group Typeclass manager and Board manager functionality together.
    """
    pass
