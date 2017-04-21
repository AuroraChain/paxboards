from evennia.typeclasses.models import TypeclassBase
from paxboards.models import Post, BoardDB
from paxboards.managers import BoardManager, PostManager
from future.utils import with_metaclass
from server.conf import settings
from django.utils import timezone


class DefaultPost(with_metaclass(TypeclassBase, Post)):

    objects = PostManager()

    def __str__(self):
        return "<Post " + str(self.id) + " by " + self.db_poster_name + ": " + self.db_subject + \
        ("(unread)>" if self.unread else "(none)>" if not hasattr(self,"db_unread") else ">")

    def __unicode__(self):
        return unicode(str(self))

    def __repr__(self):
        return str(self)

    def has_access(self, player, access_key):
        """
        Checks if the given player has the given access key or is the originator.

        Args:
            player: The player to check against
            access_key: The access key

        Returns:
            True or False

        """
        if not player:
            return False

        clsname = player.__dbclass__.__name__
        if clsname == "PlayerDB":
            if self.db_poster_player == player:
                return True
        elif clsname == "ObjectDB":
            if self.db_poster_object == player:
                return True

        return self.db_board.access(player, access_type=access_key, default=False)

    def mark_read(self, player, has_read):
        """
        Mark this post read for the given player.

        Args:
            player: The player whose read/unread status we're changing
            has_read: Should this be marked as read

        Returns:

        """
        if not player:
            return

        if has_read:
            self.db_readers.add(player)
        else:
            self.db_readers.remove(player)
        self.save()

    def display_post(self, player):
        post_num = self.db_board.posts().index(self)

        postid = self.db_board.name + " / " + str(post_num)

        datestring = str(self.db_date_created.year) + "/"
        datestring += str(self.db_date_created.month).rjust(2, '0') + "/"
        datestring += str(self.db_date_created.day).rjust(2, '0')

        header = ("===[ " + postid + " ]").ljust(75, "=")

        player.msg(" ")
        player.msg(header)
        player.msg("|555Date   :|n " + datestring)
        player.msg("|555Poster :|n " + self.db_poster_name)
        player.msg("|555Subject:|n " + self.db_subject)
        player.msg("---------------------------------------------------------------------------")
        player.msg(self.db_text)
        player.msg("===========================================================================")
        player.msg(" ")


class DefaultBoard(with_metaclass(TypeclassBase, BoardDB)):

    objects = BoardManager()

    def __str__(self):
        return "<Board: " + self.name + ">"

    def at_first_save(self):
        self.at_board_creation()

    def at_board_creation(self):
        pass

    def posts(self, player=None):
        """
        Convenience function, pulls all the posts for a given player's viewpoint.

        Args:
            player: The player whose read/unread status should be used.  If None, omits unread.

        Returns:
            A list of posts!

        """
        return DefaultPost.objects.posts(self, player=player)

    def subscribers(self):
        """
        Obtain all the Players subscribed to this board.

        Returns:
            A list of PlayerDB objects.

        """
        return self.db_subscriptions.all()

    def set_subscribed(self, player, subscribed):
        """
        Sets whether or not a given player is subscribed to the board.

        Args:
            player (PlayerDB): A player to subscribe or unsubscribe.
            subscribed (boolean): Whether or not to be subscribed.

        Returns:
            None

        """
        if subscribed:
            self.db_subscriptions.add(player)
        else:
            self.db_subscriptions.remove(player)
        self.save()

    def mark_all_read(self, caller):
        """
        Mark all the posts on a given board read.

        Args:
            caller: The player for whom these posts should be marked read.

        Returns:
            None

        """
        if not self.access(caller, access_type="read", default=True):
            return

        posts = self.posts(caller)
        for p in posts:
            if p.unread:
                p.mark_read(caller, True)

        return

    def create_post(self, subject, text, author_name=settings.SERVERNAME, author_player=None, author_object=None,
                    parent=None):
        """
        Creates a new post on the given board.

        Args:
            subject (string): The subject line for the post. Required.
            text (string): The actual text of the post.  Required.
            author_name (string): A display name for the author. Defaults to server name.
            author_player (PlayerDB): The player making a post, if applicable, or None.
            author_object (ObjectDB): An object making a post, if applicable, or None.
            parent (Post): A parent post, if this is in reply to another post, or None.

        Returns:
            The new post, or None.

        """
        if not subject or len(subject) == 0:
            return False

        if not author_name or len(author_name) == 0:
            return False

        if not text or len(text) == 0:
            return False

        p = Post(db_poster_player=author_player,
                 db_poster_object=author_object,
                 db_date_created=timezone.now(),
                 db_subject=subject,
                 db_board=self,
                 db_text=text,
                 db_poster_name=author_name,
                 db_pinned=False,
                 db_parent=parent)
        p.save()

        # If we are a player, mark our own post read.
        if author_player:
            p.db_readers.add(author_player)

        p.save()

        return p
