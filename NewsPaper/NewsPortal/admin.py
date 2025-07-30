from django.contrib import admin
from .models import Author, Category, Post, Comment, PostCategory


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


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating')
    search_fields = ('user__username',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at', 'rating')
    list_filter = ('created_at', 'rating')
    search_fields = ('text',)


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(PostCategory)