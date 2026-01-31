from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    # Schools
    path('', views.school_list_view, name='list'),
    path('create/', views.school_create_view, name='create'),
    path('<int:pk>/', views.school_detail_view, name='detail'),
    path('<int:pk>/edit/', views.school_edit_view, name='edit'),
    path('<int:pk>/delete/', views.school_delete_view, name='delete'),
    
    # Subjects
    path('subjects/', views.subject_list_view, name='subjects'),
    path('subjects/create/', views.subject_create_view, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit_view, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete_view, name='subject_delete'),
    
    # Master Students
    path('students/', views.master_student_list_view, name='master_students'),
    path('students/upload/', views.master_student_upload_view, name='master_student_upload'),
    path('<int:school_pk>/students/add/', views.master_student_add_view, name='master_student_add'),
    path('students/<int:pk>/edit/', views.master_student_edit_view, name='master_student_edit'),
    path('students/<int:pk>/delete/', views.master_student_delete_view, name='master_student_delete'),
]
