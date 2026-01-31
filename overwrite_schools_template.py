
import os

file_path = r'C:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\analytics\templates\analytics\schools.html'

content = """{% extends 'base.html' %}
{% load i18n %}

{% block title %}{% trans "School Analytics" %} - {% if school %}{{ school.name }}{% else %}{% trans "All Schools" %}{% endif %}{% endblock %}

{% block content %}
<div class="topbar">
    <div class="topbar-left">
        <h1 class="topbar-title">{% trans "Analytics" %}: {% if school %}{{ school.name }}{% else %}{% trans "All Schools" %}{% endif %}</h1>
        {% if schools %}
        <div style="margin-left: 20px;">
            <select onchange="window.location.href='?school_id='+this.value+'&source={{ source }}'">
                <option value="all" {% if not school %}selected{% endif %}>{% trans "All Schools" %}</option>
                {% for s in schools %}
                <option value="{{ s.pk }}" {% if school and s.pk == school.pk %}selected{% endif %}>{{ s.name }}</option>
                {% endfor %}
            </select>
        </div>
        {% endif %}
        <div style="margin-left: 20px; display: flex; gap: 4px;">
            <a href="?{% if school %}school_id={{ school.pk }}&{% endif %}source=exams" class="btn btn-sm {% if source == 'exams' or not source %}btn-primary{% else %}btn-outline{% endif %}">{% trans "Exams" %}</a>
            <a href="?{% if school %}school_id={{ school.pk }}&{% endif %}source=zipgrade" class="btn btn-sm {% if source == 'zipgrade' %}btn-primary{% else %}btn-outline{% endif %}">{% trans "ZipGrade" %}</a>
        </div>
    </div>
    <div class="topbar-actions">
        <a href="{% url 'analytics:export_excel' %}{% if school %}?school_id={{ school.pk }}{% endif %}" class="btn btn-outline">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px;">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            {% trans "Excel" %}
        </a>
        <a href="{% url 'analytics:export_pdf' %}{% if school %}?school_id={{ school.pk }}{% endif %}" class="btn btn-outline">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px;">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            {% trans "PDF" %}
        </a>
        <button class="btn btn-outline" onclick="window.print()">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px;">
                <path d="M6 9V2h12v7"></path>
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                <path d="M6 14h12v8H6z"></path>
            </svg>
            {% trans "Print" %}
        </button>
    </div>
</div>

{% include 'partials/messages.html' %}

{% if source == 'zipgrade' and available_exams %}
<div class="card" style="margin-bottom: var(--spacing-lg);">
    <form method="get" style="display: flex; flex-wrap: wrap; gap: var(--spacing-md); align-items: flex-end;">
        <input type="hidden" name="source" value="zipgrade">
        {% if school %}<input type="hidden" name="school_id" value="{{ school.pk }}">{% endif %}
        {% if available_folders %}
        <div class="form-group" style="margin-bottom: 0; min-width: 200px;">
            <label class="form-label">{% trans "Folders" %}</label>
            <select name="folder_ids" multiple class="form-select" style="min-height: 80px;">
                {% for folder in available_folders %}
                <option value="{{ folder.pk }}" {% if folder.pk|stringformat:"i" in selected_folder_ids %}selected{% endif %}>{{ folder.name }}</option>
                {% endfor %}
            </select>
        </div>
        {% endif %}
        <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 250px;">
            <label class="form-label">{% trans "Select Exams" %}</label>
            <select name="exam_ids" multiple class="form-select" style="min-height: 80px;">
                {% for exam in available_exams %}
                <option value="{{ exam.pk }}" {% if exam.pk|stringformat:"i" in selected_exam_ids %}selected{% endif %}>{{ exam.title }} ({{ exam.school__name }})</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group" style="margin-bottom: 0; min-width: 180px;">
            <label class="form-label">{% trans "Subject" %}</label>
            <select name="subject_id" class="form-select">
                <option value="">{% trans "All Subjects" %}</option>
                {% for subject in available_subjects %}
                <option value="{{ subject.pk }}" {% if selected_subject_id == subject.pk|stringformat:"i" %}selected{% endif %}>{{ subject.name }}</option>
                {% endfor %}
            </select>
        </div>
        <button type="submit" class="btn btn-primary">{% trans "Apply Filters" %}</button>
        <a href="?source=zipgrade{% if school %}&school_id={{ school.pk }}{% endif %}" class="btn btn-outline">{% trans "Reset" %}</a>
    </form>
</div>
{% endif %}

{% if error %}
<div class="alert alert-danger">{{ error }}</div>
{% else %}

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-lg); margin-bottom: var(--spacing-xl);">
    <div class="card" style="text-align: center;">
        <div class="text-muted">{% trans "Total Exams Taken" %}</div>
        <div style="font-size: 2.5em; font-weight: bold; color: var(--primary);">{{ stats.online_exams.count }}</div>
    </div>
    <div class="card" style="text-align: center;">
        <div class="text-muted">{% trans "Average Score" %}</div>
        <div style="font-size: 2.5em; font-weight: bold; color: {% if stats.online_exams.avg_score >= 60 %}var(--success){% else %}var(--danger){% endif %};">{{ stats.online_exams.avg_score }}%</div>
    </div>
    <div class="card" style="text-align: center;">
        <div class="text-muted">{% trans "Pass Rate" %}</div>
        <div style="font-size: 2.5em; font-weight: bold; color: {% if stats.online_exams.pass_rate >= 70 %}var(--success){% else %}var(--warning){% endif %};">{{ stats.online_exams.pass_rate }}%</div>
    </div>
    <div class="card" style="text-align: center;">
        <div class="text-muted">{% trans "Best Score" %}</div>
        <div style="font-size: 2.5em; font-weight: bold; color: var(--success);">{{ stats.online_exams.max_score }}%</div>
    </div>
    <div class="card" style="text-align: center;">
        <div class="text-muted">{% trans "Lowest Score" %}</div>
        <div style="font-size: 2.5em; font-weight: bold; color: var(--danger);">{{ stats.online_exams.min_score }}%</div>
    </div>
</div>

{% if school_comparison_labels %}
<div class="card" style="margin-bottom: var(--spacing-xl);">
    <h3>{% trans "School Comparison" %} {% if selected_subject_id %}<span class="text-muted" style="font-size: 0.75rem;">({% trans "by subject" %})</span>{% endif %}</h3>
    <canvas id="schoolComparisonChart" height="200"></canvas>
</div>
{% endif %}

<div style="display: grid; grid-template-columns: 2fr 1fr; gap: var(--spacing-lg); margin-bottom: var(--spacing-xl);">
    <div class="card">
        <h3>{% trans "Exam Activity (Last 12 Weeks)" %}</h3>
        <canvas id="activityChart" height="150"></canvas>
    </div>
    <div class="card">
        <h3>{% trans "Recent Exams" %}</h3>
        <div class="table-container">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>{% trans "Exam" %}</th>
                        <th>{% trans "Date" %}</th>
                    </tr>
                </thead>
                <tbody>
                    {% for exam in recent_exams %}
                    <tr>
                        <td>{% if source == 'zipgrade' %}<a href="{% url 'zipgrade:exam_detail' exam.pk %}">{{ exam.title }}</a>{% else %}<a href="{% url 'exams:exam_results' exam.pk %}">{{ exam.title }}</a>{% endif %}</td>
                        <td>{% if source == 'zipgrade' %}{{ exam.exam_date|date:"d.m" }}{% else %}{{ exam.created_at|date:"d.m" }}{% endif %}</td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="2" class="text-muted text-center">{% trans "No exams yet" %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div style="margin-top: 10px; text-align: center;">
            {% if source == 'zipgrade' %}
            <a href="{% url 'zipgrade:results' %}" class="btn btn-sm btn-outline">{% trans "View All Exams" %}</a>
            {% else %}
            <a href="{% url 'exams:exam_list' %}" class="btn btn-sm btn-outline">{% trans "View All Exams" %}</a>
            {% endif %}
        </div>
    </div>
</div>

{% endif %}
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    const ctx = document.getElementById('activityChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: {{ chart_labels| safe }},
            datasets: [{
                label: '{% trans "Completed Exams" %}',
                data: {{ chart_data| safe }},
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
        }
    });

    {% if school_comparison_labels %}
    const compCtx = document.getElementById('schoolComparisonChart').getContext('2d');
    new Chart(compCtx, {
        type: 'bar',
        data: {
            labels: {{ school_comparison_labels| safe }},
            datasets: [{
                label: '{% trans "Average Score %" %}',
                data: {{ school_comparison_data| safe }},
                backgroundColor: ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1'],
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, max: 100, ticks: { callback: function (v) { return v + '%'; } } } }
        }
    });
    {% endif %}
</script>
{% endblock %}
"""

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully overwrote {file_path} with {len(content)} bytes.")
