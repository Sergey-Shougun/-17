from django.contrib import admin
from .models import Author, Category, Post, Comment, PostCategory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subscribers_count')
    search_fields = ('name',)

    def subscribers_count(self, obj):
        return obj.subscribers.count()

    subscribers_count.short_description = 'Подписчиков'


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'created_at')
    search_fields = ('user__username',)


class PostCategoryInline(admin.TabularInline):
    model = PostCategory
    extra = 1


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'post_type', 'created_at', 'rating')
    list_filter = ('post_type', 'created_at', 'author')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    inlines = [PostCategoryInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'author', 'post_type')
        }),
        ('Дополнительно', {
            'fields': ('rating',),
            'classes': ('collapse',)
        }),
    )


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at', 'rating')
    list_filter = ('created_at', 'rating')
    search_fields = ('text',)


admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(PostCategory)
