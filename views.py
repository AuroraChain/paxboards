from django.shortcuts import render
from django.http import Http404
from boards import DefaultBoard
from models import Post
from evennia.utils import ansi

# Create your views here.


def boardlist(request):
    if not request.user:
        return render(request, 'board_noperm.html', context)

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

        threads = board.threads(request.user)
        context = {'board': board, 'threads': threads}

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
        setattr(post, 'plaintext', plaintext)
        post.mark_read(request.user, True)

        replies = Post.objects.filter(db_parent=post).order_by('db_date_created')
        for r in replies:
            plaintext = ansi.strip_ansi(r.db_text)
            setattr(r, 'plaintext', plaintext)
            r.mark_read(request.user, True)

        context = {'board': board, 'post': post, 'replies': replies}

        return render(request, 'post.html', context)

    except Post.DoesNotExist, Post.MultipleObjectsReturned:
        raise Http404("Error accessing boards.")
