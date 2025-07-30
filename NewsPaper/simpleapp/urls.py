from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pages/', include('django.contrib.flatpages.urls')),
    path('', views.product_list, name='product_list'),
    path('<int:id>/', views.ProductDetail.as_view(), name='ProductDetail'),
]