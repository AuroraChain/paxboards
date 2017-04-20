from evennia import default_cmds
from evennia.locks.lockhandler import LockException
from evennia import CmdSet
from evennia.utils import evtable
from typeclasses.characters import Character
from typeclasses.objects import Object

from board_utils import *
from boards import DefaultBoard, DefaultPost


class BoardAdminCmd(default_cmds.MuxCommand):
    """
    bbadmin/create <name>
    bbadmin/lock <board>[=lock]

    The first form of the command will create a new board.  The name must be unique,
    and cannot be solely an integer string.

    The second form of the command will set a lock for the given board.  The lock
    is a standard Evennia lock function string; the valid access types are:

       read:    ability to see/read the bboard
       post:    ability to post to the bboard
       edit:    ability to edit all posts on the bboard
       delete:  ability to delete all posts on the bboard
       pin:     ability to pin or unpin posts on the bboard

    Wizards and Immortals have all permissions by default.

    """
    key = "bbadmin"
    aliases = ["@bbadmin", "forumadmin", "@forumadmin"]
    locks = "cmd:perm(Wizards) OR perm(bbadmin)"
    help_category = "Forum"

    def func(self):
        caller = self.caller

        if "create" in self.switches:
            testboard = DefaultBoard.objects.get_board_exact(self.args)

            if not self.args:
                self.msg("You must provide a board name!")
                return

            if is_int(self.args):
                self.msg("A board name cannot be an integer.")
                return

            if testboard:
                self.msg("Board '" + self.args + "' already exists!")
                return

            board = DefaultBoard(db_key=self.args)
            board.save()
            self.msg("Created board '" + self.args + "'")
            return

        if "lock" in self.switches:
            if not self.args:
                self.msg("You must provide parameters!")
                return

            if not self.lhs:
                self.msg("You must provide a bboard name!")
                return

            board = DefaultBoard.objects.get_board(self.lhs)
            if not board:
                self.msg("No board matches '" + self.lhs + "'")
                return

            if not self.rhs:
                string = "Current locks on %s: %s" % (board.name, board.locks)
                self.msg(string)
                return

            try:
                board.locks.add(self.rhs)
            except LockException, err:
                self.msg(err)
                return

            self.msg("Lock(s) applied.")
            string = "Current locks on %s: %s" % (board.name, board.locks)
            self.msg(string)
            return

        self.msg("Unknown switch.  Please see {555help " + self.cmdstring + "{n for help.")


class BoardCmd(default_cmds.MuxCommand):
    """
    bboard [board[/post]]
    bboard/read [board[/post]]
    bboard/post <board>/<subject>=<post>
    bboard/sub <board>
    bboard/unsub <board>
    bboard/edit <board>/<post>=<newpost>
    bboard/delete <board>/<post>

    The first and second forms of this command will read the bboards.  If no
    parameters are provided, it list all available bboards.  If a single
    parameter - the board - is provided, it will list the posts on that board.
    If two are provided, it will read the specific post.

    The third form will make a post to a given bboard.

    The fourth and fifth will toggle your subscriptions on and off, controlling
    whether or not you see notifications of new posts on that board.

    The fifth will edit a post you have permissions to edit.

    The sixth will delete a post you have permission to delete.
    """
    key = "bboard"
    aliases = ["@bb", "@bboard", "forum", "@forum", "@bbread"]
    help_category = "Forum"

    def resolve_id(self, string):
        """
        Helper function which, given a string, will resolve it into a board or post.
        The string should be in the format "<board>[/postnum]", where board is either
        the name of a board or a number within those the player can see, while postnum
        should be an integer.

        Args:
            string: The string to resolve

        Returns:
            A dictionary containing 'board' (for a board), 'post' (if applicable), and the
            post number (just for convenience).

        """
        readargs = self.lhs.split('/', 1)
        boardname = readargs[0]

        if not 1 <= len(readargs) <= 2:
            self.msg("Unable to parse post identifier '" + string + "'!")

        if len(readargs) == 2:
            try:
                postnum = int(readargs[1])
            except ValueError:
                self.msg("The post identifier '" + readargs[1] + "' must be a positive integer!")
                return None

        board = DefaultBoard.objects.get_visible_board(self.player, boardname)
        if not board:
            self.msg("Unable to find a board matching '" + string + "'!")
            return None

        if len(readargs) == 1:
            return {"board": board, "post": None, "postnum": 0}

        posts = board.posts(self.player)

        if not (0 < postnum <= len(posts)):
            self.msg("There's no post by that number.")
            return

        post = posts[postnum - 1]
        return {"board": board, "post": post, "postnum": postnum}

    # This is overly long, and could potentially use a refactor to split the switches out
    # into their own functions.
    def func(self):
        caller = self.player

        boards = DefaultBoard.objects.get_all_visible_boards(caller)

        if len(self.switches) == 0 or "read" in self.switches or self.cmdstring == "@bbread":
            if not self.lhs:
                table = evtable.EvTable("#", "Name", "Unread", "Total", "Sub'd")
                counter = 0
                for board in boards:
                    counter += 1

                    posts = board.posts(caller)
                    unread_count = 0
                    for p in posts:
                        if p.unread:
                            unread_count += 1

                    subbed = " "
                    if board.subscribers().filter(pk=caller.pk).exists():
                        subbed = "Yes"

                    table.add_row(counter,board.name,unread_count,len(posts),subbed)

                self.msg(table)
            else:
                result = self.resolve_id(self.lhs)

                if not result:
                    return

                board = result["board"]
                post = result["post"]

                if not post:
                    posts = board.posts(player=caller)
                    if not posts:
                        self.msg("No posts on " + board.name)
                        return

                    table = evtable.EvTable("","Poster","Subject","Date")
                    counter = 0
                    for post in posts:
                        counter += 1

                        unreadstring = "  "
                        if post.unread:
                            unreadstring = "|555*|n "

                        datestring = str(post.db_date_created.year) + "/"
                        datestring += str(post.db_date_created.month).rjust(2,'0') + "/"
                        datestring += str(post.db_date_created.day).rjust(2,'0')

                        table.add_row(unreadstring + self.lhs + "/" + str(counter), post.db_poster_name, post.db_subject, datestring)

                    self.msg(table)
                else:
                    postid = post.db_board.name + " / " + str(result["postnum"])

                    datestring = str(post.db_date_created.year) + "/"
                    datestring += str(post.db_date_created.month).rjust(2,'0') + "/"
                    datestring += str(post.db_date_created.day).rjust(2,'0')

                    header = ("===[ " + postid + " ]").ljust(75, "=")

                    self.msg(" ")
                    self.msg(header)
                    self.msg("|555Date   :|n " + datestring)
                    self.msg("|555Poster :|n " + post.db_poster_name)
                    self.msg("|555Subject:|n " + post.db_subject)
                    self.msg("---------------------------------------------------------------------------")
                    self.msg(post.db_text)
                    self.msg("===========================================================================")
                    self.msg(" ")

                    post.db_readers.add(caller)
                    post.save()

                    return

        if "post" in self.switches:
            if not self.lhs:
                self.msg("You must provide a bboard to post to.")
                return

            readargs = self.lhs.split('/', 1)
            boardname = readargs[0]

            if len(readargs) == 1:
                self.msg("You must provide a subject!")
                return

            if not self.rhs:
                self.msg("It wouldn't do much good to make an empty post, would it?")
                return

            board = DefaultBoard.objects.get_visible_board(caller, boardname)
            if not board:
                self.msg("Unable to find a unique board matching '" + self.lhs + "'")
                return

            # Take the read permissions as a default, in case 'post' permissions aren't
            # set.  If a board has NO permissions set, it'll be accessible to everyone.
            can_read = board.access(caller, access_type='read', default=True)

            if not board.access(caller, access_type='post', default=can_read):
                self.msg("You don't have permission to post to " + board.name + "!")
                return

            postplayer = self.player
            postobject = None
            postname = self.player.name

            if self.caller is Object or self.caller is Character:
                postobject = self.caller
                postname = postobject.name

            post = board.create_post(author_name=postname, author_player=postplayer, author_object=postobject,
                                     subject=readargs[1], text=self.rhs)

            if post:
                posts = board.posts()
                postnum = posts.index(post)

                # Give up
                if postnum == 0:
                    return

                announcement = "|/New post by |555" + post.db_poster_name + ":|n (" + board.name + "/" + \
                               str(postnum + 1) + ") |555" + post.db_subject + "|n|/"

                self.msg("Posted.")

                subs = board.subscribers()
                for s in subs:
                    s.msg(announcement)

            return

        if "sub" in self.switches or "unsub" in self.switches:

            sub = True
            if "unsub" in self.switches:
                sub = False

            if not self.lhs:
                self.msg("You must provide a bboard to " + ("subscribe" if sub else "unsubscribe") + "to.")
                return

            board = DefaultBoard.objects.get_visible_board(caller, self.lhs)
            if not board:
                self.msg("Unable to find a unique board matching '" + self.lhs + "'")
                return

            board.set_subscribed(caller, sub)
            self.msg("Subscribed to " + board.name if sub else "Unsubscribed from " + board.name)
            return

        if "edit" in self.switches:
            result = self.resolve_id(self.lhs)

            # No valid results
            if not result:
                return

            board = result["board"]
            post = result["post"]

            # No post
            if not post:
                self.msg("You must provide a post to edit.")
                return

            if not post.has_access(caller,"edit"):
                self.msg("You can't edit that post!")
                return

            post.db_text = self.rhs
            post.save()
            self.msg("Post updated.")
            return

        if "delete" in self.switches:
            result = self.resolve_id(self.lhs)

            # No valid results
            if not result:
                return

            board = result["board"]
            post = result["post"]

            # No post
            if not post:
                self.msg("You must provide a post to delete.")
                return

            if not post.has_access(caller, "delete"):
                self.msg("You can't delete that post!")
                return

            # TODO: Should we delete this or just unlink it?
            post.delete()
            self.msg("Post deleted.")
            return


class BoardCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(BoardAdminCmd())
        self.add(BoardCmd())