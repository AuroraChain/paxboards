from evennia.typeclasses.models import TypeclassBase
from paxboards.models import Post, BoardDB
from paxboards.managers import BoardManager
from future.utils import with_metaclass
from server.conf import settings
from django.utils import timezone


class DefaultBoard(with_metaclass(TypeclassBase, BoardDB)):

    objects = BoardManager()

    def __str__(self):
        return "<Board: " + self.name + ">"

    def at_init(self):
        pass

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
        return Post.objects.posts(self, player=player)

    def threads(self, player=None):
        """
        Convenience function, pulls all the threads for a given player's viewpoint.

        Args:
            player: The player whose read/unread status should be used.  If non, omits unread.

        Returns:
            A list of posts representing the threads.

        """
        return Post.objects.threads(self, player=player)

    def subscribers(self):
        """
        Obtain all the Players subscribed to this board.

        Returns:
            A list of AccountDB objects.

        """
        return self.db_subscriptions.all()

    def set_subscribed(self, player, subscribed):
        """
        Sets whether or not a given player is subscribed to the board.

        Args:
            player (AccountDB): A player to subscribe or unsubscribe.
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
            if p.is_unread:
                p.mark_read(caller, True)

        return

    def is_unread(self):
        if hasattr(self, 'unread_count'):
            return getattr(self, 'unread_count') > 0

        return False

    def create_post(self, subject, text, author_name=settings.SERVERNAME, author_player=None, author_object=None,
                    parent=None):
        """
        Creates a new post on the given board.

        Args:
            subject (string): The subject line for the post. Required.
            text (string): The actual text of the post.  Required.
            author_name (string): A display name for the author. Defaults to server name.
            author_player (AccountDB): The player making a post, if applicable, or None.
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

        postnum = p.post_num or None

        # Give up
        if not postnum:
            return p

        announcement = "|/New post by |555" + p.db_poster_name + ":|n (" + self.name + "/" + \
                       str(postnum) + ") |555" + p.db_subject + "|n|/"

        subs = self.subscribers()
        for s in subs:
            s.msg(announcement)

        return p
