from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect
from paxboards.boards import DefaultBoard
from paxboards.models import Post
from evennia.utils import ansi
from paxboards.forms import PostForm, ReplyForm

# Create your views here.

def show_boardlist(request):
    if not request.user.is_authenticated or request.user.username == "":
        return render(request, 'login.html', {})

    boards = DefaultBoard.objects.get_all_visible_boards(request.user)
    context = {'boards': boards, 'page_title': 'Forums'}
    # make the variables in 'context' available to the web page template
    return render(request, 'boardlist.html', context)


def show_board(request, board_id):
    if not request.user.is_authenticated or request.user.username == "":
        return render(request, 'login.html', {})

    try:
        board = DefaultBoard.objects.get(pk=board_id)

        if not board.access(request.user, access_type="read", default=False):
            return render(request, 'board_noperm.html', {})

        can_post = board.access(request.user, access_type="post", default=False)

        threads = board.threads(request.user)

        context = {'board': board, 'threads': threads, 'can_post': can_post,
                   'board_id': board.id, 'page_title': 'Forums - ' + board.name}

        return render(request, 'board.html', context)

    except (DefaultBoard.DoesNotExist, DefaultBoard.MultipleObjectsReturned):
        return render(request, 'board_noperm.html', {})


def show_thread(request, board_id, post_id):
    if not request.user.is_authenticated or request.user.username == "":
        return render(request, 'login.html', {})

    try:
        post = Post.objects.get(pk=post_id)
        board = post.db_board

        if not board.access(request.user, access_type="read", default=False):
            return render(request, 'board_noperm.html', {})

        can_post = board.access(request.user, access_type="post", default=False)

        plaintext = ansi.strip_ansi(post.db_text)
        setattr(post, 'plaintext', plaintext)
        post.mark_read(request.user, True)

        replies = Post.objects.filter(db_parent=post).order_by('db_date_created')
        for r in replies:
            plaintext = ansi.strip_ansi(r.db_text)
            setattr(r, 'plaintext', plaintext)
            r.mark_read(request.user, True)

        form = ReplyForm()
        context = {'board': board, 'post': post, 'replies': replies, 'can_post': can_post,
                   'board_id': board, 'post_id': post, 'form': form,
                  'page_title': 'Forums - ' + post.db_subject}

        return render(request, 'thread.html', context)

    except (Post.DoesNotExist, Post.MultipleObjectsReturned):
        return Http404("Error accessing boards.")


def submit_post(request, board_id):
    if not request.user.is_authenticated or request.user.username == "":
        return render(request, 'login.html', {})

    try:
        board = DefaultBoard.objects.get(pk=board_id)

        if not board.access(request.user, access_type="post", default=False):
            return render(request, 'board_noperm.html', {})

        if request.method == "POST":
            # Actual submission
            form = PostForm(request.POST)
            if not form.is_valid():
                return Http404("Error submitting post.")

            text = form.cleaned_data['text']

            new_post = board.create_post(subject=form.cleaned_data['subject'], text=text,
                                         author_name=request.user.username, author_player=request.user)
            return HttpResponseRedirect("/boards/" + str(board.id) + "/" + str(new_post.id) + "/")
        else:
            form = PostForm()
            context = {'board': board, 'board_id': board.id, 'form': form}
            return render(request, 'submit_post.html', context)

    except (Board.DoesNotExist, Board.MultipleObjectsReturned):
        return Http404("Error accessing boards.")


def submit_reply(request, board_id, post_id):
    if not request.user.is_authenticated or request.user.username == "":
        return render(request, 'login.html', {})

    try:
        board = DefaultBoard.objects.get(pk=board_id)
        post = Post.objects.get(pk=post_id)

        if not board.access(request.user, access_type="post", default=False):
            return render(request, 'board_noperm.html', {})

        if request.method == "POST":
            form = ReplyForm(request.POST)
            if not form.is_valid():
                return Http404("Error submitting post.")

            text = form.cleaned_data['text']

            board.create_post(subject="Re: " + post.db_subject, text=text, author_name=request.user.username,
                              author_player=request.user, parent=post)
            return HttpResponseRedirect("/boards/" + str(board.id) + "/" + str(post.id) + "/")
        else:
            form = ReplyForm()
            context = {'board': board, 'board_id': board.id, 'post_id': post.id, 'form': form}
            return render(request, 'submit_reply.html', context)

    except (Board.DoesNotExist, Board.MultipleObjectsReturned, Post.DoesNotExist, Post.MultipleObjectsReturned):
        return Http404("Error accessing boards.")

