from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    # Teacher/Admin - Exam Management
    path('', views.exam_list_view, name='exam_list'),
    path('create/', views.exam_create_view, name='exam_create'),
    path('<int:pk>/edit/', views.exam_edit_view, name='exam_edit'),
    path('<int:pk>/delete/', views.exam_delete_view, name='exam_delete'),
    path('<int:pk>/questions/', views.exam_questions_view, name='exam_questions'),
    path('<int:exam_pk>/questions/add/', views.add_question_view, name='add_question'),
    path('questions/<int:pk>/edit/', views.edit_question_view, name='edit_question'),
    path('questions/<int:pk>/delete/', views.delete_question_view, name='delete_question'),
    path('<int:pk>/results/', views.exam_results_view, name='exam_results'),
    path('attempts/<int:pk>/answers/', views.view_attempt_answers_view, name='view_attempt_answers'),
    path('attempts/<int:pk>/unlock/', views.unlock_attempt_view, name='unlock_attempt'),
    
    # Student - Exam Taking
    path('my-exams/', views.student_exams_view, name='student_exams'),
    path('<int:pk>/start/', views.start_exam_view, name='start_exam'),
    path('take/<int:pk>/', views.take_exam_view, name='take_exam'),
    path('take/<int:attempt_pk>/save-answer/', views.save_answer_view, name='save_answer'),
    path('take/<int:attempt_pk>/log-event/', views.log_proctor_event_view, name='log_proctor_event'),
    path('take/<int:pk>/submit/', views.submit_exam_view, name='submit_exam'),
    path('result/<int:pk>/', views.exam_result_view, name='exam_result'),
]
