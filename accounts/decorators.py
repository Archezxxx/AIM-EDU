from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


def super_admin_required(view_func):
    """Decorator that requires super_admin role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role != 'super_admin':
            messages.error(request, _('You do not have permission to access this page.'))
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_or_admin_required(view_func):
    """Decorator that requires teacher or super_admin role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role not in ['super_admin', 'teacher']:
            messages.error(request, _('You do not have permission to access this page.'))
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """Decorator that requires student role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role != 'student':
            messages.error(request, _('This page is for students only.'))
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(allowed_roles):
    """Decorator that requires user to have one of the allowed roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in allowed_roles:
                messages.error(request, _('You do not have permission to access this page.'))
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
