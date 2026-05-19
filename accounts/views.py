from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import UserRegistrationForm, UserLoginForm, PatientProfileForm
from .models import User
from queues.realtime import broadcast_queue_refresh


class HomeView(View):
    """Landing page view or Admin ML Analytics Dashboard."""
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.role == 'ADMIN' or request.user.is_staff:
                return render(request, 'admin/ml_analytics.html', {
                    'user': request.user,
                    'model_metrics': {
                        'rmse': '6.75 mins',
                        'r2': '92%',
                        'dataset_size': 800,
                        'model_type': 'Random Forest Regressor'
                    }
                })
            return redirect('role_redirect')
        return render(request, 'home.html')

    def post(self, request):
        if not (request.user.is_authenticated and (request.user.role == 'ADMIN' or request.user.is_staff)):
            from django.http import JsonResponse
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        from ml_models.predictor import predictor
        from django.http import JsonResponse

        try:
            hour = int(request.POST.get('hour', 10))
            day_of_week = int(request.POST.get('day_of_week', 1))
            queue_length = int(request.POST.get('queue_length', 5))
            doctor_count = int(request.POST.get('doctor_count', 2))
            department = request.POST.get('department', 'GENERAL')

            prediction = predictor.predict_wait_time(
                hour=hour,
                day_of_week=day_of_week,
                queue_length=queue_length,
                doctor_count=doctor_count,
                department=department
            )

            if prediction is not None:
                return JsonResponse({
                    'success': True,
                    'prediction': prediction
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Model could not generate prediction. Ensure the model is trained.'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class RegisterView(View):
    """Unified registration view for all roles."""
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('role_redirect')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('role_redirect')

        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == 'PATIENT':
                broadcast_queue_refresh(
                    'patient_registered',
                    {
                        'patient_id': user.patient_profile.id,
                        'patient_name': user.patient_profile.name,
                    },
                )
            messages.success(request, f"Account created successfully! Welcome, {user.first_name}.")
            login(request, user)
            return redirect('role_redirect')

        return render(request, self.template_name, {'form': form})


class LoginView(View):
    """Unified login view for all roles."""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('role_redirect')
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('role_redirect')

        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('role_redirect')

        return render(request, self.template_name, {'form': form})


class RoleRedirectView(LoginRequiredMixin, View):
    """Redirect users to their role-based dashboard after login."""
    def get(self, request):
        dashboard_url = request.user.get_dashboard_url()
        if dashboard_url:
            return HttpResponseRedirect(dashboard_url)
        messages.error(request, "Role not recognized. Please contact admin.")
        return redirect('home')


class ProfileView(LoginRequiredMixin, View):
    """User profile view."""
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = None
        if request.user.role == 'PATIENT':
            form = PatientProfileForm(user=request.user)
        return render(request, self.template_name, {
            'user': request.user,
            'form': form
        })

    def post(self, request):
        if request.user.role == 'PATIENT':
            form = PatientProfileForm(user=request.user, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your profile has been updated successfully!")
                return redirect('accounts:profile')
            
            return render(request, self.template_name, {
                'user': request.user,
                'form': form
            })
        
        return redirect('accounts:profile')
