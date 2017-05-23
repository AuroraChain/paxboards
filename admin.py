"""
This defines how Board models are displayed in the web admin interface.

"""

from django.contrib import admin
from models import BoardDB, Post

class BoardAdmin(admin.ModelAdmin):
    """
    Defines display for Board objects

    """
    list_display = ('id', 'db_key', 'db_lock_storage')
    list_display_links = ("id", 'db_key')

    pass

admin.site.register(BoardDB, BoardAdmin)
