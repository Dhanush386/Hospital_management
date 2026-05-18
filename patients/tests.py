from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import DoctorProfile
from doctors.models import DoctorAvailability
from patients.models import Patient
from queues.models import QueueSlot


User = get_user_model()


class PatientQueueFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient1',
            password='StrongPass123!',
            role='PATIENT',
            phone_number='9999999999',
        )
        self.patient = Patient.objects.create(
            user=self.user,
            name='Patient One',
            phone='9999999999',
        )

    def test_queue_status_serializes_model_property(self):
        QueueSlot.objects.create(patient=self.patient, department='GENERAL')
        self.client.force_login(self.user)

        response = self.client.get(reverse('patients:queue_status'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['queue_slots']), 1)
        self.assertEqual(payload['queue_slots'][0]['department'], 'GENERAL')
        self.assertEqual(payload['queue_slots'][0]['status'], 'WAITING')
        self.assertEqual(payload['queue_slots'][0]['position_in_queue'], 1)

    def test_patient_can_join_queue_multiple_times(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('patients:join_queue'),
            {'department': 'CARDIOLOGY'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            QueueSlot.objects.filter(patient=self.patient, department='CARDIOLOGY').exists()
        )

        second_response = self.client.post(
            reverse('patients:join_queue'),
            {'department': 'GENERAL'},
            follow=True,
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(
            QueueSlot.objects.filter(patient=self.patient, status='WAITING').count(),
            2,
        )

    def test_queue_tokens_increment_within_department_for_the_same_queue_day(self):
        first_slot = QueueSlot.objects.create(patient=self.patient, department='CARDIOLOGY')
        second_slot = QueueSlot.objects.create(patient=self.patient, department='CARDIOLOGY')

        self.assertEqual(first_slot.token_number, 1)
        self.assertEqual(second_slot.token_number, 2)
        self.assertEqual(first_slot.token_date, second_slot.token_date)

    def test_queue_tokens_are_separate_for_each_department(self):
        cardiology_slot = QueueSlot.objects.create(patient=self.patient, department='CARDIOLOGY')
        general_slot = QueueSlot.objects.create(patient=self.patient, department='GENERAL')

        self.assertEqual(cardiology_slot.token_number, 1)
        self.assertEqual(general_slot.token_number, 1)
        self.assertEqual(cardiology_slot.token_date, general_slot.token_date)

    def test_queue_tokens_reset_at_four_am(self):
        tz = ZoneInfo('Asia/Kolkata')

        with patch('queues.models.timezone.now', return_value=datetime(2026, 4, 28, 3, 59, tzinfo=tz)):
            before_reset = QueueSlot.objects.create(patient=self.patient, department='CARDIOLOGY')
            also_before_reset = QueueSlot.objects.create(patient=self.patient, department='CARDIOLOGY')

        with patch('queues.models.timezone.now', return_value=datetime(2026, 4, 28, 4, 0, tzinfo=tz)):
            after_reset = QueueSlot.objects.create(patient=self.patient, department='ORTHOPEDICS')

        self.assertEqual(before_reset.token_number, 1)
        self.assertEqual(also_before_reset.token_number, 2)
        self.assertEqual(before_reset.token_date.isoformat(), '2026-04-27')
        self.assertEqual(after_reset.token_number, 1)
        self.assertEqual(after_reset.token_date.isoformat(), '2026-04-28')

    def test_department_availability_reports_online_doctor(self):
        doctor = User.objects.create_user(
            username='doctor1',
            password='StrongPass123!',
            role='DOCTOR',
            first_name='Asha',
            last_name='Rao',
        )
        DoctorProfile.objects.filter(user=doctor).update(department='CARDIOLOGY')
        DoctorAvailability.objects.create(doctor=doctor, is_online=True)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('patients:department_availability'),
            {'department': 'CARDIOLOGY'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['is_available'])
        self.assertEqual(payload['available_count'], 1)
        self.assertEqual(payload['doctors'], ['Asha Rao'])

    def test_department_availability_reports_offline_doctor(self):
        doctor = User.objects.create_user(
            username='doctor2',
            password='StrongPass123!',
            role='DOCTOR',
        )
        DoctorProfile.objects.filter(user=doctor).update(department='GENERAL')
        DoctorAvailability.objects.create(doctor=doctor, is_online=False)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('patients:department_availability'),
            {'department': 'GENERAL'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['is_available'])
        self.assertEqual(payload['total_doctors'], 1)
        self.assertEqual(payload['available_count'], 0)

    def test_queue_status_reflects_assigned_doctor_offline_toggle(self):
        doctor = User.objects.create_user(
            username='doctor3',
            password='StrongPass123!',
            role='DOCTOR',
            first_name='Meera',
            last_name='Nair',
        )
        DoctorAvailability.objects.create(doctor=doctor, is_online=True)
        QueueSlot.objects.create(
            patient=self.patient,
            department='GENERAL',
            status='IN_PROGRESS',
            doctor=doctor,
        )
        self.client.force_login(self.user)

        online_response = self.client.get(reverse('patients:queue_status'))
        self.assertEqual(online_response.status_code, 200)
        online_slot = online_response.json()['queue_slots'][0]
        self.assertTrue(online_slot['doctor_is_online'])
        self.assertEqual(online_slot['doctor_status_display'], 'Online')
        self.assertEqual(online_slot['doctor_status_detail'], 'Dr. Meera Nair')

        DoctorAvailability.objects.filter(doctor=doctor).update(is_online=False)
        offline_response = self.client.get(reverse('patients:queue_status'))
        self.assertEqual(offline_response.status_code, 200)
        offline_slot = offline_response.json()['queue_slots'][0]
        self.assertFalse(offline_slot['doctor_is_online'])
        self.assertEqual(offline_slot['doctor_status_display'], 'Offline')
