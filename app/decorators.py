from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def staff_required(view_func):
    """Restrict a view to staff/admin accounts. Anonymous users are sent to
    login; authenticated non-staff users are bounced to their own dashboard."""

    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to access that page.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper
