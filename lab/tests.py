from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import DoctorProfile, LabProfile
from lab.models import LabOrder
from patients.models import Patient


User = get_user_model()


class LabDepartmentAccessTests(TestCase):
    def setUp(self):
        self.lab_user = User.objects.create_user(
            username='blood_lab',
            password='StrongPass123!',
            role='LAB',
        )
        LabProfile.objects.filter(user=self.lab_user).update(department='BLOOD')
        self.other_lab_user = User.objects.create_user(
            username='other_blood_lab',
            password='StrongPass123!',
            role='LAB',
        )
        LabProfile.objects.filter(user=self.other_lab_user).update(department='BLOOD')

        self.cardio_doctor = User.objects.create_user(
            username='cardio_doctor_lab',
            password='StrongPass123!',
            role='DOCTOR',
        )
        DoctorProfile.objects.filter(user=self.cardio_doctor).update(department='CARDIOLOGY')

        self.general_doctor = User.objects.create_user(
            username='general_doctor_lab',
            password='StrongPass123!',
            role='DOCTOR',
        )
        DoctorProfile.objects.filter(user=self.general_doctor).update(department='GENERAL')

        self.patient = Patient.objects.create(name='Lab Patient', phone='9000000011')
        self.cardio_order = LabOrder.objects.create(
            patient=self.patient,
            doctor=self.cardio_doctor,
            test_type='BLOOD',
        )
        self.general_order = LabOrder.objects.create(
            patient=self.patient,
            doctor=self.general_doctor,
            test_type='URINE',
        )

    def test_lab_dashboard_only_shows_assigned_test_type_orders(self):
        self.client.force_login(self.lab_user)

        response = self.client.get(reverse('lab:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['pending_orders']), [self.cardio_order])

    def test_lab_order_list_only_shows_assigned_test_type_orders(self):
        self.client.force_login(self.lab_user)

        response = self.client.get(reverse('lab:order_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['orders']), [self.cardio_order])

    def test_lab_cannot_open_other_department_order(self):
        self.client.force_login(self.lab_user)

        response = self.client.get(reverse('lab:order_detail', args=[self.general_order.id]))

        self.assertEqual(response.status_code, 404)

    def test_central_lab_without_department_sees_all_orders(self):
        central_lab = User.objects.create_user(
            username='central_lab',
            password='StrongPass123!',
            role='LAB',
        )
        self.client.force_login(central_lab)

        response = self.client.get(reverse('lab:order_list'))

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            [order.id for order in response.context['orders']],
            [self.cardio_order.id, self.general_order.id],
        )

    def test_assigned_lab_order_is_visible_only_to_specific_lab(self):
        assigned_order = LabOrder.objects.create(
            patient=self.patient,
            doctor=self.cardio_doctor,
            assigned_lab=self.lab_user,
            test_type='XRAY',
        )
        self.client.force_login(self.lab_user)

        assigned_response = self.client.get(reverse('lab:order_list'))

        self.assertEqual(assigned_response.status_code, 200)
        self.assertIn(assigned_order, list(assigned_response.context['orders']))

        self.client.force_login(self.other_lab_user)
        other_response = self.client.get(reverse('lab:order_list'))

        self.assertEqual(other_response.status_code, 200)
        self.assertNotIn(assigned_order, list(other_response.context['orders']))

    def test_other_lab_cannot_open_assigned_order(self):
        assigned_order = LabOrder.objects.create(
            patient=self.patient,
            doctor=self.cardio_doctor,
            assigned_lab=self.lab_user,
            test_type='XRAY',
        )
        self.client.force_login(self.other_lab_user)

        response = self.client.get(reverse('lab:order_detail', args=[assigned_order.id]))

        self.assertEqual(response.status_code, 404)

    def test_central_lab_cannot_see_order_assigned_to_another_lab(self):
        assigned_order = LabOrder.objects.create(
            patient=self.patient,
            doctor=self.cardio_doctor,
            assigned_lab=self.lab_user,
            test_type='XRAY',
        )
        central_lab = User.objects.create_user(
            username='central_lab_assigned',
            password='StrongPass123!',
            role='LAB',
        )
        self.client.force_login(central_lab)

        response = self.client.get(reverse('lab:order_list'))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(assigned_order, list(response.context['orders']))
