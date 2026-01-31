from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Profile Management
    path('profile/', views.profile_view, name='profile'),
    path('password/change/', views.password_change_view, name='password_change'),
    
    # User Management (Admin only)
    path('users/', views.users_list_view, name='users'),
    path('users/teacher/new/', views.teacher_create_view, name='teacher_create'),
    path('users/teacher/<int:pk>/edit/', views.teacher_edit_view, name='teacher_edit'),
    path('users/admin/new/', views.admin_create_view, name='admin_create'),
    path('users/admin/<int:pk>/edit/', views.admin_edit_view, name='admin_edit'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
    path('users/<int:pk>/reset-password/', views.admin_reset_password_view, name='admin_reset_password'),
]
