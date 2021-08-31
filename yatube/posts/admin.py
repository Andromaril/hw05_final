from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели в интерфейсе админки."""

    # Перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    list_editable = ('group',)
    # Добавляем интерфейс для поиска по тексту постов
    search_fields = ('text',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели в интерфейсе админки."""

    list_display = ('pk', 'title',)
    search_fields = ('title',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели в интерфейсе админки."""

    list_display = ('pk', 'post', 'author', 'text',)
    search_fields = ('text',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели в интерфейсе админки."""

    list_display = ('user', 'author',)
    search_fields = ('author',)


# При регистрации модели Post источником конфигурации для неё назначаем
# класс PostAdmin
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
