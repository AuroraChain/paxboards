# Paxboards

A simple, extensible, threaded bulletin board system for Evennia, with both on-game and web-based interfaces.

## Installation

Simply grab this repository as a subdirectory of your Evennia game directory, and then add the following two lines to your `server/conf/settings.py` file:

```
INSTALLED_APPS += ('paxboards',)
TYPECLASS_PATHS += ['paxboards']
```

Then go to `web/urls.py` and add:

```
custom_patterns = [
    url(r'^boards/', include('paxboards.urls', namespace='board', app_name='paxboards')),
]
```

If you already have custom patterns, just add the url record to your existing list.

When all of this is done, run `evennia migrate` and execute `@reload` on your game, and you should be good to go.

## Components

### DefaultBoard

DefaultBoard is a new Evennia base typeclass, which encapsulates all the board functionality.  It shows up at a database level and is manageable as with any other Evennia typeclass.

It also exposes a custom Django manager/queryset handler, allowing you to easily query which bboards are visible to a specific player from from the class.

It supports full lock handlers, with the following access keys:

* `read`: can read the board -- _this is necessary to see the board in your list_
* `post`: can post to the board
* `edit`: can edit posts by people other than yourself
* `delete`: can delete posts by people other than yourself

### Post

Post is a simple object class which encapsulates a given post.  Boards can be asked for their posts, and when you provide a calling player, it will annotate each DefaultPost with an 'unread' property as to whether or not that property has been read.

It supports some simple tools to check whether or not a player has access to perform a given operation.

## TODO

* The DefaultBoard/Post APIs could be cleaned up considerably; we shouldn't be dipping into the models' `db_*` fields for basic access.
* The web interface needs help like *seriously*.  In particular, it needs to support threaded posts, as well as posting/replying.
* The web interface also seriously needs better templates.  It's kind of ugly right now.
* The helpfile for bboard could be a lot better.