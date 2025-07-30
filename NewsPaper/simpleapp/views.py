from django.shortcuts import render, get_object_or_404
# Импортируем класс, который говорит нам о том,
# что в этом представлении мы будем выводить список объектов из БД
from django.views.generic import ListView, DetailView
from .models import Product
from datetime import datetime



class ProductsList(ListView):
    # Указываем модель, объекты которой мы будем выводить
    model = Product
    # Поле, которое будет использоваться для сортировки объектов
    ordering = 'name'
    # Указываем имя шаблона, в котором будут все инструкции о том,
    # как именно пользователю должны быть показаны наши объекты
    template_name = 'products.html'
    # Это имя списка, в котором будут лежать все объекты.
    # Его надо указать, чтобы обратиться к списку объектов в html-шаблоне.
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = datetime.utcnow()
        context['next_sale'] = "Распродажа в среду!"
        return context


class ProductDetail(DetailView):
    # Модель всё та же, но мы хотим получать информацию по отдельному товару
    model = Product
    # Используем другой шаблон — product.html
    template_name = 'simpleapp/product_detail.html'
    # Название объекта, в котором будет выбранный пользователем продукт
    context_object_name = 'product'
    pk_url_kwarg = 'id'


# Create your views here.
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'simpleapp/product_detail.html', {'product': product})


def product_list(request):
    products = Product.objects.all()
    # queryset=Product.objects.order_by(
    #    '-name'
    # )
    return render(request, 'simpleapp/product_list.html', {'products': products})
