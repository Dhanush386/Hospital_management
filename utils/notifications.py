"""
Notification utilities for real-time updates and SMS integration.
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .sms_service import SMSService


def notify_queue_update(queue_slot):
    """Send real-time queue update to all connected clients."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'queue_updates',
        {
            'type': 'queue_update',
            'data': {
                'event': 'queue_update',
                'slot_id': queue_slot.id,
                'patient_token': queue_slot.patient.token_id,
                'department': queue_slot.department,
                'status': queue_slot.status,
                'position': queue_slot.position_in_queue if hasattr(queue_slot, 'position_in_queue') else None,
            }
        }
    )


def notify_lab_update(lab_order, event_type='updated'):
    """Send real-time lab order update."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'lab_updates',
        {
            'type': 'lab_update',
            'data': {
                'event': event_type,
                'order_id': lab_order.id,
                'patient_id': lab_order.patient.id,
                'patient_name': lab_order.patient.name,
                'test_name': lab_order.test_name,
                'status': lab_order.status,
            }
        }
    )

    if event_type == 'completed' and lab_order.patient.phone:
        SMSService.send_lab_ready_notification(
            lab_order.patient.phone,
            lab_order.patient.name,
            lab_order.test_name
        )


def notify_pharmacy_update(prescription, event_type='updated'):
    """Send real-time pharmacy update."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'pharmacy_updates',
        {
            'type': 'pharmacy_update',
            'data': {
                'event': event_type,
                'prescription_id': prescription.id,
                'patient_id': prescription.patient.id,
                'patient_name': prescription.patient.name,
                'status': prescription.status,
            }
        }
    )

    if event_type == 'ready' and prescription.patient.phone:
        SMSService.send_prescription_ready_notification(
            prescription.patient.phone,
            prescription.patient.name
        )


def notify_patient(patient, message_type, extra_data=None):
    """Send notification to specific patient."""
    if not patient.user:
        return

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'patient_{patient.user.id}',
        {
            'type': 'patient_notification',
            'data': {
                'type': message_type,
                'message': extra_data or {},
            }
        }
    )
