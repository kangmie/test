from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home_view, name='home'),
    path('analytics/', views.tenant_analytics_view, name='analytics'),
    path('analytics/<int:tenant_id>/', views.tenant_analytics_view, name='tenant_analytics'),
]