from __future__ import print_function

from django.db import models
from django.db.models import Q
from itertools import chain
from datetime import datetime
from evennia.typeclasses.managers import (TypedObjectManager, TypeclassManager)

_GA = object.__getattribute__
_AccountDB = None
_ObjectDB = None
_BoardDB = None
_SESSIONS = None


def sort_date(post):
    result_time = 0
    result_pinned = 0

    if hasattr(post, "last_post_on"):
        result_time = getattr(post, "last_post_on")

    if hasattr(post, "db_pinned"):
        if getattr(post, "db_pinned"):
            result_pinned = 1

    return result_pinned, result_time


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
                posts = self.filter(db_board=board).filter(Q(db_date_created__gte=oldest) | Q(db_pinned=True))\
                    .order_by('-db_pinned', 'db_date_created')
            else:
                posts = self.filter(db_board=board).order_by('-db_pinned', 'db_date_created')

            # This is a little unfortunate
            if board.db_expiry_maxposts and (board.db_expiry_maxposts > 0) and \
                    (board.db_expiry_maxposts <= posts.count()):
                pinned_count = self.filter(db_board=board, db_pinned=True).count()
                max_normal = board.db_expiry_maxposts - (pinned_count + 1)

                firstpost = posts[::-1][max_normal]

                posts = self.filter(Q(db_board=board) & (Q(db_pinned=True) | (Q(pk__gte=firstpost.id)))) \
                        .order_by('-db_pinned','db_date_created')


            return posts

        except self.model.DoesNotExist:
            return []

    def by_board_for_player(self, board, player):
        """
        Returns all the active posts on a board, with an 'unread' field based on the current user's
        read or unread status.

        Args:
            board (BoardDB): The board whose posts should be checked.
            player (AccountDB): The player whose read/unread status should be used.

        Returns:
            A list of Post objects.

        """
        posts = self.by_board(board)
        for p in posts:
            if player.read_posts.filter(pk=p.id).exists():
                setattr(p, "unread", False)
            else:
                setattr(p, "unread", True)

        return posts

    def by_board_threaded_player(self, board, player):
        """
        Return just all the threads.

        Args:
            board: The board to get threads for
            player: The player whose unread states should be used

        Returns:
            A list of Post objects

        """
        posts = self.filter(db_board=board).filter(db_parent__isnull=True)
        for p in posts:
            lr = p.last_reply
            setattr(p, "last_post_on", lr.db_date_created)
            setattr(p, "last_poster", lr.db_poster_name)
            replies = self.filter(db_parent=p)
            setattr(p, "total_posts", replies.count() + 1)
            if player:
                if player.read_posts.filter(pk=lr.id).exists():
                    setattr(p, "unread", False)
                else:
                    setattr(p, "unread", True)

        return sorted(posts, key=lambda p: (p.db_pinned, p.date_for_sort), reverse=True)


class PostManager(TypedObjectManager):

    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def post(self, id):
        return self.get_queryset().get(pk=id)

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

    def threads(self, board, player=None):
        """
        Given a board and an optional player, return the threads.

        Args:
            board:
            player:

        Returns:

        """
        return self.get_queryset().by_board_threaded_player(board, player)

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

    def get_all_boards(self):
        """
        Returns all boards.

        Returns:
            A list of DefaultBoard objects.
        """
        return self.all()

    def get_board_id(self, id):
        return self.get(pk=id)

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
                if p.is_unread:
                    unread = unread + 1

            setattr(b, "unread_count", unread)
            setattr(b, "total_count", len(all_posts))

            if all_posts:
                last_post = list(all_posts)[-1]
                setattr(b, "last_post", last_post)

        return filtered

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
                    if p.is_unread:
                        unread = unread + 1

                setattr(b, "unread_count", unread)
                setattr(b, "total_count", len(all_posts))

                return b

        return None

    def get_subscriptions(self, subscriber):
        """
        This function returns a list of boards a given user is subscribed to.

        Args:
            subscriber (Player): The player whose subscriptions should be checked.

        Returns:
            A list of boards subscribed to.

        """
        clsname = subscriber.__dbclass__.__name__
        if clsname == "AccountDB":
            return subscriber.board_subscriptions_set.all()

        return []


class BoardManager(BoardDBManager, TypeclassManager):
    """
    Wrapper class to group Typeclass manager and Board manager functionality together.
    """
    pass
