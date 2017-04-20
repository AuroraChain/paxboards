from django.shortcuts import render
from django.http import Http404
from boards import DefaultBoard
from models import Post
from evennia.utils import ansi

# Create your views here.

def boardlist(request):
    boards = DefaultBoard.objects.get_all_visible_boards(request.user)
    context = {'boards': boards}
    # make the variables in 'context' available to the web page template
    return render(request, 'boardlist.html', context)


def board(request, board_id):
    try:
        board = DefaultBoard.objects.get(pk=board_id)

        context = {'board': board}

        if not board.access(request.user, access_type="read", default=False):
            return render(request, 'board_noperm.html', context)

        posts = board.posts(request.user)
        context = {'board': board, 'posts': posts}

        return render(request, 'board.html', context)

    except DefaultBoard.DoesNotExist, DefaultBoard.MultipleObjectsReturned:
        return render(request, 'board_noperm.html', context)


def post(request, board_id, post_id):
    try:
        post = Post.objects.get(pk=post_id)

        board = post.db_board

        if not board.access(request.user, access_type="read", default=False):
            return render(request, 'board_noperm.html', context)

        plaintext = ansi.strip_ansi(post.db_text)
        context = {'board': board, 'post': post, 'text': plaintext}

        post.mark_read(request.user, True)

        return render(request, 'post.html', context)

    except Post.DoesNotExist, Post.MultipleObjectsReturned:
        raise Http404("Error accessing boards.")
