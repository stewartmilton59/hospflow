"""WebSocket routing for real-time ward dashboards"""
from django.urls import re_path
from .consumers import BedOccupancyConsumer

websocket_urlpatterns = [
    re_path(r"ws/wards/(?P<ward_id>[0-9a-f-]+)/$", BedOccupancyConsumer.as_asgi()),
]
