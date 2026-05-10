from django.urls import path
from .views import (
    InventoryItemListView, InventoryBatchListView,
    dispense_medication, receive_stock, StockAdjustmentListCreateView
)

urlpatterns = [
    path("items/", InventoryItemListView.as_view(), name="inventory-items"),
    path("batches/", InventoryBatchListView.as_view(), name="inventory-batches"),
    path("dispense/", dispense_medication, name="dispense"),
    path("receive/", receive_stock, name="receive-stock"),
    path("adjustments/", StockAdjustmentListCreateView.as_view(), name="stock-adjustments"),
]
