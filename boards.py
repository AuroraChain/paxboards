from evennia.typeclasses.models import TypeclassBase
from paxboards.models import Post, BoardDB
from paxboards.managers import BoardManager
from future.utils import with_metaclass
from server.conf import settings
from django.utils import timezone


class DefaultBoard(with_metaclass(TypeclassBase, BoardDB)):

    objects = BoardManager()

    def at_first_save(self):
        self.at_board_creation()

    def at_board_creation(self):
        pass

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
