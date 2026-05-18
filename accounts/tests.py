from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.forms import UserRegistrationForm
from accounts.models import User


class UserRegistrationFormTests(TestCase):
    def test_registration_creates_patient_account(self):
        form = UserRegistrationForm(
            data={
                'first_name': 'Pat',
                'last_name': 'Ient',
                'username': 'patient1',
                'email': 'patient@example.com',
                'phone_number': '9999999999',
                'age': 24,
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.role, 'PATIENT')
        self.assertEqual(user.patient_profile.age, 24)

    def test_patient_registration_requires_age(self):
        form = UserRegistrationForm(
            data={
                'first_name': 'Pat',
                'last_name': 'Ient',
                'username': 'patient_no_age',
                'email': 'patient-no-age@example.com',
                'phone_number': '9999999999',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('age', form.errors)

    def test_patient_registration_saves_age_to_profile(self):
        form = UserRegistrationForm(
            data={
                'first_name': 'Pat',
                'last_name': 'Ient',
                'username': 'patient_with_age',
                'email': 'patient-with-age@example.com',
                'phone_number': '9999999999',
                'age': 27,
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.patient_profile.age, 27)

    @patch('accounts.views.broadcast_queue_refresh')
    def test_registration_broadcasts_doctor_queue_refresh(self, broadcast_queue_refresh):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'first_name': 'Pat',
                'last_name': 'Refresh',
                'username': 'patient_refresh',
                'email': 'patient-refresh@example.com',
                'phone_number': '9999999999',
                'age': 31,
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        user = User.objects.get(username='patient_refresh')
        self.assertEqual(response.status_code, 302)
        broadcast_queue_refresh.assert_called_once_with(
            'patient_registered',
            {
                'patient_id': user.patient_profile.id,
                'patient_name': user.patient_profile.name,
            },
        )

    def test_admin_created_lab_user_gets_lab_profile(self):
        lab_user = User.objects.create_user(
            username='labtech1',
            password='StrongPass123!',
            role='LAB',
        )

        self.assertTrue(hasattr(lab_user, 'lab_profile'))
