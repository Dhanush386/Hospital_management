from django.shortcuts import redirect
from django.contrib import messages


class RoleRedirectMiddleware:
    """Middleware to handle role-based access control and redirects."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info

            if path.startswith('/admin/'):
                return self.get_response(request)

            role_paths = {
                'PATIENT': ['/patient/', '/auth/', '/redirect/'],
                'DOCTOR': ['/doctor/', '/auth/', '/redirect/'],
                'LAB': ['/lab/', '/auth/', '/redirect/'],
                'PHARMACY': ['/pharmacy/', '/auth/', '/redirect/'],
                'ADMIN': ['/admin/', '/auth/', '/redirect/'],
            }

            allowed = role_paths.get(request.user.role, [])

            if (
                path == '/'
                or path.startswith('/static/')
                or path.startswith('/media/')
                or path.startswith('/queue/display/')
                or path.startswith('/queue/api/status/')
                or '/view-file/' in path
            ):
                return self.get_response(request)

            is_allowed = any(path.startswith(prefix) for prefix in allowed)

            if not is_allowed:
                dashboard_url = request.user.get_dashboard_url()
                if dashboard_url and dashboard_url != path:
                    messages.warning(request, "You don't have access to that area.")
                    return redirect(dashboard_url)

        response = self.get_response(request)
        return response
