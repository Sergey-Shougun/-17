from django.shortcuts import render, get_object_or_404
from .models import Post


def news_list(request):
    news = Post.objects.filter(post_type='NW').order_by('-created_at')
    return render(request, 'news/news_list.html', {
        'news_list': news,
        'total_news': news.count()
    })


def news_detail(request, pk):
    news = get_object_or_404(Post, pk=pk, post_type='NW')
    return render(request, 'news/news_detail.html', {'news': news})

# Create your views here.
