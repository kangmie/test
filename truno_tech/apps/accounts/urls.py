from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('create-client/', views.create_client_view, name='create_client'),
    path('create-crew/', views.create_crew_view, name='create_crew'),
    path('delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),
]