from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from .filters import PostFilter
from .forms import NewsCreateForm
from .models import Post, Author, Category, PostCategory, Subscriber
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from datetime import timedelta
from .signals import send_author_request_email


@login_required
def my_subscriptions(request):
    try:
        subscriber = Subscriber.objects.get(user=request.user)
        categories = subscriber.categories.all()
    except Subscriber.DoesNotExist:
        categories = []

    return render(request, 'my_subscriptions.html', {
        'categories': categories
    })


def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})


def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    posts = Post.objects.filter(categories=category).order_by('-created_at')

    # Проверяем, подписан ли пользователь на эту категорию
    is_subscribed = False
    if request.user.is_authenticated:
        try:
            subscriber = Subscriber.objects.get(user=request.user)
            is_subscribed = category in subscriber.categories.all()
        except Subscriber.DoesNotExist:
            pass

    return render(request, 'category_detail.html', {
        'category': category,
        'posts': posts,
        'is_subscribed': is_subscribed
    })


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = 'account/profile_edit.html'
    success_url = reverse_lazy('NewsPortal:profile')

    def get_object(self, queryset=None):
        return self.request.user


def permission_denied_view(request, exception):
    return render(request, '403.html', status=403)


@login_required
def subscribe_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    subscriber, created = Subscriber.objects.get_or_create(user=request.user)

    if category not in subscriber.categories.all():
        subscriber.categories.add(category)
        messages.success(request, f'Вы подписались на рассылку категории "{category.name}"')
    else:
        messages.info(request, f'Вы уже подписаны на категорию "{category.name}"')

    return redirect(request.META.get('HTTP_REFERER', reverse('NewsPortal:category_list')))


@login_required
def unsubscribe_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    try:
        subscriber = Subscriber.objects.get(user=request.user)
        if category in subscriber.categories.all():
            subscriber.categories.remove(category)
            messages.success(request, f'Вы отписались от рассылки категории "{category.name}"')
        else:
            messages.info(request, 'Вы не были подписаны на эту категорию')
    except Subscriber.DoesNotExist:
        messages.info(request, 'У вас нет активных подписок')

    return redirect(request.META.get('HTTP_REFERER', reverse('NewsPortal:category_list')))


def news_detail(request, pk):
    news = get_object_or_404(Post, pk=pk, post_type='NW')
    return render(request, 'news/news_detail.html', {'news': news})


def article_list(request):
    articles = Post.objects.filter(post_type='AR').order_by('-created_at')
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/article_list.html', {
        'page_obj': page_obj,
        'total_articles': articles.count()
    })


def article_detail(request, pk):
    article = get_object_or_404(Post, pk=pk)
    return render(request, 'news/article_detail.html', {'article': article})


def news_list(request):
    news = Post.objects.filter(post_type='NW').order_by('-created_at')
    categories = Category.objects.all()
    paginator = Paginator(news, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/news_list.html', {
        'page_obj': page_obj,
        'total_news': news.count(),
        'categories': categories
    })


class PostSearch(ListView):
    model = Post
    template_name = 'news/search.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(post_type='NW')
        self.filterset = PostFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context


class AuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

    def handle_no_permission(self):
        return redirect('NewsPortal:become_author')


class NewsCreate(AuthorRequiredMixin, LoginRequiredMixin, CreateView):
    form_class = NewsCreateForm
    model = Post
    template_name = 'news/post_edit.html'
    login_url = '/accounts/login/'
    permission_required = 'NewsPortal.add_post'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('account_login')
        else:
            messages.error(self.request, "У вас нет прав для создания новостей. Станьте автором!")
            return redirect('NewsPortal:become_author')

    def form_valid(self, form):

        try:
            author = self.request.user.author
        except Author.DoesNotExist:
            author = Author.objects.create(user=self.request.user)

        time_threshold = timezone.now() - timedelta(days=1)
        news_count = Post.objects.filter(
            author=author,
            post_type=Post.NEWS,
            created_at__gte=time_threshold
        ).count()

        if news_count >= 3:
            form.add_error(None, ValidationError('Вы не можете публиковать более 3 новостей в сутки.'))
            return self.form_invalid(form)

        post = form.save(commit=False)
        post.author = author
        post.post_type = Post.NEWS
        print(f"Создаем новость: {post.title}")
        print(f"Автор: {author.user.username}")
        print(f"Категории: {[c.name for c in form.cleaned_data['categories']]}")

        post.save()

        print(f"Новость создана! ID: {post.id}")

        for category in form.cleaned_data['categories']:
            print(f"Связываем с категорией: {category.name}")
            PostCategory.objects.create(post=post, category=category)

        self.object = post

        messages.success(self.request, "Новость успешно опубликована!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('NewsPortal:news_detail', kwargs={'pk': self.object.pk})


class NewsUpdate(LoginRequiredMixin, UpdateView):
    form_class = NewsCreateForm
    model = Post
    template_name = 'news/post_edit.html'
    login_url = '/accounts/login/'
    permission_required = 'NewsPortal.change_post'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('account_login')
        else:
            messages.error(self.request, "У вас нет прав для редактирования новостей. Станьте автором!")
            return redirect('NewsPortal:become_author')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author.user != request.user:
            raise PermissionDenied("Вы не являетесь автором этой новости")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(post_type='NW')

    def get_success_url(self):
        return reverse_lazy('NewsPortal:news_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):

        post = form.save(commit=False)
        post.save()

        PostCategory.objects.filter(post=post).delete()

        for category in form.cleaned_data['categories']:
            PostCategory.objects.create(post=post, category=category)

        return super().form_valid(form)


class NewsDelete(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/post_delete.html'
    success_url = reverse_lazy('NewsPortal:news_list')
    login_url = '/accounts/login/'
    permission_required = 'NewsPortal.delete_post'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('account_login')
        else:
            messages.error(self.request, "У вас нет прав для удаления новостей. Станьте автором!")
            return redirect('NewsPortal:become_author')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author.user != request.user:
            raise PermissionDenied("Вы не являетесь автором этой новости")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(post_type='NW')


class ArticleCreate(AuthorRequiredMixin, LoginRequiredMixin, CreateView):
    form_class = NewsCreateForm
    model = Post
    template_name = 'news/article_edit.html'
    login_url = '/accounts/login/'
    permission_required = 'NewsPortal.add_post'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('account_login')
        else:
            messages.error(self.request, "У вас нет прав для создания статей. Станьте автором!")
            return redirect('NewsPortal:become_author')

    def form_valid(self, form):

        try:
            author = self.request.user.author
        except Author.DoesNotExist:
            author = Author.objects.create(user=self.request.user)

        post = form.save(commit=False)
        post.author = author
        post.post_type = Post.ARTICLE
        post.save()

        for category in form.cleaned_data['categories']:
            PostCategory.objects.create(post=post, category=category)

        self.object = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('NewsPortal:article_detail', kwargs={'pk': self.object.pk})


class ArticleUpdate(LoginRequiredMixin, UpdateView):
    form_class = NewsCreateForm
    model = Post
    template_name = 'news/article_edit.html'
    login_url = '/accounts/login/'
    permission_required = 'NewsPortal.change_post'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('account_login')
        else:
            messages.error(self.request, "У вас нет прав для редактирования статей. Станьте автором!")
            return redirect('NewsPortal:become_author')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author.user != request.user:
            raise PermissionDenied("Вы не являетесь автором этой новости")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(post_type='AR')

    def get_success_url(self):
        return reverse_lazy('NewsPortal:article_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):

        post = form.save(commit=False)
        post.save()

        PostCategory.objects.filter(post=post).delete()

        for category in form.cleaned_data['categories']:
            PostCategory.objects.create(post=post, category=category)

        return super().form_valid(form)


class ArticleDelete(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/post_delete.html'
    success_url = reverse_lazy('NewsPortal:article_list')
    login_url = '/accounts/login/'
    permission_required = 'NewsPortal.delete_post'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('account_login')
        else:
            messages.error(self.request, "У вас нет прав для удаления статей. Станьте автором!")
            return redirect('NewsPortal:become_author')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author.user != request.user:
            raise PermissionDenied("Вы не являетесь автором этой новости")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(post_type='AR')


@login_required
def become_author(request):
    user = request.user
    if not Author.objects.filter(user=user).exists():
        Author.objects.create(user=user)
        send_author_request_email(user)
        messages.success(request, 'Ваша заявка на статус автора отправлена администратору!')
    return redirect('NewsPortal:profile')


@login_required
def profile(request):
    try:
        subscriber = request.user.digest_subscriber
    except Subscriber.DoesNotExist:
        subscriber = None

    if request.method == 'POST' and 'toggle_digest' in request.POST:
        if not subscriber:
            subscriber = Subscriber.objects.create(user=request.user)

        if subscriber.unsubscribed_at:
            subscriber.unsubscribed_at = None
            messages.success(request, "Вы подписались на еженедельную рассылку")
        else:
            subscriber.unsubscribed_at = timezone.now()
            messages.success(request, "Вы отписались от еженедельной рассылки")
        subscriber.save()
        return redirect('NewsPortal:profile')

    subscribed_categories = subscriber.categories.all() if subscriber else []

    context = {
        'user': request.user,
        'subscriber': subscriber,
        'subscribed_categories': subscribed_categories
    }
    return render(request, 'account/profile.html', context)
