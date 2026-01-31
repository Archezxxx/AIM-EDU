from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('schools/', views.school_analytics_view, name='schools'),
    path('classes/', views.class_analytics_view, name='classes'),
    path('students/', views.student_analytics_view, name='students'),
    path('network/', views.network_analytics_view, name='network'),
    path('export/excel/', views.export_analytics_excel_view, name='export_excel'),
    path('export/pdf/', views.export_analytics_pdf_view, name='export_pdf'),
    # Class exports
    path('export/class/excel/', views.export_class_excel_view, name='export_class_excel'),
    path('export/class/pdf/', views.export_class_pdf_view, name='export_class_pdf'),
    # Student exports
    path('export/student/excel/<int:student_id>/', views.export_student_excel_view, name='export_student_excel'),
    path('export/student/pdf/<int:student_id>/', views.export_student_pdf_view, name='export_student_pdf'),
    # ZipGrade Analytics
    path('zipgrade/', views.zipgrade_analytics_view, name='zipgrade'),
    
    # ===== Advanced Analytics =====
    path('item-analysis/<int:exam_id>/', views.item_analysis_view, name='item_analysis'),
    path('student/<int:student_id>/advanced/', views.student_advanced_analytics_view, name='student_advanced'),
    path('class-heatmap/', views.class_heatmap_view, name='class_heatmap'),
    
    # API Endpoints
    path('api/radar/', views.api_radar_data, name='api_radar'),
    path('api/trend/', views.api_trend_data, name='api_trend'),
    path('api/distribution/', views.api_distribution_data, name='api_distribution'),
    path('api/heatmap/', views.api_heatmap_data, name='api_heatmap'),
]
