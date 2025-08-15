from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.urls import reverse
from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} (Автор)"

    def update_rating(self):
        author_post_rating = Post.objects.filter(author=self).aggregate(
            post_rating_sum=Sum('rating')
        )['post_rating_sum'] or 0
        author_post_rating *= 3

        author_comments_rating = Comment.objects.filter(user=self.user).aggregate(
            comments_rating_sum=Sum('rating')
        )['comments_rating_sum'] or 0

        post_ids = Post.objects.filter(author=self).values_list('id', flat=True)
        comments_to_author_post_rating = Comment.objects.filter(
            post__id__in=post_ids
        ).exclude(user=self.user).aggregate(
            comments_rating_sum=Sum('rating')
        )['comments_rating_sum'] or 0

        self.rating = author_post_rating + author_comments_rating + comments_to_author_post_rating
        self.save()

    @property
    def is_author(self):
        return hasattr(self, 'author')


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subscribers = models.ManyToManyField(User, related_name='subscribed_categories', blank=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    POST_TYPES = [
        (ARTICLE, 'Статья'),
        (NEWS, 'Новость'),
    ]

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    post_type = models.CharField(max_length=2, choices=POST_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(
        Category,
        through='PostCategory',
        related_name='posts'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.IntegerField(default=0)

    def get_absolute_url(self):
        """Генерирует правильный URL в зависимости от типа поста"""
        if self.post_type == self.NEWS:
            return reverse('NewsPortal:news_detail', args=[str(self.id)])
        else:
            return reverse('NewsPortal:article_detail', args=[str(self.id)])

    def save(self, *args, **kwargs):
        # Вызываем валидацию перед сохранением
        self.clean()
        super().save(*args, **kwargs)

    @property
    def preview(self):
        return self.content[:50] + '...' if len(self.content) > 50 else self.content

    def get_categories_display(self):
        return ", ".join([category.name for category in self.categories.all()])

    def get_post_type_display_name(self):
        return dict(self.POST_TYPES).get(self.post_type, 'Неизвестный тип')

    def __str__(self):
        return self.title

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()


class PostCategory(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
    )

    def save(self, *args, **kwargs):
        if not PostCategory.objects.filter(post=self.post, category=self.category).exists():
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.post.title} - {self.category.name}"

    class Meta:
        unique_together = ('post', 'category')


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

    def __str__(self):
        return f"Комментарий от {self.user.username} к {self.post.title}"

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()


class Subscriber(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='digest_subscriber'
    )
    categories = models.ManyToManyField(
        Category,
        related_name='digest_subscribers',
        blank=True
    )

    last_digest_sent = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Последняя рассылка'
    )
    unsubscribed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата отписки'
    )

    class Meta:
        verbose_name = 'Подписчик на рассылку'
        verbose_name_plural = 'Подписчики на рассылку'

    def __str__(self):
        return f"Подписчик: {self.user.username}"

    @property
    def unsubscribed(self):
        return self.unsubscribed_at is not None

    def get_new_posts(self):
        from .models import Post

        if not self.last_digest_sent:
            period_start = timezone.now() - timedelta(days=365)
        else:
            period_start = self.last_digest_sent

        subscribed_categories = self.user.subscribed_categories.all()

        return Post.objects.filter(
            categories__in=subscribed_categories,
            created_at__gt=period_start,
            created_at__lte=timezone.now()
        ).distinct().order_by('-created_at')
