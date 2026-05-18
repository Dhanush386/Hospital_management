from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from accounts.models import User
from patients.models import Patient, Prescription, ConsultationNote
from queues.models import QueueSlot
from queues.realtime import broadcast_queue_update
from lab.models import LabOrder
from .models import DoctorAvailability
from utils.ai_nlp_service import generate_soap_note_from_transcript


class DoctorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'DOCTOR'


def get_doctor_department(user):
    profile = getattr(user, 'doctor_profile', None)
    return profile.department if profile else ''


def get_available_lab_technicians(test_type=None):
    lab_users = User.objects.filter(
        role='LAB',
        is_active=True,
    )
    if test_type:
        lab_users = lab_users.filter(lab_profile__department__in=['', test_type])
    return lab_users.select_related('lab_profile').order_by('first_name', 'last_name', 'username')


def get_lab_technicians_by_test_type():
    return User.objects.filter(
        role='LAB',
        is_active=True,
    ).select_related('lab_profile').order_by('lab_profile__department', 'first_name', 'last_name', 'username')


class DoctorDashboardView(LoginRequiredMixin, DoctorRequiredMixin, View):
    template_name = 'doctors/dashboard.html'

    def get(self, request):
        doctor_department = get_doctor_department(request.user)

        assigned_patients = QueueSlot.objects.filter(
            doctor=request.user,
            status='IN_PROGRESS'
        ).select_related('patient')

        waiting_patients = QueueSlot.objects.filter(
            status='WAITING',
            department=doctor_department,
        ).select_related('patient').order_by('priority', 'slot_time')[:10]

        my_lab_orders = LabOrder.objects.filter(
            doctor=request.user,
            status__in=['PENDING', 'IN_PROGRESS']
        ).select_related('patient')[:10]

        recent_prescriptions = Prescription.objects.filter(
            doctor=request.user
        ).select_related('patient').order_by('-created_at')[:10]

        availability, _ = DoctorAvailability.objects.get_or_create(
            doctor=request.user,
            defaults={'is_online': True}
        )

        context = {
            'assigned_patients': assigned_patients,
            'waiting_patients': waiting_patients,
            'my_lab_orders': my_lab_orders,
            'recent_prescriptions': recent_prescriptions,
            'availability': availability,
            'doctor_department': doctor_department,
        }
        return render(request, self.template_name, context)


class DoctorQueueView(LoginRequiredMixin, DoctorRequiredMixin, View):
    template_name = 'doctors/queue.html'

    def get(self, request):
        doctor_department = get_doctor_department(request.user)

        waiting_patients = QueueSlot.objects.filter(
            status='WAITING',
            department=doctor_department,
        ).select_related('patient').order_by('priority', 'slot_time')

        in_progress = QueueSlot.objects.filter(
            doctor=request.user,
            status='IN_PROGRESS'
        ).select_related('patient')

        my_history = QueueSlot.objects.filter(
            doctor=request.user,
            status='COMPLETED'
        ).select_related('patient').order_by('-completed_at')[:20]

        return render(request, self.template_name, {
            'waiting_patients': waiting_patients,
            'in_progress': in_progress,
            'my_history': my_history,
            'doctor_department': doctor_department,
        })

    def post(self, request):
        action = request.POST.get('action')
        queue_slot_id = request.POST.get('queue_slot_id')
        doctor_department = get_doctor_department(request.user)

        if action == 'accept':
            slot = get_object_or_404(
                QueueSlot,
                id=queue_slot_id,
                status='WAITING',
                department=doctor_department,
            )
            slot.status = 'IN_PROGRESS'
            slot.doctor = request.user
            slot.started_at = timezone.now()
            slot.save()
            broadcast_queue_update('accepted', slot)
            messages.success(request, f"Patient {slot.patient.name} assigned to you.")

        elif action == 'complete':
            slot = get_object_or_404(QueueSlot, id=queue_slot_id, doctor=request.user, status='IN_PROGRESS')
            slot.status = 'COMPLETED'
            slot.completed_at = timezone.now()
            slot.save()
            broadcast_queue_update('completed', slot)
            messages.success(request, f"Consultation with {slot.patient.name} completed.")

        return redirect('doctors:queue')


class DoctorConsultationView(LoginRequiredMixin, DoctorRequiredMixin, View):
    template_name = 'doctors/consultation.html'

    def get(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)

        current_slot = QueueSlot.objects.filter(
            patient=patient,
            doctor=request.user,
            status='IN_PROGRESS'
        ).first()

        prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')[:5]
        lab_orders = LabOrder.objects.filter(patient=patient).order_by('-created_at')[:5]
        consultation_notes = ConsultationNote.objects.filter(
            patient=patient
        ).order_by('-created_at')[:5]
        lab_technicians = get_lab_technicians_by_test_type()

        return render(request, self.template_name, {
            'patient': patient,
            'current_slot': current_slot,
            'prescriptions': prescriptions,
            'lab_orders': lab_orders,
            'consultation_notes': consultation_notes,
            'lab_technicians': lab_technicians,
        })


class CreatePrescriptionView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def post(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)

        medicines = request.POST.getlist('medicine[]')
        dosages = request.POST.getlist('dosage[]')
        durations = request.POST.getlist('duration[]')
        instructions = request.POST.getlist('instructions[]')

        medicines_data = {
            'medicines': [
                {
                    'name': med,
                    'dosage': dos,
                    'duration': dur,
                    'instructions': inst
                }
                for med, dos, dur, inst in zip(medicines, dosages, durations, instructions)
                if med
            ]
        }

        notes = request.POST.get('notes', '')

        prescription = Prescription.objects.create(
            patient=patient,
            doctor=request.user,
            medicines_json=medicines_data,
            notes=notes
        )

        messages.success(request, 'Prescription created successfully!')
        return redirect('doctors:consultation', patient_id=patient_id)


class CreateLabOrderView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def post(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)

        test_type = request.POST.get('test_type')
        custom_test = request.POST.get('custom_test', '')
        notes = request.POST.get('notes', '')
        assigned_lab_id = request.POST.get('assigned_lab')
        assigned_lab = None

        if assigned_lab_id:
            assigned_lab = get_object_or_404(
                get_available_lab_technicians(test_type),
                id=assigned_lab_id,
            )

        if test_type == 'OTHER' and custom_test:
            test_type = 'OTHER'

        LabOrder.objects.create(
            patient=patient,
            doctor=request.user,
            assigned_lab=assigned_lab,
            test_type=test_type,
            custom_test_name=custom_test if test_type == 'OTHER' else '',
            notes=notes
        )

        messages.success(request, 'Lab order created successfully!')
        return redirect('doctors:consultation', patient_id=patient_id)


class SaveConsultationNoteView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def post(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)

        transcript = request.POST.get('transcript', '')
        structured_note = {
            'subjective': request.POST.get('subjective', ''),
            'objective': request.POST.get('objective', ''),
            'assessment': request.POST.get('assessment', ''),
            'plan': request.POST.get('plan', ''),
        }

        ConsultationNote.objects.create(
            patient=patient,
            doctor=request.user,
            transcript=transcript,
            structured_note=structured_note,
            approved=True
        )

        messages.success(request, 'Consultation note saved!')
        return redirect('doctors:consultation', patient_id=patient_id)


@method_decorator(csrf_exempt, name='dispatch')
class GenerateSOAPNoteView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def post(self, request, patient_id):
        transcript = request.POST.get('transcript', '')
        if not transcript:
            return JsonResponse({'error': 'No transcript provided'}, status=400)
        
        soap_note = generate_soap_note_from_transcript(transcript)
        return JsonResponse(soap_note)


class ToggleAvailabilityView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def post(self, request):
        availability, _ = DoctorAvailability.objects.get_or_create(doctor=request.user)
        availability.is_online = not availability.is_online
        availability.save()

        status = 'online' if availability.is_online else 'offline'
        messages.success(request, f'You are now {status}.')

        return redirect('doctors:dashboard')


class DoctorLabResultsView(LoginRequiredMixin, DoctorRequiredMixin, View):
    template_name = 'doctors/lab_results.html'

    def get(self, request):
        lab_orders = LabOrder.objects.filter(
            doctor=request.user
        ).select_related('patient').order_by('-created_at')

        return render(request, self.template_name, {'lab_orders': lab_orders})
