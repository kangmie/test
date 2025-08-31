from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Category URLs
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/create/', views.category_create_view, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_edit_view, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete_view, name='category_delete'),
    
    # Product URLs
    path('', views.product_list_view, name='list'),
    path('create/', views.product_create_view, name='create'),
    path('<int:product_id>/edit/', views.product_edit_view, name='edit'),
    path('<int:product_id>/delete/', views.product_delete_view, name='delete'),
    path('<int:product_id>/stock/', views.product_stock_adjustment_view, name='stock_adjustment'),
    
    # AJAX URLs
    path('api/categories/', views.get_categories_by_tenant, name='get_categories_by_tenant'),
]