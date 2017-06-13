# URL patterns for the character app

from django.conf.urls import url
from paxboards.views import show_boardlist, show_board, show_thread, submit_post, submit_reply

urlpatterns = [
    url(r'^$', show_boardlist, name="boardlist"),
    url(r'^(?P<board_id>\d+)/$', show_board, name="board"),
    url(r'^(?P<board_id>\d+)/(?P<post_id>\d+)/$', show_thread, name="thread"),
    url(r'^(?P<board_id>\d+)/post/$', submit_post, name="post"),
    url(r'^(?P<board_id>\d+)/(?P<post_id>\d+)/reply/$', submit_reply, name="reply"),
]
