"""
This defines how Board models are displayed in the web admin interface.

"""

from django.contrib import admin
from paxboards.boards import DefaultBoard


class BoardAdmin(admin.ModelAdmin):
    """
    Defines display for Board objects

    """
    list_display = ('id', 'db_key', 'db_lock_storage')
    list_display_links = ("id", 'db_key')
    ordering = ["id"]
    search_fields = ['id', 'db_key']
    save_as = True
    save_on_top = True
    list_select_related = True
    fieldsets = (
        (None, {'fields': (('db_key', ), 'db_lock_storage', 'db_expiry_maxposts', 'db_expiry_duration')}),
        )

    def save_model(self, request, obj, form, change):
        """
        Model-save hook.

        Args:
            request (Request): Incoming request.
            obj (Object): Database object.
            form (Form): Form instance.
            change (bool): If this is a change or a new object.

        """
        obj.save()
        if not change:
            # adding a new object
            # have to call init with typeclass passed to it
            obj.set_class_from_typeclass(typeclass_path='paxboards.boards.DefaultBoard')
        obj.at_init()
    pass


admin.site.register(DefaultBoard, BoardAdmin)
