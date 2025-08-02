from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from .filters import PostFilter
from .forms import PostForm
from .models import Post
from django.core.paginator import Paginator


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


class NewsCreate(CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/post_edit.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.post_type = 'NW'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('NewsPortal:news_detail', kwargs={'pk': self.object.pk})


class NewsUpdate(UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/post_edit.html'

    def get_queryset(self):
        return super().get_queryset().filter(post_type='NW')

    def get_success_url(self):
        return reverse_lazy('NewsPortal:news_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        return super().form_valid(form)


class NewsDelete(DeleteView):
    model = Post
    template_name = 'news/post_delete.html'
    success_url = reverse_lazy('NewsPortal:news_list')

    def get_queryset(self):
        return super().get_queryset().filter(post_type='NW')


class ArticleCreate(CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/article_edit.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.post_type = 'AR'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('NewsPortal:article_detail', kwargs={'pk': self.object.pk})


class ArticleUpdate(UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/article_edit.html'

    def get_queryset(self):
        return super().get_queryset().filter(post_type='AR')

    def get_success_url(self):
        return reverse_lazy('NewsPortal:article_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        return super().form_valid(form)


class ArticleDelete(DeleteView):
    model = Post
    template_name = 'news/post_delete.html'
    success_url = reverse_lazy('NewsPortal:article_list')

    def get_queryset(self):
        return super().get_queryset().filter(post_type='AR')

# Create your views here.
