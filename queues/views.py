from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import QueueSlot
from .realtime import broadcast_queue_update
from patients.models import Patient
from accounts.models import User
from django.utils import timezone
from ml_models.predictor import predictor


class PublicQueueView(View):
    template_name = 'queue/public_display.html'

    def get(self, request):
        active_slots = QueueSlot.objects.filter(
            status__in=['WAITING', 'IN_PROGRESS']
        ).select_related('patient', 'doctor').order_by('department', 'status', 'slot_time')

        department_stats = QueueSlot.objects.filter(
            status='WAITING'
        ).values('department').annotate(
            waiting_count=Count('id')
        ).order_by('department')

        from utils.queue_optimizer import optimizer
        enhanced_stats = []
        for stat in department_stats:
            analysis = optimizer.analyze_department_queue(stat['department'])
            enhanced_stats.append({
                'department': stat['department'],
                'waiting_count': stat['waiting_count'],
                'risk_level': analysis['risk_level'],
                'anomaly': analysis['anomaly'],
                'recommendation': analysis['recommendation']
            })

        context = {
            'active_slots': active_slots,
            'department_stats': enhanced_stats,
        }
        return render(request, self.template_name, context)


class QueueStatusApiView(View):
    def get(self, request):
        department = request.GET.get('department')

        slots = QueueSlot.objects.filter(
            status__in=['WAITING', 'IN_PROGRESS']
        )

        if department:
            slots = slots.filter(department=department)

        data = slots.values(
            'id', 'token_number', 'token_date', 'department', 'status', 'priority',
            'patient__name', 'patient__token_id',
            'doctor__first_name', 'doctor__last_name',
            'slot_time', 'started_at'
        )

        return JsonResponse({'slots': list(data)})


class AddToQueueView(LoginRequiredMixin, View):
    def post(self, request):
        patient_id = request.POST.get('patient_id')
        department = request.POST.get('department', 'GENERAL')
        priority = request.POST.get('priority', 0)

        patient = get_object_or_404(Patient, id=patient_id)

        # Calculate ML features
        current_time = timezone.now()
        hour = current_time.hour
        day_of_week = current_time.weekday()
        queue_length = QueueSlot.objects.filter(department=department, status='WAITING').count()
        
        # Estimate active doctors
        doctor_count = User.objects.filter(role='DOCTOR').count() # Simplified, could be specifically online doctors
        if doctor_count == 0:
            doctor_count = 1

        # ML Prediction
        predicted_wait = predictor.predict_wait_time(
            hour=hour,
            day_of_week=day_of_week,
            queue_length=queue_length,
            doctor_count=doctor_count,
            department=department
        )

        queue_slot = QueueSlot.objects.create(
            patient=patient,
            department=department,
            priority=int(priority),
            predicted_wait_time=predicted_wait,
            estimated_wait_time=predicted_wait if predicted_wait else 15
        )

        broadcast_queue_update('created', queue_slot)

        return JsonResponse({
            'success': True,
            'queue_id': queue_slot.id,
            'token': queue_slot.token_number,
            'department': department
        })
