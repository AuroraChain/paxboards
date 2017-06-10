# URL patterns for the character app

from django.conf.urls import url
from paxboards.views import show_boardlist, show_board, show_thread, submit_post, submit_reply

urlpatterns = [
    url(r'^$', show_boardlist, name="boardlist"),
    url(r'^all/$', show_boardlist, name="boardlist"),
    url(r'^(?P<board_id>\d+)/$', show_board, name="board"),
    url(r'^(?P<board_id>\d+)/(?P<post_id>\d+)/$', show_thread, name="thread"),
    url(r'^post/(?P<board_id>\d+)/$', submit_post, name="post"),
    url(r'^reply/(?P<board_id>\d+)/(?P<post_id>\d+)/$', submit_reply, name="reply"),
]
