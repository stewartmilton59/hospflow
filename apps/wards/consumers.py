"""WebSocket consumers for real-time ward data"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class BedOccupancyConsumer(AsyncWebsocketConsumer):
    """Real-time bed occupancy updates via WebSocket"""

    async def connect(self):
        self.ward_id = self.scope["url_route"]["kwargs"]["ward_id"]
        self.room_group_name = f"ward_{self.ward_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial bed status
        beds = await self.get_bed_data()
        await self.send(text_data=json.dumps({"type": "initial", "beds": beds}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Handle client messages if needed
        pass

    async def bed_update(self, event):
        """Handle bed status update from channel layer"""
        await self.send(text_data=json.dumps({
            "type": "bed_update",
            "bed_id": event["bed_id"],
            "status": event["status"]
        }))

    @database_sync_to_async
    def get_bed_data(self):
        from .models import Bed
        beds = Bed.objects.filter(ward_id=self.ward_id).values(
            "id", "bed_number", "bed_type", "status"
        )
        return list(beds)
