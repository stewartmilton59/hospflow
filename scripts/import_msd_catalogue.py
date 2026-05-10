"""Import MSD Price Catalogue"""
import csv
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hospflow.settings")
django.setup()

from apps.inventory.models import InventoryItem


def import_msd_catalogue(file_path):
    """Import MSD price catalogue CSV"""
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            item, created = InventoryItem.objects.update_or_create(
                msd_code=row["item_code"],
                defaults={
                    "name": row["item_name"],
                    "generic_name": row.get("generic_name", ""),
                    "category": row.get("category", "medicine"),
                    "ven_classification": row.get("ven", "essential"),
                    "msd_unit_price": row.get("unit_price", 0),
                    "selling_price": row.get("selling_price", 0),
                }
            )
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} items...")

    print(f"Import complete. Total items: {count}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python import_msd_catalogue.py <csv_file_path>")
        sys.exit(1)

    import_msd_catalogue(sys.argv[1])
