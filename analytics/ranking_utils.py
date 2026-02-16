"""
Ranking calculation utilities for AIMS Analytics.

Provides multi-dimensional ranking algorithms:
- Absolute Top: Highest scores in exam/subject
- Progress Top: Most improved students/classes compared to previous exams  
- Consistency Top: Students maintaining high results for 3+ consecutive exams

Also includes:
- Fair ranking algorithm for schools of different sizes
- Tie-breaking logic
"""

import json
from decimal import Decimal
from django.db.models import Avg, Count, StdDev, F, Q, Max, Min
from django.db.models.functions import Coalesce

from zipgrade.models import ZipGradeExam, ExamResult, SubjectResult, SubjectSplit
from schools.models import MasterStudent, School, Subject


class RankingCalculator:
    """Calculate various ranking types for students, classes, and schools."""
    
    # Thresholds
    CONSISTENCY_THRESHOLD = 80.0  # Minimum percentage for "consistent" performance
    MIN_STREAK_LENGTH = 3  # Minimum exams for consistency ranking
    
    @classmethod
    def calculate_absolute_top(cls, exam_ids, entity_type='student', subject_id=None, limit=20):
        """
        Calculate absolute top rankings - entities with highest scores.
        
        Args:
            exam_ids: List of exam IDs to consider
            entity_type: 'student', 'class', or 'school'
            subject_id: Optional - filter by specific subject
            limit: Max results to return
            
        Returns:
            List of dicts with ranking info including position, name, score, etc.
        """
        if not exam_ids:
            return []
            
        if entity_type == 'student':
            return cls._absolute_top_students(exam_ids, subject_id, limit)
        elif entity_type == 'class':
            return cls._absolute_top_classes(exam_ids, subject_id, limit)
        elif entity_type == 'school':
            return cls._absolute_top_schools(exam_ids, subject_id, limit)
        return []
    
    @classmethod
    def _absolute_top_students(cls, exam_ids, subject_id, limit):
        """Top students by average score."""
        if subject_id:
            # Filter by subject using SubjectResult
            results = SubjectResult.objects.filter(
                result__exam_id__in=exam_ids,
                subject_split__subject_id=subject_id,
                result__student__isnull=False
            ).values(
                'result__student__id',
                'result__student__name',
                'result__student__surname',
                'result__student__grade',
                'result__student__section',
                'result__student__school__name'
            ).annotate(
                avg_score=Avg('percentage'),
                exam_count=Count('result__exam', distinct=True),
                best_score=Max('percentage'),
                worst_score=Min('percentage')
            ).order_by('-avg_score')[:limit]
        else:
            # Use overall exam results
            results = ExamResult.objects.filter(
                exam_id__in=exam_ids,
                student__isnull=False
            ).values(
                'student__id',
                'student__name',
                'student__surname',
                'student__grade',
                'student__section',
                'student__school__name'
            ).annotate(
                avg_score=Avg('percentage'),
                exam_count=Count('exam', distinct=True),
                best_score=Max('percentage'),
                worst_score=Min('percentage')
            ).order_by('-avg_score')[:limit]
        
        # Format results
        ranking = []
        for i, r in enumerate(results, 1):
            if subject_id:
                student_name = f"{r['result__student__surname']} {r['result__student__name']}"
                grade = r['result__student__grade']
                section = r['result__student__section']
                school = r['result__student__school__name']
                student_id = r['result__student__id']
            else:
                student_name = f"{r['student__surname']} {r['student__name']}"
                grade = r['student__grade']
                section = r['student__section']
                school = r['student__school__name']
                student_id = r['student__id']
            
            ranking.append({
                'position': i,
                'entity_id': student_id,
                'name': student_name.strip(),
                'grade': grade,
                'section': section,
                'school': school,
                'class_name': f"{grade}{section}" if grade and section else grade or '-',
                'avg_score': round(float(r['avg_score']), 1),
                'exam_count': r['exam_count'],
                'best_score': round(float(r['best_score'] or 0), 1),
                'worst_score': round(float(r['worst_score'] or 0), 1),
                'trend': 'stable',  # Will be calculated separately if needed
            })
        
        return ranking
    
    @classmethod
    def _absolute_top_classes(cls, exam_ids, subject_id, limit):
        """Top classes by average score."""
        if subject_id:
            results = SubjectResult.objects.filter(
                result__exam_id__in=exam_ids,
                subject_split__subject_id=subject_id,
                result__student__isnull=False
            ).values(
                'result__student__grade',
                'result__student__section',
                'result__student__school__name',
                'result__student__school__id'
            ).annotate(
                avg_score=Avg('percentage'),
                student_count=Count('result__student', distinct=True)
            ).order_by('-avg_score')[:limit]
        else:
            results = ExamResult.objects.filter(
                exam_id__in=exam_ids,
                student__isnull=False
            ).values(
                'student__grade',
                'student__section',
                'student__school__name',
                'student__school__id'
            ).annotate(
                avg_score=Avg('percentage'),
                student_count=Count('student', distinct=True)
            ).order_by('-avg_score')[:limit]
        
        ranking = []
        for i, r in enumerate(results, 1):
            if subject_id:
                grade = r['result__student__grade']
                section = r['result__student__section']
                school = r['result__student__school__name']
            else:
                grade = r['student__grade']
                section = r['student__section']
                school = r['student__school__name']
            
            ranking.append({
                'position': i,
                'name': f"{grade}{section}" if section else grade,
                'school': school,
                'avg_score': round(float(r['avg_score']), 1),
                'student_count': r['student_count'],
                'trend': 'stable',
            })
        
        return ranking
    
    @classmethod
    def _absolute_top_schools(cls, exam_ids, subject_id, limit):
        """Top schools by weighted average score."""
        if subject_id:
            results = SubjectResult.objects.filter(
                result__exam_id__in=exam_ids,
                subject_split__subject_id=subject_id,
                result__student__isnull=False
            ).values(
                'result__student__school__id',
                'result__student__school__name'
            ).annotate(
                avg_score=Avg('percentage'),
                student_count=Count('result__student', distinct=True),
                score_stddev=StdDev('percentage')
            ).order_by('-avg_score')[:limit]
        else:
            results = ExamResult.objects.filter(
                exam_id__in=exam_ids,
                student__isnull=False
            ).values(
                'student__school__id',
                'student__school__name'
            ).annotate(
                avg_score=Avg('percentage'),
                student_count=Count('student', distinct=True),
                score_stddev=StdDev('percentage')
            ).order_by('-avg_score')[:limit]
        
        ranking = []
        for i, r in enumerate(results, 1):
            # Calculate weighted score that accounts for school size
            weighted = cls._calculate_weighted_school_score(
                r['avg_score'], 
                r['student_count'],
                r['score_stddev'] or 0
            )
            
            if subject_id:
                school_name = r['result__student__school__name']
                school_id = r['result__student__school__id']
            else:
                school_name = r['student__school__name']
                school_id = r['student__school__id']
            
            ranking.append({
                'position': i,
                'entity_id': school_id,
                'name': school_name,
                'avg_score': round(float(r['avg_score']), 1),
                'weighted_score': round(weighted, 1),
                'student_count': r['student_count'],
                'std_dev': round(float(r['score_stddev'] or 0), 2),
                'trend': 'stable',
            })
        
        # Re-sort by weighted score
        ranking.sort(key=lambda x: x['weighted_score'], reverse=True)
        for i, r in enumerate(ranking, 1):
            r['position'] = i
        
        return ranking[:limit]
    
    @classmethod
    def calculate_progress_top(cls, exam_ids, entity_type='student', limit=20):
        """
        Calculate progress rankings - most improved entities.
        
        Compares performance in recent exams vs earlier exams.
        Requires at least 2 exams in exam_ids.
        
        Returns:
            List with improvement percentage, from/to scores
        """
        if len(exam_ids) < 2:
            return []
        
        exams = ZipGradeExam.objects.filter(id__in=exam_ids).order_by('exam_date')
        exam_dates = {e.id: e.exam_date for e in exams}
        
        # Split into earlier and later halves
        sorted_ids = sorted(exam_ids, key=lambda x: exam_dates.get(x) or 0)
        mid = len(sorted_ids) // 2
        earlier_ids = sorted_ids[:mid] if mid > 0 else sorted_ids[:1]
        later_ids = sorted_ids[mid:] if mid > 0 else sorted_ids[1:]
        
        if entity_type == 'student':
            return cls._progress_top_students(earlier_ids, later_ids, limit)
        elif entity_type == 'class':
            return cls._progress_top_classes(earlier_ids, later_ids, limit) 
        return []
    
    @classmethod
    def _progress_top_students(cls, earlier_ids, later_ids, limit):
        """Calculate student progress rankings."""
        # Get earlier averages
        earlier = ExamResult.objects.filter(
            exam_id__in=earlier_ids,
            student__isnull=False
        ).values('student__id').annotate(avg=Avg('percentage'))
        earlier_map = {r['student__id']: float(r['avg']) for r in earlier}
        
        # Get later averages
        later = ExamResult.objects.filter(
            exam_id__in=later_ids,
            student__isnull=False
        ).values(
            'student__id',
            'student__name',
            'student__surname',
            'student__grade',
            'student__section',
            'student__school__name'
        ).annotate(avg=Avg('percentage'))
        
        progress = []
        for r in later:
            student_id = r['student__id']
            if student_id in earlier_map:
                earlier_score = earlier_map[student_id]
                later_score = float(r['avg'])
                improvement = later_score - earlier_score
                
                if improvement > 0:  # Only include those who improved
                    progress.append({
                        'entity_id': student_id,
                        'name': f"{r['student__surname']} {r['student__name']}".strip(),
                        'grade': r['student__grade'],
                        'section': r['student__section'],
                        'school': r['student__school__name'],
                        'class_name': f"{r['student__grade']}{r['student__section']}",
                        'earlier_score': round(earlier_score, 1),
                        'later_score': round(later_score, 1),
                        'improvement': round(improvement, 1),
                        'improvement_pct': round(improvement / earlier_score * 100, 1) if earlier_score > 0 else 0,
                        'trend': 'up',
                    })
        
        # Sort by improvement
        progress.sort(key=lambda x: x['improvement'], reverse=True)
        
        # Add positions
        for i, p in enumerate(progress[:limit], 1):
            p['position'] = i
        
        return progress[:limit]
    
    @classmethod
    def _progress_top_classes(cls, earlier_ids, later_ids, limit):
        """Calculate class progress rankings."""
        earlier = ExamResult.objects.filter(
            exam_id__in=earlier_ids,
            student__isnull=False
        ).values('student__grade', 'student__section', 'student__school__id').annotate(avg=Avg('percentage'))
        
        earlier_map = {}
        for r in earlier:
            key = (r['student__grade'], r['student__section'], r['student__school__id'])
            earlier_map[key] = float(r['avg'])
        
        later = ExamResult.objects.filter(
            exam_id__in=later_ids,
            student__isnull=False
        ).values(
            'student__grade', 
            'student__section', 
            'student__school__id',
            'student__school__name'
        ).annotate(avg=Avg('percentage'))
        
        progress = []
        for r in later:
            key = (r['student__grade'], r['student__section'], r['student__school__id'])
            if key in earlier_map:
                earlier_score = earlier_map[key]
                later_score = float(r['avg'])
                improvement = later_score - earlier_score
                
                if improvement > 0:
                    progress.append({
                        'name': f"{r['student__grade']}{r['student__section']}",
                        'school': r['student__school__name'],
                        'earlier_score': round(earlier_score, 1),
                        'later_score': round(later_score, 1),
                        'improvement': round(improvement, 1),
                        'trend': 'up',
                    })
        
        progress.sort(key=lambda x: x['improvement'], reverse=True)
        for i, p in enumerate(progress[:limit], 1):
            p['position'] = i
        
        return progress[:limit]
    
    @classmethod
    def calculate_consistency_top(cls, exam_ids, threshold=None, min_streak=None, limit=20):
        """
        Calculate consistency rankings - students with consistent high performance.
        
        Args:
            exam_ids: List of exam IDs (in chronological order ideally)
            threshold: Minimum percentage to count as "high" (default 80)
            min_streak: Minimum consecutive exams (default 3)
            limit: Max results
            
        Returns:
            List of students with current streak length and average
        """
        threshold = threshold or cls.CONSISTENCY_THRESHOLD
        min_streak = min_streak or cls.MIN_STREAK_LENGTH
        
        if len(exam_ids) < min_streak:
            return []
        
        exams = ZipGradeExam.objects.filter(id__in=exam_ids).order_by('exam_date')
        ordered_exam_ids = list(exams.values_list('id', flat=True))
        
        # Get all results for matched students
        results = ExamResult.objects.filter(
            exam_id__in=exam_ids,
            student__isnull=False
        ).select_related('student', 'exam').order_by('student_id', 'exam__exam_date')
        
        # Group by student
        student_results = {}
        for r in results:
            if r.student_id not in student_results:
                student_results[r.student_id] = {
                    'student': r.student,
                    'scores': []
                }
            student_results[r.student_id]['scores'].append({
                'exam_id': r.exam_id,
                'percentage': float(r.percentage)
            })
        
        # Calculate streaks
        consistency_rankings = []
        for student_id, data in student_results.items():
            student = data['student']
            scores = data['scores']
            
            # Sort by exam order
            exam_order = {eid: i for i, eid in enumerate(ordered_exam_ids)}
            scores.sort(key=lambda x: exam_order.get(x['exam_id'], 999))
            
            # Calculate current streak (from most recent backwards)
            current_streak = 0
            streak_scores = []
            for score in reversed(scores):
                if score['percentage'] >= threshold:
                    current_streak += 1
                    streak_scores.append(score['percentage'])
                else:
                    break
            
            if current_streak >= min_streak:
                avg_streak = sum(streak_scores) / len(streak_scores) if streak_scores else 0
                consistency_rankings.append({
                    'entity_id': student_id,
                    'name': student.full_name,
                    'grade': student.grade,
                    'section': student.section,
                    'school': student.school.name if student.school else '-',
                    'class_name': student.class_name,
                    'current_streak': current_streak,
                    'avg_streak_score': round(avg_streak, 1),
                    'exams_taken': len(scores),
                    'trend': 'stable',
                })
        
        # Sort by streak length, then by average
        consistency_rankings.sort(key=lambda x: (x['current_streak'], x['avg_streak_score']), reverse=True)
        
        for i, r in enumerate(consistency_rankings[:limit], 1):
            r['position'] = i
        
        return consistency_rankings[:limit]
    
    @classmethod
    def _calculate_weighted_school_score(cls, avg_score, student_count, std_dev):
        """
        Calculate weighted score for fair school comparison.
        
        Formula: weighted = avg * (1 + log10(n) * k) / (1 + std_dev / 20)
        
        - Larger schools get slight bonus (log scale to prevent dominance)
        - Higher std deviation penalizes (suggests inconsistent teaching)
        - k = 0.05 scaling factor
        """
        import math
        
        avg = float(avg_score)
        n = max(1, student_count)
        std = float(std_dev)
        k = 0.05  # Scaling factor
        
        # Size bonus (logarithmic)
        size_factor = 1 + math.log10(n) * k
        
        # Consistency penalty
        consistency_factor = 1 + std / 20
        
        weighted = avg * size_factor / consistency_factor
        return weighted
    
    @classmethod
    def handle_ties(cls, rankings, tie_break_fields=None):
        """
        Handle ties in rankings by applying tie-breaking rules.
        
        Priority:
        1. Best score in most recent exam
        2. Lower standard deviation (more consistent)
        3. More exams taken
        
        Args:
            rankings: List of ranking dicts (must have 'avg_score')
            tie_break_fields: Optional list of fields for tie-breaking
            
        Returns:
            Updated rankings with ties resolved
        """
        if not rankings:
            return rankings
        
        # Group by score
        from collections import defaultdict
        score_groups = defaultdict(list)
        for r in rankings:
            score_key = round(r.get('avg_score', 0), 1)
            score_groups[score_key].append(r)
        
        # Sort within tied groups
        result = []
        for score in sorted(score_groups.keys(), reverse=True):
            group = score_groups[score]
            if len(group) > 1:
                # Apply tie-breaking
                group.sort(key=lambda x: (
                    -x.get('best_score', 0),  # Higher best score first
                    x.get('std_dev', 100),    # Lower std dev first  
                    -x.get('exam_count', 0)   # More exams first
                ))
            result.extend(group)
        
        # Re-assign positions
        for i, r in enumerate(result, 1):
            r['position'] = i
        
        return result
    
    @classmethod
    def get_award_eligibility(cls, exam_ids, entity_type='student'):
        """
        Determine award eligibility based on rankings.
        
        Gold: Top 5%
        Silver: Top 10%
        Bronze: Top 20%
        """
        absolute = cls.calculate_absolute_top(exam_ids, entity_type, limit=1000)
        
        if not absolute:
            return {'gold': [], 'silver': [], 'bronze': []}
        
        total = len(absolute)
        gold_cutoff = max(1, int(total * 0.05))
        silver_cutoff = max(1, int(total * 0.10))
        bronze_cutoff = max(1, int(total * 0.20))
        
        return {
            'gold': absolute[:gold_cutoff],
            'silver': absolute[gold_cutoff:silver_cutoff],
            'bronze': absolute[silver_cutoff:bronze_cutoff],
        }
