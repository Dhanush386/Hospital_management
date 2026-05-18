from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import LabOrder


class LabRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'LAB'


def get_lab_department(user):
    profile = getattr(user, 'lab_profile', None)
    return profile.department if profile else ''


def get_lab_orders_for_user(user):
    orders = LabOrder.objects.select_related(
        'patient',
        'doctor',
        'doctor__doctor_profile',
        'completed_by',
    )
    department = get_lab_department(user)
    orders = orders.filter(Q(assigned_lab__isnull=True) | Q(assigned_lab=user))
    if department:
        orders = orders.filter(
            Q(assigned_lab=user) |
            Q(assigned_lab__isnull=True, test_type=department)
        )
    return orders


class LabDashboardView(LoginRequiredMixin, LabRequiredMixin, View):
    template_name = 'lab/dashboard.html'

    def get(self, request):
        lab_orders = get_lab_orders_for_user(request.user)

        pending_orders = lab_orders.filter(
            status='PENDING'
        ).order_by('-created_at')

        in_progress_orders = lab_orders.filter(
            status='IN_PROGRESS'
        ).order_by('-created_at')

        completed_orders = lab_orders.filter(
            status='COMPLETED'
        ).order_by('-completed_at')[:20]

        return render(request, self.template_name, {
            'pending_orders': pending_orders,
            'in_progress_orders': in_progress_orders,
            'completed_orders': completed_orders,
            'lab_department': get_lab_department(request.user),
        })


class LabOrderDetailView(LoginRequiredMixin, LabRequiredMixin, View):
    template_name = 'lab/order_detail.html'

    def get(self, request, order_id):
        order = get_object_or_404(get_lab_orders_for_user(request.user), id=order_id)
        return render(request, self.template_name, {'order': order})

    def post(self, request, order_id):
        order = get_object_or_404(get_lab_orders_for_user(request.user), id=order_id)
        action = request.POST.get('action')

        if action == 'start':
            order.status = 'IN_PROGRESS'
            order.save()
            messages.success(request, f"Started working on {order.test_name}")

        elif action == 'complete':
            order.status = 'COMPLETED'
            order.result_notes = request.POST.get('result_notes', '')

            uploaded_file = request.FILES.get('result_file')
            if uploaded_file:
                # Try to upload to cloud storage (Catbox) to support serverless environment
                cloud_url = None
                try:
                    import requests
                    url = "https://catbox.moe/user/api.php"
                    uploaded_file.seek(0)
                    files = {
                        'fileToUpload': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
                    }
                    data = {
                        'reqtype': 'fileupload'
                    }
                    response = requests.post(url, data=data, files=files, timeout=15)
                    if response.status_code == 200:
                        file_url = response.text.strip()
                        if file_url.startswith("http"):
                            cloud_url = file_url
                except Exception as e:
                    print(f"[!] Catbox upload failed, falling back to local storage: {e}")

                if cloud_url:
                    # Save the direct cloud URL string to the FileField
                    order.result_file = cloud_url
                else:
                    # Fallback to local /tmp/media storage
                    uploaded_file.seek(0)
                    order.result_file = uploaded_file

            order.completed_at = timezone.now()
            order.completed_by = request.user
            order.save()

            messages.success(request, f"Completed {order.test_name} for {order.patient.name}")

        elif action == 'cancel':
            order.status = 'CANCELLED'
            order.save()
            messages.warning(request, f"Cancelled {order.test_name}")

        return redirect('lab:dashboard')


class LabOrderListView(LoginRequiredMixin, LabRequiredMixin, View):
    template_name = 'lab/order_list.html'

    def get(self, request):
        status = request.GET.get('status', '')

        orders = get_lab_orders_for_user(request.user)

        if status:
            orders = orders.filter(status=status)

        orders = orders.order_by('-created_at')

        return render(request, self.template_name, {
            'orders': orders,
            'current_status': status,
            'lab_department': get_lab_department(request.user),
        })
