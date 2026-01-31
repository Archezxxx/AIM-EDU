from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from accounts.decorators import teacher_or_admin_required, super_admin_required
from schools.models import School
from exams.models import OnlineExam, ExamAttempt
from .utils import AnalyticsHelper


@login_required
@teacher_or_admin_required
def school_analytics_view(request):
    """School analytics dashboard with Exam/ZipGrade toggle and comparison charts."""
    # Determine which school to show
    school = None
    schools = None
    all_schools = School.objects.filter(is_active=True)
    
    if request.user.is_super_admin:
        school_id = request.GET.get('school_id', '')
        if school_id and school_id != 'all':
            school = get_object_or_404(School, pk=school_id)
        # If 'all' or empty, school remains None (will aggregate all schools)
        schools = all_schools
    else:
        school = request.user.primary_school

    # If no school and not super_admin, show error
    if not school and not request.user.is_super_admin:
        return render(request, 'analytics/schools.html', {'error': _('No school found')})

    # Determine data source (exams or zipgrade)
    source = request.GET.get('source', 'exams')
    if source not in ('exams', 'zipgrade'):
        source = 'exams'

    stats = None
    recent_exams = []
    chart_labels = []
    chart_data = []
    
    # School comparison data
    school_comparison_labels = []
    school_comparison_data = []
    
    # Available exams and subjects for filters
    available_exams = []
    available_subjects = []
    available_folders = []
    selected_folder_ids = []
    selected_exam_ids = request.GET.getlist('exam_ids')
    selected_subject_id = request.GET.get('subject_id')

    if source == 'exams':
        # Online Exam Stats
        if school:
            stats = AnalyticsHelper.get_school_stats(school)
            recent_exams = OnlineExam.objects.filter(school=school).order_by('-created_at')[:5]
            exam_filter = {'exam__school': school}
        else:
            # All schools aggregated
            stats = AnalyticsHelper.get_all_schools_stats()
            recent_exams = OnlineExam.objects.all().order_by('-created_at')[:5]
            exam_filter = {}
        
        # Growth Chart Data (Last 12 weeks of attempts)
        # Growth Chart Data (Last 12 weeks of attempts)
        chart_labels, chart_data = AnalyticsHelper.get_growth_chart_data(school)
    else:
        # ZipGrade Stats
        from zipgrade.models import ZipGradeExam, ExamResult, SubjectSplit, SubjectResult
        from schools.models import Subject
        
        if school:
            zipgrade_exams = ZipGradeExam.objects.filter(school=school)
            from zipgrade.models import ExamFolder
            available_folders = ExamFolder.objects.filter(school=school)
        else:
            zipgrade_exams = ZipGradeExam.objects.all()
            available_folders = []
            
        available_exams = list(ZipGradeExam.objects.all().values('pk', 'title', 'school__name'))
        available_subjects = list(Subject.objects.filter(is_active=True).values('pk', 'name'))
        
        # Filter by selected folders if provided
        selected_folder_ids = request.GET.getlist('folder_ids')
        folder_exam_ids = []
        if selected_folder_ids:
            folder_ids = [int(fid) for fid in selected_folder_ids if fid.isdigit()]
            if folder_ids:
                folder_exams = ZipGradeExam.objects.filter(folder__id__in=folder_ids)
                folder_exam_ids = list(folder_exams.values_list('pk', flat=True))
        
        # Filter by selected exams if provided
        if selected_exam_ids:
            exam_ids = [int(eid) for eid in selected_exam_ids if eid.isdigit()]
            # Combine with folder exams (Union)
            if folder_exam_ids:
                exam_ids = list(set(exam_ids) | set(folder_exam_ids))
        elif folder_exam_ids:
            exam_ids = folder_exam_ids
        else:
            exam_ids = list(zipgrade_exams.values_list('pk', flat=True))
        
        if exam_ids:
            # Get stats based on subject filter or overall
            if selected_subject_id:
                # Filter by subject - use SubjectResult
                subject_results = SubjectResult.objects.filter(
                    result__exam_id__in=exam_ids,
                    subject_split__subject_id=selected_subject_id
                )
                if subject_results.exists():
                    scores = [float(sr.percentage) for sr in subject_results]
                    passed_count = sum(1 for sr in subject_results if sr.percentage >= 60)
                    stats = {
                        'online_exams': {
                            'count': len(scores),
                            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
                            'pass_rate': round(passed_count / len(scores) * 100, 1) if scores else 0,
                            'max_score': round(max(scores), 1) if scores else 0,
                            'min_score': round(min(scores), 1) if scores else 0,
                        }
                    }
                else:
                    stats = {'online_exams': {'count': 0, 'avg_score': 0, 'pass_rate': 0, 'max_score': 0, 'min_score': 0}}
            else:
                zg_stats = AnalyticsHelper.get_zipgrade_exam_stats(exam_ids)
                if zg_stats:
                    stats = {
                        'online_exams': {
                            'count': zg_stats['total_students'],
                            'avg_score': zg_stats['avg_score'],
                            'pass_rate': zg_stats['pass_rate'],
                            'max_score': zg_stats['max_score'],
                            'min_score': zg_stats['min_score'],
                        }
                    }
        else:
            stats = {'online_exams': {'count': 0, 'avg_score': 0, 'pass_rate': 0, 'max_score': 0, 'min_score': 0}}
        
        recent_exams = zipgrade_exams.order_by('-exam_date')[:5]
        
        # ZipGrade chart: results by week
        today = timezone.now()
        for i in range(11, -1, -1):
            start_date = today - timedelta(weeks=i+1)
            end_date = today - timedelta(weeks=i)
            count = ExamResult.objects.filter(
                exam__school=school,
                exam__created_at__range=(start_date, end_date)
            ).count()
            chart_labels.append(end_date.strftime('%d.%m'))
            chart_data.append(count)
        
        # School Comparison Chart (all schools avg scores)
        if request.user.is_super_admin:
            school_comparison_labels, school_comparison_data = AnalyticsHelper.get_school_comparison_data(selected_exam_ids, selected_subject_id)

    context = {
        'school': school,
        'schools': schools,
        'stats': stats,
        'recent_exams': recent_exams,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'source': source,
        'school_comparison_labels': school_comparison_labels,
        'school_comparison_data': school_comparison_data,
        'available_exams': available_exams,
        'available_subjects': available_subjects,
        'selected_exam_ids': selected_exam_ids,
        'selected_subject_id': selected_subject_id,
        'available_folders': available_folders,
        'selected_folder_ids': selected_folder_ids,
    }
    
    return render(request, 'analytics/schools.html', context)



@login_required
@teacher_or_admin_required
def class_analytics_view(request):
    """Class analytics view with per-class statistics and source toggle."""
    # Determine school
    if request.user.is_super_admin:
        school_id = request.GET.get('school_id')
        if school_id:
            school = get_object_or_404(School, pk=school_id)
        else:
            school = School.objects.first()
        schools = School.objects.all()
    else:
        school = request.user.primary_school
        schools = None
    
    if not school:
        return render(request, 'analytics/classes.html', {'error': _('No school found')})
    
    # Determine data source
    source = request.GET.get('source', 'exams')
    if source not in ('exams', 'zipgrade'):
        source = 'exams'
    
    # Get list of classes
    classes = AnalyticsHelper.get_classes_list(school)
    
    # Get selected class
    selected_grade = request.GET.get('grade')
    selected_section = request.GET.get('section')
    stats = None
    selected_class = None
    
    if source == 'exams':
        if selected_grade and selected_section:
            stats = AnalyticsHelper.get_class_stats(school, selected_grade, selected_section)
            selected_class = {'grade': selected_grade, 'section': selected_section, 
                              'name': f"{selected_grade}{selected_section}"}
        elif classes:
            selected_grade = classes[0]['grade']
            selected_section = classes[0]['section']
            stats = AnalyticsHelper.get_class_stats(school, selected_grade, selected_section)
            selected_class = classes[0]
        
        # Chart data for class comparison
        chart_labels = []
        chart_data = []
        for cls in classes[:10]:
            cls_stats = AnalyticsHelper.get_class_stats(school, cls['grade'], cls['section'])
            chart_labels.append(cls['name'])
            chart_data.append(cls_stats['avg_score'])
    else:
        # ZipGrade source
        from zipgrade.models import ZipGradeExam
        zipgrade_exams = ZipGradeExam.objects.filter(school=school)
        exam_ids = list(zipgrade_exams.values_list('pk', flat=True))
        
        if selected_grade and selected_section:
            selected_class = {'grade': selected_grade, 'section': selected_section, 
                              'name': f"{selected_grade}{selected_section}"}
        elif classes:
            selected_grade = classes[0]['grade']
            selected_section = classes[0]['section']
            selected_class = classes[0]
        
        # Get ZipGrade class stats
        if exam_ids and selected_class:
            class_breakdown = AnalyticsHelper.get_zipgrade_class_breakdown(exam_ids, school)
            # Find stats for selected class
            for cls_data in class_breakdown:
                if cls_data['name'] == selected_class['name']:
                    stats = {
                        'total_students': cls_data['student_count'],
                        'avg_score': cls_data['avg_score'],
                        'max_score': cls_data['max_score'],
                        'min_score': cls_data['min_score'],
                        'pass_rate': cls_data.get('pass_rate', 0),
                        'top_students': [],
                    }
                    break
            if not stats:
                stats = {
                    'total_students': 0,
                    'avg_score': 0,
                    'max_score': 0,
                    'min_score': 0,
                    'pass_rate': 0,
                    'top_students': [],
                }
            
            # Chart data from ZipGrade class breakdown
            chart_labels = [c['name'] for c in class_breakdown[:10]]
            chart_data = [c['avg_score'] for c in class_breakdown[:10]]
        else:
            stats = {'total_students': 0, 'avg_score': 0, 'max_score': 0, 'min_score': 0, 'pass_rate': 0, 'top_students': []}
            chart_labels = []
            chart_data = []
    
    context = {
        'school': school,
        'schools': schools,
        'classes': classes,
        'selected_class': selected_class,
        'stats': stats,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'source': source,
    }
    
    return render(request, 'analytics/classes.html', context)



@login_required
@teacher_or_admin_required
def student_analytics_view(request):
    """Enhanced Student Analytics with MasterStudent list and filters."""
    from schools.models import School, MasterStudent
    from zipgrade.models import ExamResult, SubjectResult, ZipGradeExam
    from django.db.models import Max, Min, Avg
    from django.core.paginator import Paginator
    
    # Determine data source
    source = request.GET.get('source', 'zipgrade')
    if source not in ('exams', 'zipgrade'):
        source = 'zipgrade'
    
    # Get available schools for filter
    if request.user.is_super_admin:
        schools = School.objects.filter(is_active=True)
    else:
        schools = School.objects.filter(pk=request.user.primary_school_id)
    
    # Get filter values
    school_id = request.GET.get('school_id')
    grade_filter = request.GET.get('grade', '')
    section_filter = request.GET.get('section', '')
    name_search = request.GET.get('q', '')
    selected_exam_ids = request.GET.getlist('exam_ids')
    selected_subject_ids = request.GET.getlist('subject_ids')
    
    # Determine selected school
    if school_id:
        selected_school = get_object_or_404(School, pk=school_id)
    elif request.user.is_super_admin:
        selected_school = schools.first()
    else:
        selected_school = request.user.primary_school
    
    # Build MasterStudent queryset with filters
    students_qs = MasterStudent.objects.all()
    
    if selected_school:
        students_qs = students_qs.filter(school=selected_school)
    
    if grade_filter:
        students_qs = students_qs.filter(grade=grade_filter)
    
    if section_filter:
        students_qs = students_qs.filter(section=section_filter)
    
    if name_search:
        students_qs = students_qs.filter(
            Q(name__icontains=name_search) | 
            Q(surname__icontains=name_search) |
            Q(student_id__icontains=name_search)
        )
    
    students_qs = students_qs.order_by('grade', 'section', 'surname', 'name')
    
    # Get unique grades and sections for filter dropdowns
    all_grades = MasterStudent.objects.filter(school=selected_school).values_list('grade', flat=True).distinct().order_by('grade') if selected_school else []
    all_sections = MasterStudent.objects.filter(school=selected_school).values_list('section', flat=True).distinct().order_by('section') if selected_school else []
    
    # Pagination
    paginator = Paginator(students_qs, 25)
    page_number = request.GET.get('page', 1)
    students_page = paginator.get_page(page_number)
    
    # Get selected student
    student = None
    student_id = request.GET.get('student_id')
    if student_id:
        student = get_object_or_404(MasterStudent, pk=student_id)
    
    # Get available exams for multi-select
    available_exams = []
    available_subjects = []
    if selected_school and source == 'zipgrade':
        available_exams = ZipGradeExam.objects.filter(school=selected_school).order_by('-exam_date')
        from schools.models import Subject
        available_subjects = Subject.objects.filter(Q(school=selected_school) | Q(school__isnull=True)).order_by('name')
    
    context = {
        'schools': schools,
        'selected_school': selected_school,
        'students': students_page,
        'student': student,
        'source': source,
        'grade_filter': grade_filter,
        'section_filter': section_filter,
        'name_search': name_search,
        'all_grades': list(all_grades),
        'all_sections': list(all_sections),
        'available_exams': available_exams,
        'available_subjects': available_subjects,
        'selected_exam_ids': selected_exam_ids,
        'selected_subject_ids': selected_subject_ids,
    }
    
    # If student selected, get analytics
    if student:
        if source == 'zipgrade':
            # Get all results for this student
            results = ExamResult.objects.filter(
                student=student
            ).select_related('exam').order_by('-exam__exam_date')
            
            # Filter by selected exams if any
            if selected_exam_ids:
                results = results.filter(exam_id__in=selected_exam_ids)
            
            if results.exists():
                scores = [float(r.percentage) for r in results]
                passed_count = sum(1 for r in results if r.percentage >= 60)
                
                # Get subject breakdown with strength/weakness analysis
                result_ids = [r.pk for r in results]
                subject_results = SubjectResult.objects.filter(
                    result_id__in=result_ids
                ).select_related('subject_split__subject')
                
                # Filter by selected subjects if any
                if selected_subject_ids:
                    subject_results = subject_results.filter(subject_split__subject_id__in=selected_subject_ids)
                
                # Aggregate subject scores
                subject_scores = {}
                for sr in subject_results:
                    subject_name = sr.subject_split.subject.name
                    subject_id = sr.subject_split.subject.pk
                    if subject_name not in subject_scores:
                        subject_scores[subject_name] = {'total': 0, 'count': 0, 'id': subject_id, 'scores': []}
                    subject_scores[subject_name]['total'] += float(sr.percentage)
                    subject_scores[subject_name]['count'] += 1
                    subject_scores[subject_name]['scores'].append(float(sr.percentage))
                
                # Calculate averages and determine strengths/weaknesses
                subject_breakdown = []
                radar_labels = []
                radar_data = []
                
                for name, data in subject_scores.items():
                    avg = round(data['total'] / data['count'], 1) if data['count'] > 0 else 0
                    subject_breakdown.append({
                        'id': data['id'],
                        'name': name,
                        'avg_score': avg,
                        'exam_count': data['count'],
                        'trend': 'up' if len(data['scores']) > 1 and data['scores'][-1] > data['scores'][0] else 'down'
                    })
                    radar_labels.append(name)
                    radar_data.append(avg)
                
                # Sort by avg_score to find strengths/weaknesses
                subject_breakdown.sort(key=lambda x: x['avg_score'], reverse=True)
                
                # Mark top 3 as strengths, bottom 3 as weaknesses
                for i, subj in enumerate(subject_breakdown):
                    if i < 3:
                        subj['category'] = 'strong'
                    elif i >= len(subject_breakdown) - 3:
                        subj['category'] = 'weak'
                    else:
                        subj['category'] = 'average'
                
                # Get class average for comparison
                class_avg = ExamResult.objects.filter(
                    student__school=student.school,
                    student__grade=student.grade
                ).aggregate(avg=Avg('percentage'))['avg'] or 0
                
                context.update({
                    'total_exams': results.count(),
                    'avg_score': round(sum(scores) / len(scores), 1),
                    'max_score': round(max(scores), 1),
                    'min_score': round(min(scores), 1),
                    'passed_exams': passed_count,
                    'class_avg': round(class_avg, 1),
                    'attempts': results,
                    'chart_labels': [r.exam.title[:15] for r in reversed(list(results))],
                    'chart_data': [float(r.percentage) for r in reversed(list(results))],
                    'subject_breakdown': subject_breakdown,
                    'radar_labels': radar_labels,
                    'radar_data': radar_data,
                    'strengths': [s for s in subject_breakdown if s.get('category') == 'strong'][:3],
                    'weaknesses': [s for s in subject_breakdown if s.get('category') == 'weak'][:3],
                })
        else:
            # Online Exams source
            # Match via email if student has linked user account
            from accounts.models import User
            user_student = User.objects.filter(
                Q(email__icontains=student.student_id) | 
                Q(first_name=student.name, last_name=student.surname)
            ).first()
            
            if user_student:
                attempts = ExamAttempt.objects.filter(student=user_student, status='completed').order_by('-started_at')
                
                if attempts.exists():
                    stats = attempts.aggregate(
                        avg_score=Avg('percentage'),
                        max_score=Max('percentage'),
                        min_score=Min('percentage')
                    )
                    passed_count = sum(1 for a in attempts if a.percentage >= (a.exam.passing_score or 60))
                    
                    context.update({
                        'total_exams': attempts.count(),
                        'avg_score': round(stats['avg_score'], 1),
                        'max_score': round(stats['max_score'], 1),
                        'min_score': round(stats['min_score'], 1),
                        'passed_exams': passed_count,
                        'attempts': attempts,
                        'chart_labels': [a.exam.title[:15] for a in reversed(attempts)],
                        'chart_data': [float(a.percentage) for a in reversed(attempts)]
                    })
    
    return render(request, 'analytics/students.html', context)


@login_required
@super_admin_required
def network_analytics_view(request):
    """Network-wide analytics view - placeholder."""
    return render(request, 'analytics/network.html')


@login_required
@teacher_or_admin_required
def export_analytics_excel_view(request):
    """Export analytics to Excel."""
    from .utils import ReportGenerator
    
    # Determine school similarly to school_analytics_view
    school = None
    if request.user.is_super_admin:
        school_id = request.GET.get('school_id')
        if school_id:
            school = get_object_or_404(School, pk=school_id)
        else:
            school = School.objects.first()
    else:
        school = request.user.primary_school
        
    if not school:
        return render(request, 'analytics/schools.html', {'error': _('No school found')})
        
    return ReportGenerator.generate_excel_report(school)


@login_required
@teacher_or_admin_required
def export_analytics_pdf_view(request):
    """Export analytics to PDF."""
    from .utils import ReportGenerator
    
    school = None
    if request.user.is_super_admin:
        school_id = request.GET.get('school_id')
        if school_id:
            school = get_object_or_404(School, pk=school_id)
        else:
            school = School.objects.first()
    else:
        school = request.user.primary_school
        
    if not school:
        return render(request, 'analytics/schools.html', {'error': _('No school found')})
        
    return ReportGenerator.generate_pdf_report(school)


@login_required
@teacher_or_admin_required
def export_class_excel_view(request):
    """Export class analytics to Excel."""
    from .utils import ReportGenerator
    
    school = None
    if request.user.is_super_admin:
        school_id = request.GET.get('school_id')
        if school_id:
            school = get_object_or_404(School, pk=school_id)
        else:
            school = School.objects.first()
    else:
        school = request.user.primary_school
        
    if not school:
        return render(request, 'analytics/classes.html', {'error': _('No school found')})
    
    grade = request.GET.get('grade')
    section = request.GET.get('section')
    
    if not grade or not section:
        return render(request, 'analytics/classes.html', {'error': _('Please select a class')})
        
    return ReportGenerator.generate_class_excel_report(school, grade, section)


@login_required
@teacher_or_admin_required
def export_class_pdf_view(request):
    """Export class analytics to PDF."""
    from .utils import ReportGenerator
    
    school = None
    if request.user.is_super_admin:
        school_id = request.GET.get('school_id')
        if school_id:
            school = get_object_or_404(School, pk=school_id)
        else:
            school = School.objects.first()
    else:
        school = request.user.primary_school
        
    if not school:
        return render(request, 'analytics/classes.html', {'error': _('No school found')})
    
    grade = request.GET.get('grade')
    section = request.GET.get('section')
    
    if not grade or not section:
        return render(request, 'analytics/classes.html', {'error': _('Please select a class')})
        
    return ReportGenerator.generate_class_pdf_report(school, grade, section)


@login_required
@teacher_or_admin_required
def export_student_excel_view(request, student_id):
    """Export student analytics to Excel."""
    from .utils import ReportGenerator
    from accounts.models import User
    
    student = get_object_or_404(User, pk=student_id, role='student')
    return ReportGenerator.generate_student_excel_report(student)


@login_required
@teacher_or_admin_required
def export_student_pdf_view(request, student_id):
    """Export student analytics to PDF."""
    from .utils import ReportGenerator
    from accounts.models import User
    
    student = get_object_or_404(User, pk=student_id, role='student')
    return ReportGenerator.generate_student_pdf_report(student)


@login_required
@teacher_or_admin_required
def zipgrade_analytics_view(request):
    """ZipGrade exam analytics with multi-exam selection."""
    from zipgrade.models import ZipGradeExam
    
    # Determine school
    if request.user.is_super_admin:
        school_id = request.GET.get('school_id')
        if school_id:
            school = get_object_or_404(School, pk=school_id)
        else:
            school = School.objects.first()
        schools = School.objects.all()
    else:
        school = request.user.primary_school
        schools = None
    
    if not school:
        return render(request, 'analytics/zipgrade.html', {'error': _('No school found')})
    
    # Get all ZipGrade exams for the school
    exams = AnalyticsHelper.get_zipgrade_exams_for_school(school)
    
    # Handle form submission for analysis
    stats = None
    class_breakdown = []
    subject_breakdown = []
    student_ranking = []
    selected_exam_ids = []
    
    if request.method == 'POST':
        # Get selected exam IDs from checkboxes
        selected_exam_ids = request.POST.getlist('exam_ids')
        selected_exam_ids = [int(x) for x in selected_exam_ids if x.isdigit()]
    elif request.GET.get('exam_ids'):
        # Support GET for direct links
        selected_exam_ids = [int(x) for x in request.GET.get('exam_ids', '').split(',') if x.isdigit()]
    
    if selected_exam_ids:
        # Get aggregated stats
        stats = AnalyticsHelper.get_zipgrade_exam_stats(selected_exam_ids)
        class_breakdown = AnalyticsHelper.get_zipgrade_class_breakdown(selected_exam_ids, school)
        subject_breakdown = AnalyticsHelper.get_zipgrade_subject_breakdown(selected_exam_ids)
        student_ranking = AnalyticsHelper.get_zipgrade_student_ranking(selected_exam_ids, limit=20)
    
    # Prepare chart data
    chart_labels = [c['name'] for c in class_breakdown]
    chart_data = [c['avg_score'] for c in class_breakdown]
    
    context = {
        'school': school,
        'schools': schools,
        'exams': exams,
        'selected_exam_ids': selected_exam_ids,
        'stats': stats,
        'class_breakdown': class_breakdown,
        'subject_breakdown': subject_breakdown,
        'student_ranking': student_ranking,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    
    return render(request, 'analytics/zipgrade.html', context)


# ============ Advanced Analytics Views ============

@login_required
@teacher_or_admin_required
def item_analysis_view(request, exam_id):
    """Item-level distractor analysis for a specific exam."""
    from .advanced_analytics import AdvancedAnalyticsHelper
    from zipgrade.models import ZipGradeExam
    import json
    
    source = request.GET.get('source', 'zipgrade')
    
    if source == 'zipgrade':
        exam = get_object_or_404(ZipGradeExam, pk=exam_id)
        exam_title = exam.title
    else:
        exam = get_object_or_404(OnlineExam, pk=exam_id)
        exam_title = exam.title
    
    analysis = AdvancedAnalyticsHelper.get_distractor_analysis(exam_id, source=source)
    
    context = {
        'exam': exam,
        'exam_title': exam_title,
        'analysis': analysis,
        'analysis_json': json.dumps(analysis),
        'source': source,
    }
    
    return render(request, 'analytics/item_analysis.html', context)


@login_required
@teacher_or_admin_required
def student_advanced_analytics_view(request, student_id):
    """Advanced analytics for a specific student: radar, trend, gaps."""
    from .advanced_analytics import AdvancedAnalyticsHelper
    from schools.models import MasterStudent
    from zipgrade.models import ZipGradeExam, ExamResult
    import json
    
    source = request.GET.get('source', 'zipgrade')
    
    # Get student from MasterStudent (not User)
    student = get_object_or_404(MasterStudent, pk=student_id)
    
    # Get exam IDs from request or use all available for this student
    exam_ids = request.GET.getlist('exam_ids')
    
    if source == 'zipgrade':
        if not exam_ids:
            # Get all exams where this student has results
            exam_ids = list(ExamResult.objects.filter(
                student=student
            ).values_list('exam_id', flat=True).distinct())
        else:
            exam_ids = [int(x) for x in exam_ids if x.isdigit()]
        
        student_id_for_calc = student.pk
        
        # Get available exams for multi-select
        available_exams = ZipGradeExam.objects.filter(
            school=student.school
        ).order_by('-exam_date')
    else:
        # Online Exams source - try to find linked User account
        from accounts.models import User
        from django.db.models import Q
        
        user_student = User.objects.filter(
            Q(email__icontains=student.student_id) |
            Q(first_name__iexact=student.name, last_name__iexact=student.surname)
        ).first()
        
        if not exam_ids:
            if user_student:
                exam_ids = list(ExamAttempt.objects.filter(
                    student=user_student, status='completed'
                ).values_list('exam_id', flat=True))
            else:
                exam_ids = []
        else:
            exam_ids = [int(x) for x in exam_ids if x.isdigit()]
        
        student_id_for_calc = user_student.pk if user_student else None
        
        # Get available exams for multi-select
        available_exams = OnlineExam.objects.filter(
            school=student.school
        ).order_by('-created_at')
    
    # Generate chart data
    radar_data = []
    trend_data = {'labels': [], 'scores': [], 'movingAverage': []}
    gap_data = []
    weakest_areas = []
    
    if exam_ids and student_id_for_calc:
        radar_data = AdvancedAnalyticsHelper.get_student_radar_data(
            student_id_for_calc, exam_ids, source=source
        )
        trend_data = AdvancedAnalyticsHelper.get_progressive_trend(
            student_id_for_calc, exam_ids, source=source
        )
        gap_data = AdvancedAnalyticsHelper.get_competency_gap(
            student_id_for_calc, exam_ids, source=source
        )
        weakest_areas = AdvancedAnalyticsHelper.get_weakest_areas(
            student_id_for_calc, exam_ids, source=source
        )
    
    context = {
        'student': student,
        'available_exams': available_exams,
        'selected_exam_ids': [str(x) for x in exam_ids],
        'radar_data': json.dumps(radar_data),
        'trend_data': json.dumps(trend_data),
        'gap_data': json.dumps(gap_data),
        'weakest_areas': weakest_areas,
        'source': source,
    }
    
    return render(request, 'analytics/student_advanced.html', context)


@login_required
@teacher_or_admin_required  
def class_heatmap_view(request):
    """Topic mastery heatmap for a class."""
    from .advanced_analytics import AdvancedAnalyticsHelper
    from zipgrade.models import ZipGradeExam
    import json
    
    school = request.user.primary_school
    grade = request.GET.get('grade')
    section = request.GET.get('section')
    exam_ids = request.GET.getlist('exam_ids')
    
    if not exam_ids:
        # Use recent exams
        exam_ids = list(ZipGradeExam.objects.filter(
            school=school
        ).order_by('-exam_date')[:10].values_list('pk', flat=True))
    else:
        exam_ids = [int(x) for x in exam_ids]
    
    # Get available classes
    classes = AnalyticsHelper.get_classes_list(school) if school else []
    
    # Get available exams
    available_exams = ZipGradeExam.objects.filter(school=school).order_by('-exam_date')
    
    # Generate heatmap
    heatmap_data = AdvancedAnalyticsHelper.get_topic_mastery_heatmap(
        exam_ids, school=school, grade=grade, section=section
    )
    
    # Grade distribution
    distribution = AdvancedAnalyticsHelper.get_grade_distribution(exam_ids, source='zipgrade')
    
    context = {
        'school': school,
        'classes': classes,
        'selected_grade': grade,
        'selected_section': section,
        'available_exams': available_exams,
        'selected_exam_ids': [str(x) for x in exam_ids],
        'heatmap_data': json.dumps(heatmap_data),
        'distribution_data': json.dumps(distribution),
    }
    
    return render(request, 'analytics/class_heatmap.html', context)


# ============ API Endpoints for AJAX ============

@login_required
@teacher_or_admin_required
def api_radar_data(request):
    """API endpoint for radar chart data."""
    from .advanced_analytics import AdvancedAnalyticsHelper
    from django.http import JsonResponse
    
    student_id = request.GET.get('student_id')
    exam_ids = request.GET.getlist('exam_ids')
    source = request.GET.get('source', 'zipgrade')
    
    if not student_id or not exam_ids:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    exam_ids = [int(x) for x in exam_ids]
    data = AdvancedAnalyticsHelper.get_student_radar_data(
        int(student_id), exam_ids, source=source
    )
    
    return JsonResponse({'data': data})


@login_required
@teacher_or_admin_required
def api_trend_data(request):
    """API endpoint for trend line data."""
    from .advanced_analytics import AdvancedAnalyticsHelper
    from django.http import JsonResponse
    
    student_id = request.GET.get('student_id')
    exam_ids = request.GET.getlist('exam_ids') or None
    source = request.GET.get('source', 'zipgrade')
    
    if not student_id:
        return JsonResponse({'error': 'Missing student_id'}, status=400)
    
    if exam_ids:
        exam_ids = [int(x) for x in exam_ids]
    
    data = AdvancedAnalyticsHelper.get_progressive_trend(
        int(student_id), exam_ids, source=source
    )
    
    return JsonResponse(data)


@login_required
@teacher_or_admin_required
def api_distribution_data(request):
    """API endpoint for grade distribution data."""
    from .advanced_analytics import AdvancedAnalyticsHelper
    from django.http import JsonResponse
    
    exam_ids = request.GET.getlist('exam_ids')
    source = request.GET.get('source', 'zipgrade')
    
    if not exam_ids:
        return JsonResponse({'error': 'Missing exam_ids'}, status=400)
    
    exam_ids = [int(x) for x in exam_ids]
    data = AdvancedAnalyticsHelper.get_grade_distribution(exam_ids, source=source)
    
    return JsonResponse(data)


@login_required
@teacher_or_admin_required
def api_heatmap_data(request):
    """API endpoint for heatmap data."""
    from .advanced_analytics import AdvancedAnalyticsHelper
    from django.http import JsonResponse
    
    exam_ids = request.GET.getlist('exam_ids')
    grade = request.GET.get('grade')
    section = request.GET.get('section')
    source = request.GET.get('source', 'zipgrade')
    
    if not exam_ids:
        return JsonResponse({'error': 'Missing exam_ids'}, status=400)
    
    exam_ids = [int(x) for x in exam_ids]
    school = request.user.primary_school
    
    data = AdvancedAnalyticsHelper.get_topic_mastery_heatmap(
        exam_ids, school=school, grade=grade, section=section
    )
    
    return JsonResponse(data)
