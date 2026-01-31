from django.urls import path
from . import views

app_name = 'zipgrade'

urlpatterns = [
    path('upload/', views.upload_view, name='upload'),
    path('upload/preview/', views.preview_view, name='preview'),
    path('upload/confirm/', views.confirm_upload_view, name='confirm'),
    path('upload/cancel/', views.cancel_upload_view, name='cancel'),
    
    path('results/', views.results_view, name='results'),
    path('exam/<int:pk>/', views.exam_detail_view, name='exam_detail'),
    path('exam/<int:pk>/delete/', views.delete_exam_view, name='exam_delete'),
    
    # Subject splits
    path('exam/<int:exam_pk>/split/add/', views.add_subject_split_view, name='add_split'),
    path('split/<int:pk>/edit/', views.edit_subject_split_view, name='edit_split'),
    path('split/<int:pk>/delete/', views.delete_subject_split_view, name='delete_split'),
    
    # Unknown student editing
    path('result/<int:pk>/edit/', views.edit_unknown_student_view, name='edit_unknown_student'),
]
