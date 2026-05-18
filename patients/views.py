from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q
from django.contrib import messages
from accounts.models import DoctorProfile
from .models import Patient, Prescription, ConsultationNote
from lab.models import LabOrder
from queues.models import QueueSlot
from queues.realtime import broadcast_queue_update


class PatientRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'PATIENT'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseRedirect(self.request.user.get_dashboard_url())


class PatientDashboardView(LoginRequiredMixin, PatientRequiredMixin, View):
    template_name = 'patients/dashboard.html'

    def add_doctor_status(self, queue_slots):
        availability_view = PatientJoinQueueView()
        for slot in queue_slots:
            status = get_queue_slot_doctor_status(slot, availability_view)
            slot.doctor_is_online = status['doctor_is_online']
            slot.doctor_status_display = status['doctor_status_display']
            slot.doctor_status_detail = status['doctor_status_detail']
        return queue_slots

    def get(self, request):
        patient = None
        if hasattr(request.user, 'patient_profile'):
            patient = request.user.patient_profile
        else:
            patient = Patient.objects.filter(
                Q(user=request.user) | Q(phone=request.user.phone_number)
            ).first()

        prescriptions = []
        lab_orders = []
        queue_slots = []
        consultation_notes = []

        if patient:
            prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')[:5]
            lab_orders = LabOrder.objects.filter(patient=patient).order_by('-created_at')[:5]
            queue_slots = patient.queue_slots.filter(
                status__in=['WAITING', 'IN_PROGRESS']
            ).select_related('doctor', 'doctor__availability').order_by('-created_at')
            queue_slots = self.add_doctor_status(queue_slots)
            consultation_notes = ConsultationNote.objects.filter(patient=patient).order_by('-created_at')[:3]

        context = {
            'patient': patient,
            'prescriptions': prescriptions,
            'lab_orders': lab_orders,
            'queue_slots': queue_slots,
            'consultation_notes': consultation_notes,
        }
        return render(request, self.template_name, context)


class PatientPrescriptionsView(LoginRequiredMixin, PatientRequiredMixin, View):
    template_name = 'patients/prescriptions.html'

    def get(self, request):
        patient = request.user.patient_profile if hasattr(request.user, 'patient_profile') else None
        prescriptions = []

        if patient:
            prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')

        return render(request, self.template_name, {'prescriptions': prescriptions, 'patient': patient})


class PatientLabResultsView(LoginRequiredMixin, PatientRequiredMixin, View):
    template_name = 'patients/lab_results.html'

    def get(self, request):
        patient = request.user.patient_profile if hasattr(request.user, 'patient_profile') else None
        lab_orders = []

        if patient:
            lab_orders = LabOrder.objects.filter(patient=patient).order_by('-created_at')

        return render(request, self.template_name, {'lab_orders': lab_orders, 'patient': patient})


class PatientQueueStatusView(LoginRequiredMixin, PatientRequiredMixin, View):
    def get(self, request):
        patient = request.user.patient_profile if hasattr(request.user, 'patient_profile') else None

        if not patient:
            return JsonResponse({'error': 'Patient not found'}, status=404)

        queue_slots = patient.queue_slots.filter(
            status__in=['WAITING', 'IN_PROGRESS']
        ).select_related('doctor', 'doctor__availability').order_by('-created_at')

        return JsonResponse({
            'queue_slots': [
                {
                    'id': slot.id,
                    'department': slot.department,
                    'department_display': slot.get_department_display(),
                    'token_number': slot.token_number,
                    'token_date': slot.token_date.isoformat(),
                    'status': slot.status,
                    'status_display': slot.get_status_display(),
                    'position_in_queue': slot.position_in_queue,
                    'slot_time': slot.slot_time.isoformat(),
                    **get_queue_slot_doctor_status(slot),
                }
                for slot in queue_slots
            ]
        })


class PatientJoinQueueView(LoginRequiredMixin, PatientRequiredMixin, View):
    template_name = 'patients/join_queue.html'

    def get_department_availability(self, department):
        doctors = DoctorProfile.objects.filter(
            user__role='DOCTOR',
            user__is_active=True,
            department=department,
            is_available=True,
        ).select_related('user')

        online_doctors = doctors.filter(user__availability__is_online=True)

        return {
            'department': department,
            'total_doctors': doctors.count(),
            'available_count': online_doctors.count(),
            'is_available': online_doctors.exists(),
            'doctors': [
                doctor.user.get_full_name() or doctor.user.username
                for doctor in online_doctors[:3]
            ],
        }

    def get_patient(self, request):
        if hasattr(request.user, 'patient_profile'):
            return request.user.patient_profile
        return Patient.objects.filter(
            Q(user=request.user) | Q(phone=request.user.phone_number)
        ).first()

    def get(self, request):
        patient = self.get_patient(request)
        active_slots = []

        if patient:
            active_slots = patient.queue_slots.filter(
                status__in=['WAITING', 'IN_PROGRESS']
            ).order_by('-created_at')

        context = {
            'patient': patient,
            'active_slots': active_slots,
            'department_choices': QueueSlot.DEPARTMENT_CHOICES,
            'default_availability': self.get_department_availability(QueueSlot.DEPARTMENT_CHOICES[0][0]),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        patient = self.get_patient(request)
        if not patient:
            messages.error(request, 'Your account is not linked to a patient profile yet.')
            return redirect('patients:dashboard')

        department = request.POST.get('department', 'GENERAL')
        valid_departments = {choice[0] for choice in QueueSlot.DEPARTMENT_CHOICES}
        if department not in valid_departments:
            messages.error(request, 'Please select a valid department.')
            return redirect('patients:join_queue')

        availability = self.get_department_availability(department)
        if availability['is_available']:
            doctor_names = ', '.join(availability['doctors'])
            messages.info(request, f'Doctor available in this department: {doctor_names}.')
        elif availability['total_doctors']:
            messages.warning(request, 'No doctor is currently online for this department. You can still join the queue.')
        else:
            messages.warning(request, 'No doctor has been assigned to this department yet. You can still join the queue.')

        queue_slot = QueueSlot.objects.create(patient=patient, department=department)
        broadcast_queue_update('created', queue_slot)
        messages.success(request, f'You have been added to the queue. Your token is {queue_slot.token_number}.')
        return redirect('patients:dashboard')


def get_queue_slot_doctor_status(slot, availability_view=None):
    if slot.doctor_id:
        availability = getattr(slot.doctor, 'availability', None)
        is_online = bool(availability and availability.is_online)
        doctor_name = slot.doctor.get_full_name() or slot.doctor.username
        return {
            'doctor_is_online': is_online,
            'doctor_status_display': 'Online' if is_online else 'Offline',
            'doctor_status_detail': f'Dr. {doctor_name}',
        }

    availability_view = availability_view or PatientJoinQueueView()
    availability = availability_view.get_department_availability(slot.department)
    doctor_names = ', '.join(availability['doctors'])
    return {
        'doctor_is_online': availability['is_available'],
        'doctor_status_display': 'Online' if availability['is_available'] else 'Offline',
        'doctor_status_detail': doctor_names or 'No doctor currently online',
    }


class DepartmentAvailabilityView(LoginRequiredMixin, PatientRequiredMixin, View):
    def get(self, request):
        department = request.GET.get('department', 'GENERAL')
        valid_departments = {choice[0] for choice in QueueSlot.DEPARTMENT_CHOICES}

        if department not in valid_departments:
            return JsonResponse({'error': 'Invalid department'}, status=400)

        availability = PatientJoinQueueView().get_department_availability(department)
        return JsonResponse(availability)
