"""Celery tasks for DHIS2 reporting"""
from celery import shared_task
from django.utils import timezone

from .service import DHIS2Service
from .models import DHIS2Report
from apps.accounts.models import Facility


@shared_task
def submit_monthly_mtuha_report(facility_id, period):
    """Automated monthly MTUHA report submission to DHIS2"""
    try:
        facility = Facility.objects.get(id=facility_id)
    except Facility.DoesNotExist:
        return {"error": "Facility not found"}

    service = DHIS2Service()

    # Generate report data
    year = int(period[:4])
    quarter = (int(period[4:6]) - 1) // 3 + 1
    report_data = service.generate_mtuha_book_10(facility, year, quarter)

    # Map to DHIS2 data elements
    data_values = [
        {"dataElement": "OPD_VISITS", "value": report_data["indicators"]["OPD_VISITS"]},
        {"dataElement": "MATERNAL_VISITS", "value": report_data["indicators"]["MATERNAL_VISITS"]},
        {"dataElement": "STOCK_OUTS", "value": report_data["indicators"]["STOCK_OUT_DAYS"]},
    ]

    # Submit to DHIS2
    result = service.submit_data_value_set(data_values, period)

    # Save report record
    report, _ = DHIS2Report.objects.update_or_create(
        report_period=period,
        facility=facility,
        report_type="monthly",
        defaults={
            "data_values": data_values,
            "status": "submitted" if result["success"] else "failed",
            "dhis2_response": result
        }
    )

    return {"success": result["success"], "report_id": str(report.id)}
