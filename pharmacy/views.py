from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from patients.models import Prescription
from .models import PharmacyOrder


class PharmacyRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'PHARMACY'


class PharmacyDashboardView(LoginRequiredMixin, PharmacyRequiredMixin, View):
    template_name = 'pharmacy/dashboard.html'

    def get(self, request):
        pending_prescriptions = Prescription.objects.filter(
            status='PENDING'
        ).select_related('patient', 'doctor').order_by('-created_at')

        ready_prescriptions = Prescription.objects.filter(
            status='READY'
        ).select_related('patient', 'doctor').order_by('-updated_at')

        dispensed_prescriptions = Prescription.objects.filter(
            status='DISPENSED'
        ).select_related('patient', 'doctor').order_by('-dispensed_at')[:20]

        return render(request, self.template_name, {
            'pending_prescriptions': pending_prescriptions,
            'ready_prescriptions': ready_prescriptions,
            'dispensed_prescriptions': dispensed_prescriptions,
        })


class PrescriptionDetailView(LoginRequiredMixin, PharmacyRequiredMixin, View):
    template_name = 'pharmacy/prescription_detail.html'

    def get(self, request, prescription_id):
        prescription = get_object_or_404(Prescription, id=prescription_id)
        return render(request, self.template_name, {'prescription': prescription})

    def post(self, request, prescription_id):
        prescription = get_object_or_404(Prescription, id=prescription_id)
        action = request.POST.get('action')

        if action == 'mark_ready':
            prescription.status = 'READY'
            prescription.save()

            PharmacyOrder.objects.create(
                patient=prescription.patient,
                prescription=prescription,
                status='READY',
                prepared_by=request.user
            )

            messages.success(request, f"Prescription for {prescription.patient.name} is ready!")

        elif action == 'dispense':
            prescription.status = 'DISPENSED'
            prescription.dispensed_at = timezone.now()
            prescription.dispensed_by = request.user
            prescription.save()

            pharmacy_order = PharmacyOrder.objects.filter(
                prescription=prescription,
                status='READY'
            ).first()

            if pharmacy_order:
                pharmacy_order.status = 'DISPENSED'
                pharmacy_order.dispensed_by = request.user
                pharmacy_order.dispensed_at = timezone.now()
                pharmacy_order.save()

            messages.success(request, f"Prescription dispensed to {prescription.patient.name}")

        return redirect('pharmacy:dashboard')


class PrescriptionListView(LoginRequiredMixin, PharmacyRequiredMixin, View):
    template_name = 'pharmacy/prescription_list.html'

    def get(self, request):
        status = request.GET.get('status', '')

        prescriptions = Prescription.objects.select_related('patient', 'doctor')

        if status:
            prescriptions = prescriptions.filter(status=status)

        prescriptions = prescriptions.order_by('-created_at')

        return render(request, self.template_name, {
            'prescriptions': prescriptions,
            'current_status': status,
        })
