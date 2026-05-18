from django.db.models import Count
from queues.models import QueueSlot
from accounts.models import User
from ml_models.predictor import predictor
from django.utils import timezone

class QueueOptimizer:
    """
    Intelligent Queue Optimization Engine.
    Handles risk assessment, anomaly detection, and adaptive recommendations.
    """

    @staticmethod
    def assess_risk_level(queue_length, doctor_count):
        if doctor_count == 0:
            return '🔴 High Congestion'
            
        ratio = queue_length / doctor_count
        if ratio < 5:
            return '🟢 Low Congestion'
        elif ratio <= 10:
            return '🟡 Medium Congestion'
        else:
            return '🔴 High Congestion'

    @staticmethod
    def detect_anomaly(department, queue_length, predicted_wait_time):
        """
        Statistical Thresholding to detect unusually long queues.
        """
        # Thresholds: Queue > 15 OR Wait > 90 mins is an anomaly
        if queue_length > 15 or predicted_wait_time > 90:
            return {
                'is_anomaly': True,
                'alert': f"Queue length unusually high for {department}."
            }
        return {'is_anomaly': False, 'alert': None}

    @staticmethod
    def get_adaptive_recommendation(department, current_wait_time):
        """
        Recommends an alternative doctor in the same department to reduce wait time.
        """
        # Get all doctors in this department
        # Note: In a full system, doctors would be tied to departments. 
        # For this MVP, we assume any doctor online could potentially help, 
        # but let's find the doctor with the least assigned patients.
        
        # Get doctors who are online/available
        available_doctors = User.objects.filter(role='DOCTOR').annotate(
            patient_count=Count('assigned_patients')
        ).order_by('patient_count')

        if not available_doctors.exists():
            return None

        best_alternative = available_doctors.first()
        
        # Simulate what the wait time would be if assigned to them
        current_time = timezone.now()
        alternative_wait = predictor.predict_wait_time(
            hour=current_time.hour,
            day_of_week=current_time.weekday(),
            queue_length=best_alternative.patient_count,
            doctor_count=1, # Evaluating a single doctor
            department=department
        )

        if alternative_wait and alternative_wait < current_wait_time:
            reduction = current_wait_time - alternative_wait
            if reduction > 5: # Only recommend if saves more than 5 mins
                return {
                    'suggested_doctor': f"Dr. {best_alternative.last_name}",
                    'wait_reduction': reduction,
                    'message': f"{department} queue overloaded. Suggested Doctor: Dr. {best_alternative.last_name}. Estimated wait reduction: {reduction} mins"
                }
        
        return None

    @classmethod
    def analyze_department_queue(cls, department):
        queue_length = QueueSlot.objects.filter(department=department, status='WAITING').count()
        doctor_count = User.objects.filter(role='DOCTOR').count() or 1
        
        current_time = timezone.now()
        predicted_wait = predictor.predict_wait_time(
            hour=current_time.hour,
            day_of_week=current_time.weekday(),
            queue_length=queue_length,
            doctor_count=doctor_count,
            department=department
        ) or 15

        risk_level = cls.assess_risk_level(queue_length, doctor_count)
        anomaly = cls.detect_anomaly(department, queue_length, predicted_wait)
        recommendation = None
        
        if 'High' in risk_level or 'Medium' in risk_level:
            recommendation = cls.get_adaptive_recommendation(department, predicted_wait)

        return {
            'department': department,
            'queue_length': queue_length,
            'predicted_wait': predicted_wait,
            'risk_level': risk_level,
            'anomaly': anomaly,
            'recommendation': recommendation
        }

optimizer = QueueOptimizer()
