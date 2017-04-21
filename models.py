from __future__ import unicode_literals

from django.db import models
from evennia.typeclasses.models import TypedObject
from evennia.utils.idmapper.models import SharedMemoryModel
from managers import PostManager

__all__ = ("Post", "BoardDB")


class Post(SharedMemoryModel):
    """
    A single post.

    A post defines the following database fields, all accessed by convenience accessors.

    - db_poster_player: The player object (if there is one) who made the post.
    - db_poster_object: The object (if there is one) that made the post.
    - db_poster_name: The name to use for the byline of the post, as a string.
    - db_subject: The subject to use for the post, as a string.
    - db_board: The board on which this post was made.
    - db_date_created: The timestamp when this post was made.
    - db_pinned: A boolean, determining if the post should be prevented from timing out.
    - db_readers: A list of players who have read this post.
    - db_parent: For threaded post chains, the parent to this post.
    - db_text: The actual text of the post.

    """
    db_poster_player = models.ForeignKey("players.PlayerDB", related_name="+", null=True, blank=True,
                                         verbose_name="poster(player)", db_index=True, help_text='Post origin (if player).')
    db_poster_object = models.ForeignKey("objects.ObjectDB", related_name="+", null=True, blank=True,
                                         verbose_name="poster(object)", db_index=True, help_text='Post origin (if object),')
    db_poster_name = models.CharField(max_length=40, verbose_name="poster", null=False, blank=False,
                                      help_text='Poster display name.')
    db_subject = models.CharField(max_length=40, verbose_name="subject", help_text='Subject of post.')
    db_board = models.ForeignKey("BoardDB", verbose_name='board', help_text='Board this post is on.', db_index=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True, help_text='Date post was made.')
    db_pinned = models.BooleanField(verbose_name="pinned", help_text='Should the post remain visible even after expiration?')
    db_readers = models.ManyToManyField("players.PlayerDB", related_name="read_posts", null=True, blank=True,
                                        verbose_name="readers", help_text='Players who have read this post.')
    db_parent = models.ForeignKey('Post', verbose_name='parent', related_name='replies', null=True, blank=True,
                                  help_text='Parent/child map for threaded replies.')
    db_text = models.TextField(verbose_name="post_text", null=True, blank=True, help_text='Text of the post.')

    objects = PostManager()

    @property
    def unread(self):
        if not hasattr(self, "db_unread"):
            return False

        return self.db_unread

    class Meta(object):
        "Define Django meta options"
        verbose_name = "Post"
        verbose_name_plural = "Posts"

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

    @property
    def post_num(self):
        posts = Post.objects.posts(self.db_board)
        return posts.index(self) + 1 if self in posts else None

    def display_post(self, player):
        post_num = self.post_num

        if post_num:
            postid = self.db_board.name + " / " + str(post_num)
        else:
            postid = self.db_board.name

        datestring = unicode(str(self.db_date_created.year)) + u'/'
        datestring += unicode(str(self.db_date_created.month)).rjust(2, '0') + u'/'
        datestring += unicode(str(self.db_date_created.day)).rjust(2, '0')

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


class BoardDB(TypedObject):
    """
    This is a basic Paxboards board, descending from the base Evennia TypedObject (and thus
    inheriting keys, locks, tags, and so on.

    In addition, it has the following fields, accessed through the managers:

    - db_expiry_maxposts: An optional number, of how many posts should be shown.
    - db_expiry_duration: An optional duration, in days, of how long a post should remain.
    - db_subscriptions: The players who are subscribed to the board.

    """
    db_expiry_maxposts = models.IntegerField('max_posts', blank=True, null=True,
                                             help_text='Maximum number of active/visible posts for this board.')
    db_expiry_duration = models.IntegerField('lifetime_days', blank=True, null=True,
                                             help_text='Maximum timeline in days for posts to live on this board.')
    db_subscriptions = models.ManyToManyField('players.PlayerDB', blank=True, verbose_name='subscribers',
                                              related_name='board_subscriptions',
                                              help_text='Players subscribed to this board.')

    __settingclasspath__ = "typeclasses.boards.Board"
    __defaultclasspath__ = "paxboards.boards.DefaultBoard"
    __applabel__ = "paxboards"

    class Meta(object):
        "Define Django meta options"
        verbose_name = "Board"
        verbose_name_plural = "Boards"

    def __str__(self):
        "Echoes the text representation of the board."
        return "Board '%s' (%s)" % (self.key, self.db.desc)

