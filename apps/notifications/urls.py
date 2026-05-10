from django.urls import path
from .views import NotificationLogListView, send_test_sms, delivery_webhook

urlpatterns = [
    path("logs/", NotificationLogListView.as_view(), name="notification-logs"),
    path("send/", send_test_sms, name="send-sms"),
    path("dlr/", delivery_webhook, name="delivery-webhook"),
]
