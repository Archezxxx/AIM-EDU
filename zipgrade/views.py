import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse

from accounts.decorators import teacher_or_admin_required, super_admin_required
from schools.models import MasterStudent
from schools.utils import normalize_student_id
from .models import ZipGradeExam, SubjectSplit, ExamResult, SubjectResult
from .forms import ZipGradeUploadForm, SubjectSplitForm
from .utils import ZipGradeParser


@login_required
@teacher_or_admin_required
def upload_view(request):
    """ZipGrade file upload view."""
    if request.method == 'POST':
        form = ZipGradeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.cleaned_data['school']
            title = form.cleaned_data['title']
            exam_date = form.cleaned_data['exam_date']
            file = form.cleaned_data['file']
            
            # Parse the file
            file_content = file.read()
            parser = ZipGradeParser(file_content, filename=file.name)
            parse_result = parser.parse()
            
            if parse_result['errors'] and not parse_result['results']:
                messages.error(request, _('Failed to parse file: %(errors)s') % {
                    'errors': ', '.join(parse_result['errors'][:3])
                })
                return render(request, 'zipgrade/upload.html', {'form': form})
            
            if not parse_result['results']:
                messages.error(request, _('No student data found in the file.'))
                return render(request, 'zipgrade/upload.html', {'form': form})
            
            # Store in session for preview
            request.session['zipgrade_preview'] = {
                'school_id': school.id,
                'title': title,
                'exam_date': str(exam_date),
                'filename': file.name,
                'parse_result': parse_result,
            }
            
            return redirect('zipgrade:preview')
    else:
        form = ZipGradeUploadForm()
    
    return render(request, 'zipgrade/upload.html', {'form': form})


@login_required
@teacher_or_admin_required
def preview_view(request):
    """Preview parsed ZipGrade data before saving."""
    preview_data = request.session.get('zipgrade_preview')
    
    if not preview_data:
        messages.warning(request, _('No upload data found. Please upload a file first.'))
        return redirect('zipgrade:upload')
    
    from schools.models import School, Subject
    school = get_object_or_404(School, pk=preview_data['school_id'])
    parse_result = preview_data['parse_result']
    
    # Match students to master list
    matched_results = []
    unknown_count = 0
    
    for result in parse_result['results']:
        normalized_id = result['student_id_normalized']
        
        # Try to find student in master list
        master_student = MasterStudent.objects.filter(
            school=school,
            student_id_normalized=normalized_id
        ).first()
        
        result['matched_student'] = master_student
        result['is_unknown'] = master_student is None
        
        if master_student is None:
            unknown_count += 1
        
        matched_results.append(result)
    
    # Get subjects for subject split dropdown
    subjects = Subject.objects.filter(is_active=True).values('id', 'name')
    subjects_json = json.dumps(list(subjects))
    
    context = {
        'school': school,
        'title': preview_data['title'],
        'exam_date': preview_data['exam_date'],
        'filename': preview_data['filename'],
        'results': matched_results[:50],  # Show first 50 for preview
        'total_students': len(matched_results),
        'total_questions': parse_result['total_questions'],
        'unknown_count': unknown_count,
        'has_more': len(matched_results) > 50,
        'subjects_json': subjects_json,
    }
    
    return render(request, 'zipgrade/preview.html', context)


@login_required
@teacher_or_admin_required
def confirm_upload_view(request):
    """Confirm and save the ZipGrade data."""
    if request.method != 'POST':
        return redirect('zipgrade:preview')
    
    preview_data = request.session.get('zipgrade_preview')
    if not preview_data:
        messages.warning(request, _('No upload data found. Please upload a file first.'))
        return redirect('zipgrade:upload')
    
    from schools.models import School, Subject
    school = get_object_or_404(School, pk=preview_data['school_id'])
    parse_result = preview_data['parse_result']
    
    # Parse subject splits from POST data
    split_count = int(request.POST.get('split_count', 0))
    subject_splits_data = []
    for i in range(split_count):
        subject_id = request.POST.get(f'split_subject_{i}')
        start_q = request.POST.get(f'split_start_{i}')
        end_q = request.POST.get(f'split_end_{i}')
        if subject_id and start_q and end_q:
            subject_splits_data.append({
                'subject_id': int(subject_id),
                'start_question': int(start_q),
                'end_question': int(end_q),
            })
    
    try:
        with transaction.atomic():
            # Create the exam
            exam = ZipGradeExam.objects.create(
                school=school,
                uploaded_by=request.user,
                title=preview_data['title'],
                original_filename=preview_data['filename'],
                exam_date=preview_data['exam_date'],
                total_questions=parse_result['total_questions'],
                total_students=len(parse_result['results']),
            )
            
            # Create subject splits
            subject_splits = []
            for split_data in subject_splits_data:
                subject = get_object_or_404(Subject, pk=split_data['subject_id'])
                split = SubjectSplit.objects.create(
                    exam=exam,
                    subject=subject,
                    start_question=split_data['start_question'],
                    end_question=split_data['end_question'],
                )
                subject_splits.append(split)
            
            unknown_count = 0
            
            # Create results
            for result_data in parse_result['results']:
                normalized_id = result_data['student_id_normalized']
                
                # Find matched student
                master_student = MasterStudent.objects.filter(
                    school=school,
                    student_id_normalized=normalized_id
                ).first()
                
                is_unknown = master_student is None
                if is_unknown:
                    unknown_count += 1
                
                # Use update_or_create to handle duplicates in the uploaded file
                exam_result, created = ExamResult.objects.update_or_create(
                    exam=exam,
                    zipgrade_student_id=result_data['student_id'],
                    defaults={
                        'student': master_student,
                        'zipgrade_first_name': result_data['first_name'],
                        'zipgrade_last_name': result_data['last_name'],
                        'earned_points': result_data['earned'],
                        'max_points': result_data['max_points'],
                        'percentage': result_data['percentage'],
                        'answers': json.dumps(result_data['answers']),
                        'is_unknown': is_unknown,
                    }
                )
                
                # Calculate subject results if splits defined
                if subject_splits:
                    answers = result_data['answers']
                    for split in subject_splits:
                        # Extract answers for this subject's question range
                        start_idx = split.start_question - 1  # 0-indexed
                        end_idx = split.end_question  # end is exclusive in slice
                        subject_answers = answers[start_idx:end_idx] if len(answers) >= end_idx else []
                        
                        # Calculate score (1 point per correct answer)
                        correct_count = sum(1 for a in subject_answers if a.get('correct', False))
                        max_points = split.question_count
                        earned_points = correct_count
                        percentage = (earned_points / max_points * 100) if max_points > 0 else 0
                        
                        SubjectResult.objects.update_or_create(
                            result=exam_result,
                            subject_split=split,
                            defaults={
                                'earned_points': earned_points,
                                'max_points': max_points,
                                'percentage': round(percentage, 2),
                                'question_results': json.dumps(subject_answers),
                            }
                        )
            
            # Update unknown count
            exam.unknown_students = unknown_count
            exam.save()
        
        # Clear session data
        del request.session['zipgrade_preview']
        
        messages.success(request, _('Successfully imported %(count)s student results.') % {
            'count': len(parse_result['results'])
        })
        
        return redirect('zipgrade:exam_detail', pk=exam.pk)
        
    except Exception as e:
        messages.error(request, _('Error saving data: %(error)s') % {'error': str(e)})
        return redirect('zipgrade:preview')


@login_required
@teacher_or_admin_required
def cancel_upload_view(request):
    """Cancel the upload and clear session data."""
    if 'zipgrade_preview' in request.session:
        del request.session['zipgrade_preview']
    return redirect('zipgrade:upload')


from django.db.models import Q

@login_required
@teacher_or_admin_required
def results_view(request):
    """List all ZipGrade exams."""
    exams = ZipGradeExam.objects.all().select_related('school', 'uploaded_by')
    
    # Filter by school for non-super-admins
    if request.user.role != 'super_admin' and request.user.primary_school:
        exams = exams.filter(school=request.user.primary_school)
    
    # Date Filtering
    date_from = request.GET.get('date_from')
    if date_from:
        exams = exams.filter(exam_date__gte=date_from)
        
    date_to = request.GET.get('date_to')
    if date_to:
        exams = exams.filter(exam_date__lte=date_to)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        exams = exams.filter(
            Q(title__icontains=search) |
            Q(original_filename__icontains=search) |
            Q(uploaded_by__first_name__icontains=search) |
            Q(uploaded_by__last_name__icontains=search)
        )
    
    # School filter
    school_filter = request.GET.get('school')
    if school_filter:
        exams = exams.filter(school_id=school_filter)
    
    # Pagination
    paginator = Paginator(exams, 20)
    page = request.GET.get('page', 1)
    exams = paginator.get_page(page)
    
    from schools.models import School
    context = {
        'exams': exams,
        'search': search,
        'school_filter': school_filter,
        'date_from': date_from,
        'date_to': date_to,
        'schools': School.objects.filter(is_active=True),
    }
    
    return render(request, 'zipgrade/results.html', context)


@login_required
@teacher_or_admin_required
def exam_detail_view(request, pk):
    """View exam details and results."""
    exam = get_object_or_404(ZipGradeExam, pk=pk)
    
    results = exam.results.all()
    
    # Filter
    show_unknown = request.GET.get('unknown')
    if show_unknown == '1':
        results = results.filter(is_unknown=True)
    elif show_unknown == '0':
        results = results.filter(is_unknown=False)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        from django.db.models import Q
        results = results.filter(
            Q(zipgrade_first_name__icontains=search) |
            Q(zipgrade_last_name__icontains=search) |
            Q(zipgrade_student_id__icontains=search) |
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search)
        )
    
    # Sort
    sort = request.GET.get('sort', '-percentage')
    if sort in ['percentage', '-percentage', 'zipgrade_student_id', 'zipgrade_last_name']:
        results = results.order_by(sort)
    
    # Pagination
    paginator = Paginator(results, 50)
    page = request.GET.get('page', 1)
    results = paginator.get_page(page)
    
    context = {
        'exam': exam,
        'results': results,
        'search': search,
        'show_unknown': show_unknown,
        'sort': sort,
        'subject_splits': exam.subject_splits.all(),
    }
    
    return render(request, 'zipgrade/exam_detail.html', context)


@login_required
@teacher_or_admin_required
def add_subject_split_view(request, exam_pk):
    """Add subject split to an exam."""
    exam = get_object_or_404(ZipGradeExam, pk=exam_pk)
    
    if request.method == 'POST':
        form = SubjectSplitForm(request.POST, exam=exam)
        if form.is_valid():
            split = form.save(commit=False)
            split.exam = exam
            split.save()
            
            # Recalculate subject results
            _recalculate_subject_results(exam)
            
            messages.success(request, _('Subject split added successfully.'))
            return redirect('zipgrade:exam_detail', pk=exam.pk)
    else:
        form = SubjectSplitForm(exam=exam)
    
    context = {
        'form': form,
        'exam': exam,
        'title': _('Add Subject Split'),
    }
    
    return render(request, 'zipgrade/subject_split_form.html', context)


@login_required
@teacher_or_admin_required
def edit_subject_split_view(request, pk):
    """Edit a subject split."""
    split = get_object_or_404(SubjectSplit, pk=pk)
    exam = split.exam
    
    if request.method == 'POST':
        form = SubjectSplitForm(request.POST, instance=split, exam=exam)
        if form.is_valid():
            form.save()
            
            # Recalculate subject results
            _recalculate_subject_results(exam)
            
            messages.success(request, _('Subject split updated successfully.'))
            return redirect('zipgrade:exam_detail', pk=exam.pk)
    else:
        form = SubjectSplitForm(instance=split, exam=exam)
    
    context = {
        'form': form,
        'exam': exam,
        'split': split,
        'title': _('Edit Subject Split'),
    }
    
    return render(request, 'zipgrade/subject_split_form.html', context)


@login_required
@teacher_or_admin_required
def delete_subject_split_view(request, pk):
    """Delete a subject split."""
    split = get_object_or_404(SubjectSplit, pk=pk)
    exam = split.exam
    
    if request.method == 'POST':
        # Delete associated subject results
        SubjectResult.objects.filter(subject_split=split).delete()
        split.delete()
        messages.success(request, _('Subject split deleted.'))
        return redirect('zipgrade:exam_detail', pk=exam.pk)
    
    context = {
        'split': split,
        'exam': exam,
    }
    
    return render(request, 'zipgrade/subject_split_confirm_delete.html', context)


def _recalculate_subject_results(exam):
    """Recalculate all subject results for an exam."""
    from .utils import calculate_subject_scores
    
    splits = list(exam.subject_splits.all())
    if not splits:
        return
    
    # Build split data
    split_data = []
    for split in splits:
        split_data.append({
            'split_id': split.pk,
            'subject_id': split.subject_id,
            'start': split.start_question,
            'end': split.end_question,
            'points': float(split.points_per_question),
        })
    
    # We need an answer key - for now, skip calculation if no key available
    # In a real implementation, you'd store the answer key or mark correct answers
    # For now, we'll just create basic subject results based on ranges
    
    for result in exam.results.all():
        try:
            answers = json.loads(result.answers) if result.answers else {}
        except:
            answers = {}
        
        # Delete existing subject results for this result
        SubjectResult.objects.filter(result=result).delete()
        
        # Create new subject results
        for split in splits:
            # Count questions in range that have answers
            start_q = split.start_question
            end_q = split.end_question
            points = float(split.points_per_question)
            
            total_questions = end_q - start_q + 1
            answered_count = 0
            
            for q in range(start_q, end_q + 1):
                if str(q) in answers and answers[str(q)]:
                    answered_count += 1
            
            # For now, use prorated score based on overall percentage
            # This is a simplification - real implementation needs answer key
            earned = (result.percentage / 100) * total_questions * points
            max_pts = total_questions * points
            pct = result.percentage  # Same as overall for now
            
            SubjectResult.objects.create(
                result=result,
                subject_split=split,
                earned_points=earned,
                max_points=max_pts,
                percentage=pct,
                question_results=json.dumps({}),  # Would need answer key
            )


@login_required
@teacher_or_admin_required
def delete_exam_view(request, pk):
    """Delete a ZipGrade exam."""
    exam = get_object_or_404(ZipGradeExam, pk=pk)
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, _('Exam deleted successfully.'))
        return redirect('zipgrade:results')
    
    context = {'exam': exam}
    return render(request, 'zipgrade/exam_confirm_delete.html', context)


@login_required
@teacher_or_admin_required
def edit_unknown_student_view(request, pk):
    """Edit unknown student's manual name or link to existing student."""
    result = get_object_or_404(ExamResult, pk=pk)
    exam = result.exam
    
    if request.method == 'POST':
        manual_first_name = request.POST.get('manual_first_name', '').strip()
        manual_last_name = request.POST.get('manual_last_name', '').strip()
        manual_class_name = request.POST.get('manual_class_name', '').strip()
        link_student_id = request.POST.get('link_student', '').strip()
        
        result.manual_first_name = manual_first_name
        result.manual_last_name = manual_last_name
        result.manual_class_name = manual_class_name
        
        if link_student_id:
            try:
                student = MasterStudent.objects.get(pk=int(link_student_id), school=exam.school)
                result.student = student
                result.is_unknown = False
            except (MasterStudent.DoesNotExist, ValueError):
                pass
        
        result.save()
        
        # Update unknown count if student is now known
        if result.student or result.manual_first_name or result.manual_last_name:
            unknown_count = exam.results.filter(
                is_unknown=True, 
                student__isnull=True, 
                manual_first_name='', 
                manual_last_name=''
            ).count()
            exam.unknown_students = unknown_count
            exam.save()
        
        messages.success(request, _('Student information updated successfully.'))
        return redirect('zipgrade:exam_detail', pk=exam.pk)
    
    # Get available students for linking
    available_students = MasterStudent.objects.filter(school=exam.school).order_by('surname', 'name')
    
    context = {
        'result': result,
        'exam': exam,
        'available_students': available_students,
    }
    
    return render(request, 'zipgrade/edit_unknown_student.html', context)
