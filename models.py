from __future__ import unicode_literals

from django.db import models
from evennia.typeclasses.models import TypedObject
from evennia.utils.idmapper.models import SharedMemoryModel
from evennia.utils.utils import crop, make_iter, lazy_property
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

    class Meta(object):
        "Define Django meta options"
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def mark_read(self, player, has_read):
        if has_read:
            self.db_readers.add(player)
        else:
            self.db_readers.remove(player)
        self.save()


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

