from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse

from accounts.decorators import super_admin_required, teacher_or_admin_required
from .models import School, Subject, MasterStudent
from .forms import SchoolForm, SubjectForm, MasterStudentUploadForm, MasterStudentForm
from .utils import parse_master_student_excel


# ============ School Views ============

@login_required
@super_admin_required
def school_list_view(request):
    """List all schools."""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    schools = School.objects.annotate(
        student_count=Count('master_students'),
        teacher_count=Count('users', filter=Q(users__role='teacher'))
    ).order_by('name')
    
    if search:
        schools = schools.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )
    
    if status == 'active':
        schools = schools.filter(is_active=True)
    elif status == 'inactive':
        schools = schools.filter(is_active=False)
    
    paginator = Paginator(schools, 20)
    page = request.GET.get('page', 1)
    schools = paginator.get_page(page)
    
    return render(request, 'schools/school_list.html', {
        'schools': schools,
        'search': search,
        'status': status,
    })


@login_required
@super_admin_required
def school_create_view(request):
    """Create a new school."""
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.save()
            messages.success(request, _('School "%(name)s" created successfully.') % {'name': school.name})
            return redirect('schools:list')
    else:
        form = SchoolForm()
    
    return render(request, 'schools/school_form.html', {
        'form': form,
        'title': _('Add School'),
        'submit_text': _('Create School'),
    })


@login_required
@super_admin_required
def school_edit_view(request, pk):
    """Edit an existing school."""
    school = get_object_or_404(School, pk=pk)
    
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, _('School updated successfully.'))
            return redirect('schools:list')
    else:
        form = SchoolForm(instance=school)
    
    return render(request, 'schools/school_form.html', {
        'form': form,
        'title': _('Edit School'),
        'submit_text': _('Save Changes'),
        'school': school,
    })


@login_required
@super_admin_required
def school_delete_view(request, pk):
    """Delete a school (soft delete)."""
    school = get_object_or_404(School, pk=pk)
    
    if request.method == 'POST':
        school.is_active = False
        school.save()
        messages.success(request, _('School "%(name)s" has been deactivated.') % {'name': school.name})
        return redirect('schools:list')
    
    return render(request, 'schools/school_confirm_delete.html', {'school': school})


@login_required
@super_admin_required
def school_detail_view(request, pk):
    """View school details with students."""
    school = get_object_or_404(School, pk=pk)
    
    # Get students with filtering
    search = request.GET.get('search', '')
    grade_filter = request.GET.get('grade', '')
    
    students = school.master_students.all().order_by('grade', 'section', 'surname', 'name')
    
    if search:
        students = students.filter(
            Q(student_id__icontains=search) |
            Q(name__icontains=search) |
            Q(surname__icontains=search)
        )
    
    if grade_filter:
        students = students.filter(grade=grade_filter)
    
    # Get unique grades for filter dropdown
    grades = school.master_students.values_list('grade', flat=True).distinct().order_by('grade')
    
    paginator = Paginator(students, 50)
    page = request.GET.get('page', 1)
    students = paginator.get_page(page)
    
    return render(request, 'schools/school_detail.html', {
        'school': school,
        'students': students,
        'search': search,
        'grade_filter': grade_filter,
        'grades': grades,
    })


# ============ Subject Views ============

@login_required
@super_admin_required
def subject_list_view(request):
    """List all subjects."""
    search = request.GET.get('search', '')
    school_filter = request.GET.get('school', '')
    
    subjects = Subject.objects.filter(is_active=True).select_related('school').order_by('name')
    
    if search:
        subjects = subjects.filter(name__icontains=search)
    
    if school_filter:
        subjects = subjects.filter(school_id=school_filter)
    
    schools = School.objects.filter(is_active=True)
    
    paginator = Paginator(subjects, 20)
    page = request.GET.get('page', 1)
    subjects = paginator.get_page(page)
    
    # Convert school_filter to int for template comparison
    school_filter_int = int(school_filter) if school_filter else None
    
    return render(request, 'schools/subject_list.html', {
        'subjects': subjects,
        'search': search,
        'school_filter': school_filter,
        'school_filter_int': school_filter_int,
        'schools': schools,
    })


@login_required
@super_admin_required
def subject_create_view(request):
    """Create a new subject."""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, _('Subject "%(name)s" created successfully.') % {'name': subject.name})
            return redirect('schools:subjects')
    else:
        form = SubjectForm()
    
    return render(request, 'schools/subject_form.html', {
        'form': form,
        'title': _('Add Subject'),
        'submit_text': _('Create Subject'),
    })


@login_required
@super_admin_required
def subject_edit_view(request, pk):
    """Edit an existing subject."""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, _('Subject updated successfully.'))
            return redirect('schools:subjects')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'schools/subject_form.html', {
        'form': form,
        'title': _('Edit Subject'),
        'submit_text': _('Save Changes'),
        'subject': subject,
    })


@login_required
@super_admin_required
def subject_delete_view(request, pk):
    """Delete a subject (soft delete)."""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        subject.is_active = False
        subject.save()
        messages.success(request, _('Subject "%(name)s" has been deleted.') % {'name': subject.name})
        return redirect('schools:subjects')
    
    return render(request, 'schools/subject_confirm_delete.html', {'subject': subject})


# ============ Master Student Views ============

@login_required
@super_admin_required
def master_student_list_view(request):
    """List all master students."""
    students = MasterStudent.objects.all().select_related('school')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        from django.db.models import Q
        students = students.filter(
            Q(name__icontains=search) |
            Q(surname__icontains=search) |
            Q(student_id__icontains=search)
        )
    
    # Filter by school
    school_filter = request.GET.get('school', '')
    if school_filter:
        students = students.filter(school_id=school_filter)
    
    # Filter by grade
    grade_filter = request.GET.get('grade', '')
    if grade_filter:
        students = students.filter(grade=grade_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(students, 50)
    page = request.GET.get('page', 1)
    students = paginator.get_page(page)
    
    # Get unique grades for filter
    grades = MasterStudent.objects.values_list('grade', flat=True).distinct().order_by('grade')
    
    context = {
        'students': students,
        'search': search,
        'school_filter': int(school_filter) if school_filter else '',
        'grade_filter': grade_filter,
        'schools': School.objects.filter(is_active=True),
        'grades': grades,
    }
    
    return render(request, 'schools/master_student_list.html', context)


@login_required
@super_admin_required
def master_student_upload_view(request):
    """Upload Master Student List from Excel file."""
    if request.method == 'POST':
        form = MasterStudentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.cleaned_data['school']
            file = form.cleaned_data['file']
            replace_existing = form.cleaned_data['replace_existing']
            
            try:
                # Parse Excel file
                students_data = parse_master_student_excel(file)
                
                if not students_data:
                    messages.error(request, _('No valid student data found in the file.'))
                    return redirect('schools:master_student_upload')
                
                # Delete existing if requested
                if replace_existing:
                    MasterStudent.objects.filter(school=school).delete()
                
                # Create students
                created_count = 0
                updated_count = 0
                
                for data in students_data:
                    obj, created = MasterStudent.objects.update_or_create(
                        school=school,
                        student_id=data['student_id'],
                        defaults={
                            'name': data['name'],
                            'surname': data['surname'],
                            'grade': data['grade'],
                            'section': data['section'],
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                messages.success(
                    request,
                    _('Import complete: %(created)d students created, %(updated)d updated.') % {
                        'created': created_count,
                        'updated': updated_count,
                    }
                )
                return redirect('schools:detail', pk=school.pk)
                
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, _('Error processing file: %(error)s') % {'error': str(e)})
    else:
        form = MasterStudentUploadForm()
    
    return render(request, 'schools/master_student_upload.html', {
        'form': form,
    })


@login_required
@super_admin_required
def master_student_add_view(request, school_pk):
    """Manually add a student to a school."""
    school = get_object_or_404(School, pk=school_pk)
    
    if request.method == 'POST':
        form = MasterStudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.school = school
            student.save()
            messages.success(request, _('Student added successfully.'))
            return redirect('schools:detail', pk=school.pk)
    else:
        form = MasterStudentForm()
    
    return render(request, 'schools/master_student_form.html', {
        'form': form,
        'school': school,
        'title': _('Add Student'),
        'submit_text': _('Add Student'),
    })


@login_required
@super_admin_required
def master_student_edit_view(request, pk):
    """Edit a student."""
    student = get_object_or_404(MasterStudent, pk=pk)
    
    if request.method == 'POST':
        form = MasterStudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, _('Student updated successfully.'))
            return redirect('schools:detail', pk=student.school.pk)
    else:
        form = MasterStudentForm(instance=student)
    
    return render(request, 'schools/master_student_form.html', {
        'form': form,
        'school': student.school,
        'student': student,
        'title': _('Edit Student'),
        'submit_text': _('Save Changes'),
    })


@login_required
@super_admin_required
def master_student_delete_view(request, pk):
    """Delete a student."""
    student = get_object_or_404(MasterStudent, pk=pk)
    school_pk = student.school.pk
    
    if request.method == 'POST':
        student.delete()
        messages.success(request, _('Student deleted.'))
        return redirect('schools:detail', pk=school_pk)
    
    return render(request, 'schools/master_student_confirm_delete.html', {
        'student': student,
    })
