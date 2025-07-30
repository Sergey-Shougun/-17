from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    def update_rating(self):
        # Рейтинг статей автора
        author_post_rating = Post.objects.filter(author=self).aggregate(
            post_rating_sum=Sum('rating')
        )['post_rating_sum'] or 0
        author_post_rating *= 3
        # Рейтинг комментариев автора
        author_comments_rating = Comment.objects.filter(user=self.user).aggregate(
            comments_rating_sum=Sum('rating')
        )['comments_rating_sum'] or 0
        # Рейтинг комментариев к статьям автора
        post_ids = Post.objects.filter(author=self).values_list('id', flat=True)
        comments_to_author_post_rating = Comment.objects.filter(
            post__id__in=post_ids
        ).exclude(user=self.user).aggregate(
            comments_rating_sum=Sum('rating')
        )['comments_rating_sum'] or 0
        self.rating = author_post_rating + author_comments_rating + comments_to_author_post_rating
        self.save()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    POST_TYPES = [
        (ARTICLE, 'Статья'),
        (NEWS, 'Новость')
    ]
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='posts'  # Явное указание related_name
    )
    post_type = models.CharField(max_length=2, choices=POST_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(Category, through='PostCategory')
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def preview(self):
        preview_text = str(self.content)
        if len(preview_text) > 124:
            return preview_text[:124] + '...'
        return preview_text

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()


class PostCategory(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='post_categories'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='category_posts'
    )


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)

    def dislike(self):
        self.rating += 1
        self.save()

    def like(self):
        self.rating += 1
        self.save()

# Create your models here.
