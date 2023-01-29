from __future__ import unicode_literals

from django.db import models
from evennia.typeclasses.models import TypedObject
from evennia.utils.idmapper.models import SharedMemoryModel
from paxboards.managers import PostManager

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
    db_poster_player = models.ForeignKey("accounts.AccountDB", related_name="+", null=True, blank=True, on_delete=models.SET_NULL,
                                         verbose_name="poster(player)", db_index=True,
                                         help_text='Post origin (if player).')
    db_poster_object = models.ForeignKey("objects.ObjectDB", related_name="+", null=True, blank=True, on_delete=models.SET_NULL,
                                         verbose_name="poster(object)", db_index=True,
                                         help_text='Post origin (if object),')
    db_poster_name = models.CharField(max_length=40, verbose_name="poster", null=False, blank=False, 
                                      help_text='Poster display name.')
    db_subject = models.CharField(max_length=40, verbose_name="subject", help_text='Subject of post.')
    db_board = models.ForeignKey("BoardDB", verbose_name='board', on_delete=models.CASCADE, help_text='Board this post is on.', db_index=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                           auto_now_add=True, db_index=True, help_text='Date post was made.')
    db_pinned = models.BooleanField(verbose_name="pinned",
                                    help_text='Should the post remain visible even after expiration?')
    db_readers = models.ManyToManyField("accounts.AccountDB", related_name="read_posts", null=True, blank=True,
                                        verbose_name="readers", help_text='Players who have read this post.')
    db_parent = models.ForeignKey('Post', verbose_name='parent', related_name='replies', null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text='Parent/child map for threaded replies.')
    db_text = models.TextField(verbose_name="post_text", null=True, blank=True, help_text='Text of the post.')

    objects = PostManager()

    class Meta(object):
        "Define Django meta options"
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return "<Post " + str(self.id) + " by " + self.db_poster_name + ": " + self.db_subject + \
        ("(unread)>" if self.is_unread else "(none)>" if not hasattr(self,"unread") else ">")

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
        if clsname == "AccountDB":
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
        """
        Simple property to return the post number this post occupies on
        its parent board.

        Returns:
            An integer.

        """
        posts = Post.objects.posts(self.db_board)
        return list(posts).index(self) + 1 if self in posts else None

    @property
    def last_reply(self):
        """

        Returns:
            The last/most recent reply Post in the reply chain, or self if
            there are none.

        """
        posts = Post.objects.filter(db_parent=self).order_by('db_date_created')
        if posts:
            return posts.last()

        return self

    @property
    def is_unread(self):
        if hasattr(self, 'unread'):
            return getattr(self, 'unread')

        return False

    @property
    def subject(self):
        result = self.db_subject
        if hasattr(self,'db_pinned') and getattr(self, 'db_pinned'):
            result = "[Pinned] " + result

        return result

    @property
    def date_for_sort(self):
        if hasattr(self,'last_post_on'):
            return getattr(self, 'last_post_on')

        return self.db_date_created

    @property
    def posted_by(self):
        return self.db_poster_name

    @property
    def poster(self):
        return self.db_poster_name

    def display_post(self, player, show_replies=False):
        post_num = self.post_num

        if post_num:
            postid = self.db_board.name + " / " + str(post_num)
        else:
            postid = self.db_board.name

        datestring = (str(self.db_date_created.year)) + u'/'
        datestring += (str(self.db_date_created.month)).rjust(2, '0') + u'/'
        datestring += (str(self.db_date_created.day)).rjust(2, '0')

        header = ("===[ " + postid + " ]").ljust(75, "=")

        post_string = header + "\n"
        post_string += "|555Date   :|n " + datestring + "\n"
        post_string += "|555Poster :|n " + self.db_poster_name + "\n"
        post_string += "|555Subject:|n " + self.db_subject
        if self.db_pinned:
            post_string += " |555(Pinned)|n"
        post_string += "\n---------------------------------------------------------------------------\n"
        post_string += self.db_text + "\n"

        if show_replies:
            replies = Post.objects.filter(db_parent=self).order_by('db_date_created')
            for r in replies:
                datestring = (str(r.db_date_created.year)) + u'/'
                datestring += (str(r.db_date_created.month)).rjust(2, '0') + u'/'
                datestring += (str(r.db_date_created.day)).rjust(2, '0')
                post_string += "\n---------------------------------------------------------------------------\n"
                post_string += "|555Date   :|n " + datestring + "\n"
                post_string += "|555Poster :|n " + r.db_poster_name + "\n"
                post_string += "--------\n"
                post_string += r.db_text + "\n"

        post_string += "==========================================================================="

        player.msg(" ")
        player.msg(post_string)
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
    db_subscriptions = models.ManyToManyField('accounts.AccountDB', blank=True, verbose_name='subscribers',
                                              related_name='board_subscriptions',
                                              help_text='Players subscribed to this board.')

    __settingclasspath__ = "paxboards.boards.DefaultBoard"
    __defaultclasspath__ = "paxboards.boards.DefaultBoard"
    __applabel__ = "paxboards"

    class Meta(object):
        "Define Django meta options"
        verbose_name = "Board"
        verbose_name_plural = "Boards"

    def __str__(self):
        "Echoes the text representation of the board."
        return "Board '%s' (%s)" % (self.key, self.db.desc)

