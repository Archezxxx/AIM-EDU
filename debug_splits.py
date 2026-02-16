"""Debug script to check subject splits in the database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aims_exam.settings')
django.setup()

from zipgrade.models import ZipGradeExam, SubjectSplit

# Get the latest exam
try:
    exam = ZipGradeExam.objects.latest('id')
    print(f"Latest Exam ID: {exam.id}")
    print(f"Exam Title: {exam.title}")
    print(f"Subject Splits count: {exam.subject_splits.count()}")
    
    splits = list(exam.subject_splits.all())
    if splits:
        for split in splits:
            print(f"  - {split.subject.name}: Q{split.start_question}-Q{split.end_question}")
    else:
        print("  No splits found!")
except Exception as e:
    print(f"Error: {e}")
