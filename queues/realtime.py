from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_queue_refresh(update_type, payload=None):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    data = {
        'event': 'queue_update',
        'update_type': update_type,
    }
    if payload:
        data.update(payload)

    async_to_sync(channel_layer.group_send)(
        'queue_updates',
        {
            'type': 'queue_update',
            'data': data,
        },
    )


def broadcast_queue_update(event_type, queue_slot):
    broadcast_queue_refresh(
        event_type,
        {
            'queue_slot_id': queue_slot.id,
            'status': queue_slot.status,
            'department': queue_slot.department,
            'patient_id': queue_slot.patient_id,
            'patient_name': queue_slot.patient.name,
            'patient_token': queue_slot.token_number,
            'token_number': queue_slot.token_number,
            'token_date': queue_slot.token_date.isoformat(),
            'doctor_id': queue_slot.doctor_id,
            'predicted_wait_time': queue_slot.predicted_wait_time,
            'actual_wait_time_mins': getattr(queue_slot, 'actual_wait_time_mins', None),
            'prediction_error_mins': getattr(queue_slot, 'prediction_error_mins', None),
        },
    )
