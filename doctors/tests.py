from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import DoctorProfile, LabProfile
from lab.models import LabOrder
from patients.models import Patient
from queues.models import QueueSlot


User = get_user_model()


class DoctorDepartmentQueueTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='cardio_doctor',
            password='StrongPass123!',
            role='DOCTOR',
        )
        DoctorProfile.objects.filter(user=self.doctor).update(department='CARDIOLOGY')

        self.cardio_patient = Patient.objects.create(name='Cardio Patient', phone='9000000001')
        self.general_patient = Patient.objects.create(name='General Patient', phone='9000000002')

    def test_doctor_queue_only_shows_doctor_department_patients(self):
        cardio_slot = QueueSlot.objects.create(
            patient=self.cardio_patient,
            department='CARDIOLOGY',
        )
        QueueSlot.objects.create(
            patient=self.general_patient,
            department='GENERAL',
        )
        self.client.force_login(self.doctor)

        response = self.client.get(reverse('doctors:queue'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['waiting_patients']), [cardio_slot])

    @patch('doctors.views.broadcast_queue_update')
    def test_doctor_cannot_accept_patient_from_another_department(self, broadcast_queue_update):
        general_slot = QueueSlot.objects.create(
            patient=self.general_patient,
            department='GENERAL',
        )
        self.client.force_login(self.doctor)

        response = self.client.post(
            reverse('doctors:queue'),
            {
                'action': 'accept',
                'queue_slot_id': general_slot.id,
            },
        )

        general_slot.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(general_slot.status, 'WAITING')
        self.assertIsNone(general_slot.doctor)
        broadcast_queue_update.assert_not_called()

    def test_doctor_can_assign_lab_order_to_specific_lab(self):
        lab_user = User.objects.create_user(
            username='blood_lab_for_doctor',
            password='StrongPass123!',
            role='LAB',
        )
        LabProfile.objects.filter(user=lab_user).update(department='BLOOD')
        self.client.force_login(self.doctor)

        response = self.client.post(
            reverse('doctors:create_lab_order', args=[self.cardio_patient.id]),
            {
                'test_type': 'BLOOD',
                'assigned_lab': lab_user.id,
                'notes': 'CBC',
            },
        )

        self.assertEqual(response.status_code, 302)
        order = LabOrder.objects.get(patient=self.cardio_patient)
        self.assertEqual(order.assigned_lab, lab_user)

    def test_doctor_cannot_assign_lab_order_to_other_department_lab(self):
        lab_user = User.objects.create_user(
            username='urine_lab_for_doctor',
            password='StrongPass123!',
            role='LAB',
        )
        LabProfile.objects.filter(user=lab_user).update(department='URINE')
        self.client.force_login(self.doctor)

        response = self.client.post(
            reverse('doctors:create_lab_order', args=[self.cardio_patient.id]),
            {
                'test_type': 'BLOOD',
                'assigned_lab': lab_user.id,
                'notes': 'CBC',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(LabOrder.objects.filter(patient=self.cardio_patient).exists())
