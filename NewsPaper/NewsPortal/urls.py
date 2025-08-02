from django.urls import path
from . import views

app_name = 'NewsPortal'

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('<int:pk>/', views.news_detail, name='news_detail'),
    path('search/', views.PostSearch.as_view(), name='post_search'),
    path('create/', views.NewsCreate.as_view(), name='news_create'),
    path('<int:pk>/edit/', views.NewsUpdate.as_view(), name='news_edit'),
    path('<int:pk>/delete/', views.NewsDelete.as_view(), name='news_delete'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/create/', views.ArticleCreate.as_view(), name='article_create'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('articles/<int:pk>/edit/', views.ArticleUpdate.as_view(), name='article_edit'),
    path('articles/<int:pk>/delete/', views.ArticleDelete.as_view(), name='article_delete'),
]