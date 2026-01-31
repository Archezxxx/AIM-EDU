"""
Advanced Analytics Helper - Deep-dive visualizations and multi-exam data aggregation.
Provides data generators for:
- Radar Charts (Student Subject Mastery)
- Topic Mastery Heatmaps
- Distractor Analysis
- Progressive Trend Lines
- Competency Gap Charts
- Predictive Insights
- Grade Distribution
"""

import json
from decimal import Decimal
from collections import defaultdict
from django.db.models import Avg, Count, Max, Min, Sum, Q
from django.utils import timezone

from zipgrade.models import ZipGradeExam, ExamResult, SubjectSplit, SubjectResult
from exams.models import OnlineExam, ExamAttempt, ExamQuestion, AttemptAnswer
from schools.models import Subject, MasterStudent


class AdvancedAnalyticsHelper:
    """Advanced analytics calculations for deep-dive visualizations."""
    
    # ========== Multi-Exam Selection & Normalization ==========
    
    @staticmethod
    def normalize_results_to_percentages(exam_ids, source='zipgrade'):
        """
        Normalize all results to percentages for comparison across exams.
        Returns: List of {exam_id, student_id, student_name, percentage, exam_date}
        """
        results = []
        
        if source == 'zipgrade':
            exam_results = ExamResult.objects.filter(
                exam_id__in=exam_ids
            ).select_related('exam', 'student')
            
            for er in exam_results:
                results.append({
                    'exam_id': er.exam_id,
                    'exam_title': er.exam.title,
                    'exam_date': er.exam.exam_date,
                    'student_id': er.student_id,
                    'student_name': er.display_name,
                    'percentage': float(er.percentage),
                    'earned_points': float(er.earned_points),
                    'max_points': float(er.max_points),
                })
        else:
            attempts = ExamAttempt.objects.filter(
                exam_id__in=exam_ids,
                status='completed'
            ).select_related('exam', 'student')
            
            for attempt in attempts:
                results.append({
                    'exam_id': attempt.exam_id,
                    'exam_title': attempt.exam.title,
                    'exam_date': attempt.exam.created_at.date(),
                    'student_id': attempt.student_id,
                    'student_name': attempt.student.get_full_name() if attempt.student else 'Unknown',
                    'percentage': float(attempt.percentage),
                    'earned_points': float(attempt.score),
                    'max_points': float(attempt.exam.total_points or 1),
                })
        
        return results
    
    @staticmethod
    def aggregate_by_tags(exam_ids, student_id=None, source='zipgrade'):
        """
        Aggregate results by Subject/Tags across selected exams.
        Returns: {subject_name: {total_earned, total_max, percentage, count}}
        """
        aggregated = defaultdict(lambda: {'earned': 0, 'max': 0, 'count': 0})
        
        if source == 'zipgrade':
            filters = {'result__exam_id__in': exam_ids}
            if student_id:
                filters['result__student_id'] = student_id
            
            subject_results = SubjectResult.objects.filter(
                **filters
            ).select_related('subject_split__subject')
            
            for sr in subject_results:
                subject_name = sr.subject_split.subject.name
                aggregated[subject_name]['earned'] += float(sr.earned_points)
                aggregated[subject_name]['max'] += float(sr.max_points)
                aggregated[subject_name]['count'] += 1
        
        # Calculate percentages
        for subject, data in aggregated.items():
            if data['max'] > 0:
                data['percentage'] = round((data['earned'] / data['max']) * 100, 1)
            else:
                data['percentage'] = 0
        
        return dict(aggregated)
    
    @staticmethod
    def calculate_weighted_averages(exam_ids, source='zipgrade'):
        """
        Calculate weighted average based on total points per exam.
        Returns: {student_id: weighted_avg_percentage}
        """
        student_scores = defaultdict(lambda: {'total_earned': 0, 'total_max': 0})
        
        if source == 'zipgrade':
            results = ExamResult.objects.filter(exam_id__in=exam_ids)
            
            for r in results:
                student_id = r.student_id or r.zipgrade_student_id
                student_scores[student_id]['total_earned'] += float(r.earned_points)
                student_scores[student_id]['total_max'] += float(r.max_points)
        
        weighted_avgs = {}
        for student_id, data in student_scores.items():
            if data['total_max'] > 0:
                weighted_avgs[student_id] = round(
                    (data['total_earned'] / data['total_max']) * 100, 1
                )
            else:
                weighted_avgs[student_id] = 0
        
        return weighted_avgs
    
    # ========== Radar Chart (Spider Chart) ==========
    
    @staticmethod
    def get_student_radar_data(student_id, exam_ids, source='zipgrade'):
        """
        Generate radar chart data for student subject mastery.
        Returns: [{"subject": "Math", "score": 85, "classAvg": 70}, ...]
        """
        radar_data = []
        
        if source == 'zipgrade':
            # Get student's subject scores
            student_results = SubjectResult.objects.filter(
                result__exam_id__in=exam_ids,
                result__student_id=student_id
            ).select_related('subject_split__subject')
            
            # Aggregate by subject
            student_scores = defaultdict(lambda: {'earned': 0, 'max': 0})
            for sr in student_results:
                subject_name = sr.subject_split.subject.name
                student_scores[subject_name]['earned'] += float(sr.earned_points)
                student_scores[subject_name]['max'] += float(sr.max_points)
            
            # Get class averages for same subjects
            all_results = SubjectResult.objects.filter(
                result__exam_id__in=exam_ids
            ).select_related('subject_split__subject')
            
            class_scores = defaultdict(lambda: {'earned': 0, 'max': 0, 'count': 0})
            for sr in all_results:
                subject_name = sr.subject_split.subject.name
                class_scores[subject_name]['earned'] += float(sr.earned_points)
                class_scores[subject_name]['max'] += float(sr.max_points)
                class_scores[subject_name]['count'] += 1
            
            # Build radar data
            for subject_name in student_scores:
                student_pct = 0
                if student_scores[subject_name]['max'] > 0:
                    student_pct = round(
                        (student_scores[subject_name]['earned'] / 
                         student_scores[subject_name]['max']) * 100, 1
                    )
                
                class_pct = 0
                if class_scores[subject_name]['max'] > 0:
                    class_pct = round(
                        (class_scores[subject_name]['earned'] / 
                         class_scores[subject_name]['max']) * 100, 1
                    )
                
                radar_data.append({
                    'subject': subject_name,
                    'score': student_pct,
                    'classAvg': class_pct
                })
        
        return radar_data
    
    # ========== Topic Mastery Heatmap ==========
    
    @staticmethod
    def get_topic_mastery_heatmap(exam_ids, school=None, grade=None, section=None):
        """
        Generate heatmap data: Students x Topics matrix.
        Returns: {students: [...], topics: [...], values: [[...]]}
        """
        # Get all subject results for selected exams
        filters = {'result__exam_id__in': exam_ids}
        if school:
            filters['result__exam__school'] = school
        
        subject_results = SubjectResult.objects.filter(
            **filters
        ).select_related('result__student', 'subject_split__subject', 'result')
        
        # Filter by grade/section if specified
        if grade or section:
            filtered_results = []
            for sr in subject_results:
                student = sr.result.student
                if student:
                    if grade and str(student.grade) != str(grade):
                        continue
                    if section and student.section != section:
                        continue
                filtered_results.append(sr)
            subject_results = filtered_results
        
        # Build matrix
        students = {}  # student_id -> name
        topics = set()
        matrix = defaultdict(dict)  # student_id -> {topic: percentage}
        
        for sr in subject_results:
            student_id = sr.result.student_id or sr.result.zipgrade_student_id
            student_name = sr.result.display_name
            topic = sr.subject_split.subject.name
            
            students[student_id] = student_name
            topics.add(topic)
            
            if topic not in matrix[student_id]:
                matrix[student_id][topic] = {'earned': 0, 'max': 0}
            
            matrix[student_id][topic]['earned'] += float(sr.earned_points)
            matrix[student_id][topic]['max'] += float(sr.max_points)
        
        # Convert to percentages
        topics_list = sorted(list(topics))
        students_list = list(students.items())
        
        values = []
        for student_id, student_name in students_list:
            row = []
            for topic in topics_list:
                if topic in matrix[student_id]:
                    data = matrix[student_id][topic]
                    if data['max'] > 0:
                        row.append(round((data['earned'] / data['max']) * 100, 1))
                    else:
                        row.append(0)
                else:
                    row.append(None)  # No data
            values.append(row)
        
        return {
            'students': [s[1] for s in students_list],
            'studentIds': [s[0] for s in students_list],
            'topics': topics_list,
            'values': values
        }
    
    # ========== Distractor Analysis (Item Analysis) ==========
    
    @staticmethod
    def get_distractor_analysis(exam_id, source='zipgrade'):
        """
        Analyze answer choice distribution for each question.
        Returns: {
            "q1": {"A": 15, "B": 60, "C": 10, "D": 15, "correct": "B", "misconception": "A"},
            ...
        }
        """
        analysis = {}
        
        if source == 'zipgrade':
            # Get all results with answers
            results = ExamResult.objects.filter(exam_id=exam_id)
            
            # Parse answers JSON and aggregate
            question_answers = defaultdict(lambda: defaultdict(int))
            
            for result in results:
                if result.answers:
                    try:
                        answers = json.loads(result.answers) if isinstance(result.answers, str) else result.answers
                        for q_num, answer in answers.items():
                            if answer:  # Skip blank answers
                                question_answers[q_num][str(answer).upper()] += 1
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            # Build analysis with misconception detection
            for q_num, answer_counts in question_answers.items():
                total = sum(answer_counts.values())
                
                # Find most common wrong answer (misconception)
                sorted_answers = sorted(answer_counts.items(), key=lambda x: x[1], reverse=True)
                
                analysis[q_num] = {
                    'distribution': dict(answer_counts),
                    'total_responses': total,
                    'percentages': {k: round((v/total)*100, 1) for k, v in answer_counts.items()},
                }
                
                # Identify misconception (most common non-correct answer > 30%)
                if len(sorted_answers) > 1:
                    for answer, count in sorted_answers[1:]:
                        pct = (count / total) * 100
                        if pct >= 30:
                            analysis[q_num]['misconception'] = {
                                'answer': answer,
                                'percentage': round(pct, 1),
                                'count': count
                            }
                            break
        
        else:  # Online exams
            exam = OnlineExam.objects.get(pk=exam_id)
            questions = exam.questions.prefetch_related('options').all()
            
            for question in questions:
                q_key = f"q{question.order}"
                
                # Get answer distribution
                answers = AttemptAnswer.objects.filter(
                    question=question,
                    attempt__status='completed'
                ).values('selected_option__text').annotate(count=Count('id'))
                
                correct_option = question.options.filter(is_correct=True).first()
                
                distribution = {}
                total = 0
                for a in answers:
                    opt_text = a['selected_option__text'] or 'Blank'
                    distribution[opt_text] = a['count']
                    total += a['count']
                
                analysis[q_key] = {
                    'question_text': question.text[:100],
                    'distribution': distribution,
                    'total_responses': total,
                    'correct': correct_option.text if correct_option else None,
                    'percentages': {k: round((v/total)*100, 1) for k, v in distribution.items()} if total > 0 else {}
                }
        
        return analysis
    
    # ========== Progressive Trend Line ==========
    
    @staticmethod
    def get_progressive_trend(student_id, exam_ids=None, source='zipgrade', limit=20):
        """
        Get chronological scores for trend visualization.
        Returns: {
            "labels": ["Exam 1", "Exam 2", ...],
            "dates": ["2024-01-01", ...],
            "scores": [75, 80, ...],
            "movingAverage": [null, null, 77.5, ...]
        }
        """
        scores_data = []
        
        if source == 'zipgrade':
            filters = {'student_id': student_id}
            if exam_ids:
                filters['exam_id__in'] = exam_ids
            
            results = ExamResult.objects.filter(
                **filters
            ).select_related('exam').order_by('exam__exam_date')[:limit]
            
            for r in results:
                scores_data.append({
                    'label': r.exam.title,
                    'date': r.exam.exam_date.isoformat(),
                    'score': float(r.percentage)
                })
        else:
            filters = {'student_id': student_id, 'status': 'completed'}
            if exam_ids:
                filters['exam_id__in'] = exam_ids
            
            attempts = ExamAttempt.objects.filter(
                **filters
            ).select_related('exam').order_by('started_at')[:limit]
            
            for a in attempts:
                scores_data.append({
                    'label': a.exam.title,
                    'date': a.started_at.date().isoformat(),
                    'score': float(a.percentage)
                })
        
        # Calculate moving average (window=3)
        scores = [d['score'] for d in scores_data]
        moving_avg = AdvancedAnalyticsHelper.calculate_moving_average(scores, window=3)
        
        return {
            'labels': [d['label'] for d in scores_data],
            'dates': [d['date'] for d in scores_data],
            'scores': scores,
            'movingAverage': moving_avg
        }
    
    @staticmethod
    def calculate_moving_average(data, window=3):
        """Calculate moving average with specified window size."""
        if len(data) < window:
            return [None] * len(data)
        
        result = [None] * (window - 1)
        for i in range(window - 1, len(data)):
            avg = sum(data[i - window + 1:i + 1]) / window
            result.append(round(avg, 1))
        
        return result
    
    # ========== Competency Gap Chart ==========
    
    @staticmethod
    def get_competency_gap(student_id, exam_ids, source='zipgrade'):
        """
        Calculate gap between student score and class/school average per subject.
        Returns: [
            {"subject": "Math", "student": 75, "classAvg": 80, "gap": -5},
            ...
        ]
        """
        gap_data = []
        
        if source == 'zipgrade':
            # Get student's subject scores
            student_by_subject = AdvancedAnalyticsHelper.aggregate_by_tags(
                exam_ids, student_id=student_id, source=source
            )
            
            # Get class averages
            class_by_subject = AdvancedAnalyticsHelper.aggregate_by_tags(
                exam_ids, student_id=None, source=source
            )
            
            # Calculate gaps
            all_subjects = set(student_by_subject.keys()) | set(class_by_subject.keys())
            
            for subject in all_subjects:
                student_pct = student_by_subject.get(subject, {}).get('percentage', 0)
                class_pct = class_by_subject.get(subject, {}).get('percentage', 0)
                
                gap_data.append({
                    'subject': subject,
                    'student': student_pct,
                    'classAvg': class_pct,
                    'gap': round(student_pct - class_pct, 1)
                })
        
        # Sort by gap (weakest first)
        gap_data.sort(key=lambda x: x['gap'])
        
        return gap_data
    
    # ========== Predictive Insights ==========
    
    @staticmethod
    def get_weakest_areas(student_id, exam_ids, source='zipgrade', top_n=3):
        """
        Identify top N weakest areas/subjects for the student.
        Returns: [
            {"subject": "Chemistry", "percentage": 45, "recommendation": "Focus on..."},
            ...
        ]
        """
        by_subject = AdvancedAnalyticsHelper.aggregate_by_tags(
            exam_ids, student_id=student_id, source=source
        )
        
        # Sort by percentage (lowest first)
        sorted_subjects = sorted(
            by_subject.items(),
            key=lambda x: x[1]['percentage']
        )[:top_n]
        
        weakest = []
        for subject, data in sorted_subjects:
            weakest.append({
                'subject': subject,
                'percentage': data['percentage'],
                'attempts': data['count'],
                'recommendation': f"Requires additional practice in {subject}. "
                                 f"Current mastery: {data['percentage']}%"
            })
        
        return weakest
    
    # ========== Grade Distribution (Bell Curve) ==========
    
    @staticmethod
    def get_grade_distribution(exam_ids, source='zipgrade', bucket_size=10):
        """
        Generate frequency distribution for score ranges.
        Returns: {
            "buckets": ["0-10", "11-20", ...],
            "frequencies": [2, 5, 10, ...],
            "percentages": [2.0, 5.0, 10.0, ...]
        }
        """
        # Define buckets
        buckets = []
        for i in range(0, 100, bucket_size):
            if i + bucket_size >= 100:
                buckets.append(f"{i}-100")
            else:
                buckets.append(f"{i}-{i + bucket_size - 1}")
        
        frequencies = [0] * len(buckets)
        
        if source == 'zipgrade':
            results = ExamResult.objects.filter(exam_id__in=exam_ids)
            scores = [float(r.percentage) for r in results]
        else:
            attempts = ExamAttempt.objects.filter(
                exam_id__in=exam_ids,
                status='completed'
            )
            scores = [float(a.percentage) for a in attempts]
        
        # Count frequencies
        for score in scores:
            bucket_idx = min(int(score // bucket_size), len(buckets) - 1)
            frequencies[bucket_idx] += 1
        
        total = len(scores)
        percentages = [round((f / total) * 100, 1) if total > 0 else 0 for f in frequencies]
        
        return {
            'buckets': buckets,
            'frequencies': frequencies,
            'percentages': percentages,
            'total': total,
            'mean': round(sum(scores) / total, 1) if total > 0 else 0,
            'max': max(scores) if scores else 0,
            'min': min(scores) if scores else 0
        }
    
    # ========== Drill-Down Helpers ==========
    
    @staticmethod
    def get_student_missed_questions(student_id, exam_id, source='zipgrade'):
        """
        Get list of questions the student got wrong.
        Returns: [{"question_num": 1, "student_answer": "A", "correct_answer": "B"}, ...]
        """
        missed = []
        
        if source == 'zipgrade':
            result = ExamResult.objects.filter(
                exam_id=exam_id,
                student_id=student_id
            ).first()
            
            if result and result.answers:
                try:
                    answers = json.loads(result.answers) if isinstance(result.answers, str) else result.answers
                    # Note: We'd need answer key data to determine correct answers
                    # For now, return the raw answers
                    for q_num, answer in answers.items():
                        # Mark questions with no answer or specific incorrect markers
                        missed.append({
                            'question_num': q_num,
                            'student_answer': answer,
                        })
                except (json.JSONDecodeError, TypeError):
                    pass
        else:
            attempt = ExamAttempt.objects.filter(
                exam_id=exam_id,
                student_id=student_id,
                status='completed'
            ).first()
            
            if attempt:
                wrong_answers = attempt.answers.filter(is_correct=False).select_related(
                    'question', 'selected_option'
                )
                
                for ans in wrong_answers:
                    correct_opt = ans.question.options.filter(is_correct=True).first()
                    missed.append({
                        'question_num': ans.question.order,
                        'question_text': ans.question.text[:100],
                        'student_answer': ans.selected_option.text if ans.selected_option else 'No answer',
                        'correct_answer': correct_opt.text if correct_opt else 'Unknown'
                    })
        
        return missed
    
    # ========== Class Performance Summary ==========
    
    @staticmethod
    def get_class_performance_summary(exam_ids, school=None, grade=None, section=None):
        """
        Get comprehensive class performance metrics.
        """
        filters = {'exam_id__in': exam_ids}
        if school:
            filters['exam__school'] = school
        
        results = ExamResult.objects.filter(**filters)
        
        if grade or section:
            results = results.filter(
                Q(student__grade=grade) if grade else Q(),
                Q(student__section=section) if section else Q()
            )
        
        scores = [float(r.percentage) for r in results]
        
        if not scores:
            return {
                'count': 0,
                'mean': 0,
                'median': 0,
                'std_dev': 0,
                'pass_rate': 0
            }
        
        # Calculate statistics
        n = len(scores)
        mean = sum(scores) / n
        
        sorted_scores = sorted(scores)
        median = sorted_scores[n // 2] if n % 2 else (sorted_scores[n//2-1] + sorted_scores[n//2]) / 2
        
        variance = sum((x - mean) ** 2 for x in scores) / n
        std_dev = variance ** 0.5
        
        pass_rate = len([s for s in scores if s >= 60]) / n * 100
        
        return {
            'count': n,
            'mean': round(mean, 1),
            'median': round(median, 1),
            'std_dev': round(std_dev, 1),
            'pass_rate': round(pass_rate, 1),
            'max': max(scores),
            'min': min(scores)
        }
