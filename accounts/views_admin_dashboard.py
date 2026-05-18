from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from queues.models import QueueSlot
from accounts.models import User
import json
import os

class AdminAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'accounts/admin_analytics.html'

    def test_func(self):
        return self.request.user.role == 'ADMIN' or self.request.user.is_superuser

    def get(self, request):
        # 1. Department Footfall
        dept_footfall = QueueSlot.objects.values('department').annotate(
            total_patients=Count('id')
        ).order_by('-total_patients')
        
        dept_labels = [item['department'] for item in dept_footfall]
        dept_data = [item['total_patients'] for item in dept_footfall]

        # 2. Average Consultation Time & Doctor Efficiency
        # We define efficiency = Patients Handled / Avg Consultation Time (in minutes)
        # Using completed_at - started_at
        duration_expr = ExpressionWrapper(
            F('completed_at') - F('started_at'),
            output_field=fields.DurationField()
        )
        
        doctor_stats = QueueSlot.objects.filter(status='COMPLETED', doctor__isnull=False).annotate(
            duration=duration_expr
        ).values('doctor__first_name', 'doctor__last_name').annotate(
            avg_duration=Avg('duration'),
            patients_handled=Count('id')
        )
        
        doc_labels = []
        doc_avg_times = []
        doc_efficiency = []
        
        for stat in doctor_stats:
            name = f"Dr. {stat['doctor__last_name']}"
            avg_mins = stat['avg_duration'].total_seconds() / 60 if stat['avg_duration'] else 0
            efficiency = round(stat['patients_handled'] / avg_mins, 2) if avg_mins > 0 else 0
            
            doc_labels.append(name)
            doc_avg_times.append(round(avg_mins, 2))
            doc_efficiency.append(efficiency)

        # 3. Peak Hour Analysis
        # Count patients based on the hour they were created
        hourly_slots = QueueSlot.objects.annotate(
            hour=ExpressionWrapper(F('created_at'), output_field=fields.DateTimeField())
        ) # This is complex in SQLite/Postgres. We can do it in Python for MVP.
        
        all_slots = QueueSlot.objects.all()
        hour_counts = {str(h): 0 for h in range(8, 21)} # 8 AM to 8 PM
        for slot in all_slots:
            h = str(timezone.localtime(slot.created_at).hour)
            if h in hour_counts:
                hour_counts[h] += 1
                
        peak_hour = max(hour_counts, key=hour_counts.get, default="10")
        
        # 4. Read Feature Importance from ML Model
        feature_importance_data = {}
        rmse = 0
        try:
            artifacts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_models', 'model_artifacts.json')
            if os.path.exists(artifacts_path):
                with open(artifacts_path, 'r') as f:
                    artifacts = json.load(f)
                    feature_importance_data = artifacts.get('feature_importances', {})
                    rmse = artifacts.get('rmse', 0)
        except Exception as e:
            pass

        context = {
            'dept_labels': json.dumps(dept_labels),
            'dept_data': json.dumps(dept_data),
            'doc_labels': json.dumps(doc_labels),
            'doc_avg_times': json.dumps(doc_avg_times),
            'doc_efficiency': json.dumps(doc_efficiency),
            'hour_labels': json.dumps(list(hour_counts.keys())),
            'hour_data': json.dumps(list(hour_counts.values())),
            'peak_hour': f"{peak_hour}:00",
            'feature_importances': json.dumps(feature_importance_data),
            'rmse': rmse,
        }

        return render(request, self.template_name, context)
