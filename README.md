# Paxboards

A simple, extensible, bulletin board system for Evennia, with both on-game and web-based interfaces.

## Components

### DefaultBoard

DefaultBoard is a new Evennia base typeclass, which encapsulates all the board functionality.  It shows up at a database level and is manageable as with any other Evennia typeclass.

It also exposes a custom Django manager/queryset handler, allowing you to easily query which bboards are visible to a specific player from from the class.

It supports full lock handlers, with the following access keys:

* `read`: can read the board -- _this is necessary to see the board in your list_
* `post`: can post to the board
* `edit`: can edit posts by people other than yourself
* `delete`: can delete posts by people other than yourself

### DefaultPost

DefaultPost is a simple object class which encapsulates a given post.  Boards can be asked for their posts, and when you provide a calling player, it will annotate each DefaultPost with an 'unread' property as to whether or not that property has been read.

It supports some simple tools to check whether or not a player has access to perform a given operation.

## TODO

* The DefaultBoard/DefaultPost APIs could be cleaned up considerably; we shouldn't be dipping into the models' `db_*` fields for basic access.
* The web interface needs help like WHOA.