"""
SMS Service - Placeholder implementation
In production, integrate with Twilio, AWS SNS, or local SMS gateway
"""
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """Placeholder SMS service for hospital notifications."""

    @staticmethod
    def send_sms(phone_number, message):
        """
        Placeholder method to send SMS.
        In production, integrate with actual SMS provider.
        """
        logger.info(f"[SMS PLACEHOLDER] To: {phone_number}, Message: {message}")
        print(f"\n[SMS SENT]\nTo: {phone_number}\nMessage: {message}\n{'='*50}")
        return True

    @classmethod
    def send_registration_confirmation(cls, phone_number, name, token_id=None):
        """Send registration confirmation SMS."""
        message = f"Welcome {name} to Smart Hospital!"
        if token_id:
            message += f" Your token ID: {token_id}"
        message += " Please save this number for future reference."
        return cls.send_sms(phone_number, message)

    @classmethod
    def send_lab_ready_notification(cls, phone_number, patient_name, test_name):
        """Send lab results ready notification."""
        message = f"Hello {patient_name}, your {test_name} results are ready. Please visit the lab collection center or check online."
        return cls.send_sms(phone_number, message)

    @classmethod
    def send_prescription_ready_notification(cls, phone_number, patient_name):
        """Send prescription ready notification."""
        message = f"Hello {patient_name}, your prescription is ready for collection at the pharmacy."
        return cls.send_sms(phone_number, message)

    @classmethod
    def send_queue_update(cls, phone_number, patient_name, token_id, position, estimated_wait):
        """Send queue status update."""
        message = f"Token {token_id}: Your position in queue is {position}. Estimated wait: {estimated_wait} mins."
        return cls.send_sms(phone_number, message)

    @classmethod
    def send_consultation_reminder(cls, phone_number, patient_name, doctor_name, time):
        """Send consultation reminder."""
        message = f"Hello {patient_name}, your consultation with Dr. {doctor_name} is scheduled at {time}. Please be ready."
        return cls.send_sms(phone_number, message)
