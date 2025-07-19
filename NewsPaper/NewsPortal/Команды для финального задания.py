# 1. Импорт моделей и функций
from django.contrib.auth.models import User
from NewsPortal.models import Author, Category, Post, PostCategory, Comment

# 2. Создание пользователей
user1 = User.objects.create_user('user1')
user2 = User.objects.create_user('user2')

# 3. Создание авторов
author1 = Author.objects.create(user=user1)
author2 = Author.objects.create(user=user2)

# 4. Добавление категорий
cat1 = Category.objects.create(name='Политика')
cat2 = Category.objects.create(name='Спорт')
cat3 = Category.objects.create(name='Технологии')
cat4 = Category.objects.create(name='Культура')

# 5. Создание статей и новости
post1 = Post.objects.create(
    author=author1,
    post_type=Post.ARTICLE,
    title='Статья о политике',
    content='Подробный анализ последних политических событий...' * 50  # Длинный текст
)

post2 = Post.objects.create(
    author=author2,
    post_type=Post.ARTICLE,
    title='Спортивные достижения',
    content='Обзор последних спортивных рекордов...' * 50
)

post3 = Post.objects.create(
    author=author1,
    post_type=Post.NEWS,
    title='Новость о технологиях',
    content='Прорыв в области искусственного интеллекта...' * 50
)

# 6. Присвоение категорий
# Для post1: 2 категории
PostCategory.objects.create(post=post1, category=cat1)
PostCategory.objects.create(post=post1, category=cat4)

# Для post2: 1 категория
PostCategory.objects.create(post=post2, category=cat2)

# Для post3: 2 категории
PostCategory.objects.create(post=post3, category=cat3)
PostCategory.objects.create(post=post3, category=cat4)

# 7. Создание комментариев
comment1 = Comment.objects.create(post=post1, user=user1, text='Отличная статья!')
comment2 = Comment.objects.create(post=post1, user=user2, text='Не согласен с автором')
comment3 = Comment.objects.create(post=post2, user=user1, text='Интересный материал')
comment4 = Comment.objects.create(post=post3, user=user2, text='Ждем продолжения')

# 8. Корректировка рейтингов
# Лайки/дислайки для постов
post1.like()  # +1
post1.like()  # +1
post1.dislike()  # -1 → итого: +1

post2.like()  # +1
post2.like()  # +1
post2.like()  # +1 → итого: +3

post3.dislike()  # -1
post3.dislike()  # -1 → итого: -2

# Лайки/дислайки для комментариев
comment1.like()  # +1
comment1.like()  # +1 → итого: +2

comment2.dislike()  # -1

comment3.like()  # +1
comment3.like()  # +1
comment3.like()  # +1 → итого: +3

comment4.dislike()  # -1

# 9. Обновление рейтингов авторов
author1.update_rating()
author2.update_rating()

# 10. Лучший пользователь
best_author = Author.objects.order_by('-rating').first()
print(f"Лучший автор: {best_author.user.username}, Рейтинг: {best_author.rating}")

# 11. Лучшая статья
best_post = Post.objects.filter(post_type=Post.ARTICLE).order_by('-rating').first()
print(f"Дата: {best_post.created_at}")
print(f"Автор: {best_post.author.user.username}")
print(f"Рейтинг: {best_post.rating}")
print(f"Заголовок: {best_post.title}")
print(f"Превью: {best_post.preview()}")

# 12. Комментарии к лучшей статье
comments = Comment.objects.filter(post=best_post).order_by('created_at')
print("\nКомментарии к статье:")
for comment in comments:
    print(f"Дата: {comment.created_at}")
    print(f"Пользователь: {comment.user.username}")
    print(f"Рейтинг: {comment.rating}")
    print(f"Текст: {comment.text}\n")




