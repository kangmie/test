from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('', views.tenant_list_view, name='list'),
    path('create/', views.tenant_create_view, name='create'),
    path('<int:tenant_id>/', views.tenant_detail_view, name='detail'),
    path('<int:tenant_id>/edit/', views.tenant_edit_view, name='edit'),
    path('<int:tenant_id>/delete/', views.tenant_delete_view, name='delete'),
    path('<int:tenant_id>/remove-access/<int:access_id>/', views.remove_crew_access_view, name='remove_access'),
]