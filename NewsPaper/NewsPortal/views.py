from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .filters import PostFilter
from .forms import PostForm
from .models import Post, Author
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render


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
def become_author(request):
    author_group, created = Group.objects.get_or_create(name='authors')
    request.user.groups.add(author_group)
    from .models import Author
    Author.objects.get_or_create(user=request.user)

    return redirect('NewsPortal:profile')


def news_detail(request, pk):
    news = get_object_or_404(Post, pk=pk, post_type='NW')
    return render(request, 'news/news_detail.html', {'news': news})


def article_list(request):
    articles = Post.objects.filter(post_type='AR').order_by('-created_at')
    paginator = Paginator(articles, 10)  # 10 статей на странице
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
    paginator = Paginator(news, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/news_list.html', {
        'page_obj': page_obj,
        'total_news': news.count()
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
    form_class = PostForm
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
        post = form.save(commit=False)
        post.post_type = 'NW'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('NewsPortal:news_detail', kwargs={'pk': self.object.pk})


class NewsUpdate(LoginRequiredMixin, UpdateView):
    form_class = PostForm
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
    form_class = PostForm
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
        post = form.save(commit=False)
        post.post_type = 'AR'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('NewsPortal:article_detail', kwargs={'pk': self.object.pk})


class ArticleUpdate(LoginRequiredMixin, UpdateView):
    form_class = PostForm
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
    author_group = Group.objects.get_or_create(name='authors')[0]
    request.user.groups.add(author_group)

    Author.objects.get_or_create(user=request.user)

    return redirect('NewsPortal:profile')


@login_required
def profile(request):
    try:
        author_profile = Author.objects.get(user=request.user)
    except Author.DoesNotExist:
        author_profile = None

    context = {
        'user': request.user,
        'is_author': request.user.groups.filter(name='authors').exists(),
        'author_profile': author_profile,
    }
    return render(request, 'account/profile.html', context)

# Create your views here.
