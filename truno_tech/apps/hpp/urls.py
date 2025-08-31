from django.urls import path
from . import views

app_name = 'hpp'

urlpatterns = [
    # Bahan URLs
    path('bahan/', views.bahan_list_view, name='bahan_list'),
    path('bahan/create/', views.bahan_create_view, name='bahan_create'),
    path('bahan/<int:bahan_id>/edit/', views.bahan_edit_view, name='bahan_edit'),
    path('bahan/<int:bahan_id>/delete/', views.bahan_delete_view, name='bahan_delete'),
    
    # HPP URLs
    path('', views.hpp_list_view, name='list'),
    path('create/', views.hpp_create_view, name='create'),
    path('<int:hpp_id>/', views.hpp_detail_view, name='detail'),
    
    # AJAX URLs
    path('api/bahan/', views.get_bahan_data, name='get_bahan_data'),
]