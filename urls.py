# URL patterns for the character app

from django.conf.urls import url
from paxboards.views import boardlist
from paxboards.views import board
from paxboards.views import post

urlpatterns = [
    url(r'^$', boardlist, name="boardlist"),
    url(r'^all/$', boardlist, name="boardlist"),
    url(r'^(?P<board_id>\d+)/$', board, name="board"),
    url(r'^(?P<board_id>\d+)/(?P<post_id>\d+)/$', post, name="post"),
]
