"""Celery tasks for notifications"""
from celery import shared_task
from django.utils import timezone

from .sms_providers import SMSFactory
from .models import NotificationLog, AppointmentReminder


@shared_task(bind=True, max_retries=3)
def send_sms_async(self, phone: str, message: str, notification_type: str = "alert", patient_id: str = None):
    """Send SMS asynchronously via configured provider"""
    provider = SMSFactory.get_provider()
    result = provider.send_sms(phone, message)

    # Log the notification
    log = NotificationLog.objects.create(
        recipient_id=patient_id,
        recipient_number=phone,
        channel="sms",
        notification_type=notification_type,
        message=message,
        message_id=result.get("message_id", ""),
        provider=result.get("provider", ""),
        status="sent" if result["success"] else "failed",
        failed_reason=result.get("error", "")
    )

    if not result["success"]:
        # Retry with exponential backoff
        raise self.retry(countdown=60 * (2 ** self.request.retries), exc=Exception(result.get("error")))

    return {"success": True, "log_id": str(log.id)}


@shared_task
def send_appointment_reminders():
    """Send appointment reminders 1 day before visit"""
    from django.utils import timezone

    tomorrow = timezone.now() + timezone.timedelta(days=1)
    reminders = AppointmentReminder.objects.filter(
        scheduled_time__date=tomorrow.date(),
        sent=False
    ).select_related("consultation", "consultation__patient")

    sent_count = 0
    for reminder in reminders:
        patient = reminder.consultation.patient
        message = (
            f"Habari {patient.first_name}, unakumbushwa kuhusu tembeleo lako "
            f"la hospitali kesho {reminder.consultation.visit_date.strftime('%H:%M')}. "
            f"Tafadhali fika kwa wakati. Asante."
        )

        send_sms_async.delay(
            phone=patient.phone_number,
            message=message,
            notification_type="appointment_reminder",
            patient_id=str(patient.unique_id)
        )

        reminder.sent = True
        reminder.sent_at = timezone.now()
        reminder.save()
        sent_count += 1

    return f"Queued {sent_count} appointment reminders"


@shared_task
def send_lab_alert(patient_id: str, phone: str):
    """Notify patient when lab results are ready"""
    message = (
        "Habari, matokeo ya vipimo vyako vya hospitali vimekamilika. "
        "Tafadhali tembelea kituo cha afya kwa maelezo zaidi."
    )
    return send_sms_async.delay(phone=phone, message=message, notification_type="lab_result", patient_id=patient_id)


@shared_task
def send_otp(phone: str, otp_code: str):
    """Send OTP for 2FA or high-value transactions"""
    message = f"HospFlow OTP yako ni: {otp_code}. Usiambie mtu. Muda wake ni dakika 5."
    return send_sms_async.delay(phone=phone, message=message, notification_type="otp")


@shared_task
def send_e_receipt(phone: str, receipt_data: dict):
    """Send fiscal receipt details via SMS"""
    message = (
        f"HospFlow Receipt: RCPT-{receipt_data.get('rctnum')} "
        f"TZS {receipt_data.get('total')} "
        f"Date: {receipt_data.get('date')} "
        f"Asante kwa kutumia huduma zetu."
    )
    return send_sms_async.delay(phone=phone, message=message, notification_type="receipt")
