from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list_view, name='list'),
    path('create/', views.order_create_view, name='create'),
    path('<int:order_id>/', views.order_detail_view, name='detail'),
    
    # AJAX URLs
    path('api/products/', views.get_products_by_tenant, name='get_products_by_tenant'),
]