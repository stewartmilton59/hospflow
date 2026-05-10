"""Notifications API Views"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import NotificationLog
from .serializers import NotificationLogSerializer
from .tasks import send_sms_async


class NotificationLogListView(generics.ListAPIView):
    queryset = NotificationLog.objects.all()
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "notification_type", "recipient"]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_test_sms(request):
    """Test SMS endpoint"""
    phone = request.data.get("phone")
    message = request.data.get("message", "Test message from HospFlow")

    if not phone:
        return Response({"error": "Phone number required"}, status=status.HTTP_400_BAD_REQUEST)

    task = send_sms_async.delay(phone=phone, message=message)
    return Response({"task_id": task.id, "status": "queued"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delivery_webhook(request):
    """Handle delivery status webhooks from SMS providers"""
    message_id = request.data.get("message_id")
    status = request.data.get("status")

    if message_id:
        NotificationLog.objects.filter(message_id=message_id).update(
            status=status.lower(),
            delivered_at=timezone.now() if status.lower() == "delivered" else None
        )

    return Response({"status": "ok"})
