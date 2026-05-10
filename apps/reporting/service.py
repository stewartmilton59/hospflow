"""DHIS2 Integration Service"""
import requests
from typing import Dict, List
from django.conf import settings
from django.db.models import Count, Sum, Avg
from django.utils import timezone

from .models import DHIS2DataElement, DHIS2Report
from apps.consultations.models import Consultation
from apps.patients.models import Patient
from apps.inventory.models import InventoryBatch


class DHIS2Service:
    """Service for DHIS2 data exchange and MTUHA reporting"""

    def __init__(self):
        self.base_url = settings.DHIS2_BASE_URL
        self.username = settings.DHIS2_USERNAME
        self.password = settings.DHIS2_PASSWORD
        self.org_unit_id = settings.DHIS2_ORG_UNIT_ID

    def _auth(self):
        return (self.username, self.password)

    def submit_data_value_set(self, data_values: List[Dict], period: str) -> Dict:
        """Submit aggregated data to DHIS2"""
        payload = {
            "dataSet": "MTUHA_HOSPITAL",
            "completeDate": timezone.now().strftime("%Y-%m-%d"),
            "period": period,
            "orgUnit": self.org_unit_id,
            "dataValues": data_values
        }

        try:
            response = requests.post(
                f"{self.base_url}/dataValueSets",
                json=payload,
                auth=self._auth(),
                timeout=60
            )
            response.raise_for_status()
            return {"success": True, "response": response.json()}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def create_tracked_entity(self, patient, disease_code: str) -> Dict:
        """Register outbreak case in DHIS2 Tracker (e-IDSR)"""
        payload = {
            "trackedEntityType": "PERSON",
            "orgUnit": self.org_unit_id,
            "attributes": [
                {"attribute": "NIN", "value": patient.nida_nin or ""},
                {"attribute": "FIRST_NAME", "value": patient.first_name},
                {"attribute": "LAST_NAME", "value": patient.last_name},
            ],
            "enrollments": [{
                "orgUnit": self.org_unit_id,
                "program": "eIDSR_PROGRAM",
                "enrollmentDate": timezone.now().strftime("%Y-%m-%d"),
                "incidentDate": timezone.now().strftime("%Y-%m-%d"),
                "events": [{
                    "programStage": "CASE_DETECTION",
                    "orgUnit": self.org_unit_id,
                    "eventDate": timezone.now().strftime("%Y-%m-%d"),
                    "dataValues": [
                        {"dataElement": "DISEASE_CODE", "value": disease_code},
                        {"dataElement": "FACILITY_CODE", "value": settings.NHIF_FACILITY_CODE},
                    ]
                }]
            }]
        }

        try:
            response = requests.post(
                f"{self.base_url}/trackedEntityInstances",
                json=payload,
                auth=self._auth(),
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "tracked_entity": response.json().get("response", {}).get("importSummaries", [{}])[0].get("reference")}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def generate_mtuha_book_10(self, facility, year: int, quarter: int) -> Dict:
        """Generate MTUHA Book 10 - Hospital Report"""
        from django.db.models import Q

        start_date = timezone.datetime(year, (quarter - 1) * 3 + 1, 1)
        if quarter == 4:
            end_date = timezone.datetime(year + 1, 1, 1)
        else:
            end_date = timezone.datetime(year, quarter * 3 + 1, 1)

        # OPD Visits
        opd_visits = Consultation.objects.filter(
            facility=facility,
            visit_date__gte=start_date,
            visit_date__lt=end_date
        ).count()

        # Maternal Health
        maternal_visits = Patient.objects.filter(
            consultations__facility=facility,
            consultations__visit_date__gte=start_date,
            consultations__visit_date__lt=end_date,
            gender="female"
        ).count()

        # Stock-out days
        stock_outs = InventoryBatch.objects.filter(
            facility=facility,
            quantity_remaining=0,
            updated_at__gte=start_date,
            updated_at__lt=end_date
        ).count()

        report_data = {
            "period": f"{year}Q{quarter}",
            "facility": facility.name,
            "indicators": {
                "OPD_VISITS": opd_visits,
                "MATERNAL_VISITS": maternal_visits,
                "STOCK_OUT_DAYS": stock_outs,
            }
        }

        return report_data


class eIDSRService:
    """Electronic Integrated Disease Surveillance and Response"""

    OUTBREAK_PRONE_DISEASES = [
        "A00",  # Cholera
        "A20",  # Plague
        "B20",  # HIV-related
        "A90",  # Dengue
        "B50",  # Malaria (severe)
    ]

    @classmethod
    def check_notifiable(cls, icd10_code: str) -> bool:
        """Check if diagnosis requires immediate e-IDSR notification"""
        return any(icd10_code.startswith(disease) for disease in cls.OUTBREAK_PRONE_DISEASES)

    @classmethod
    def trigger_alert(cls, consultation):
        """Automatically trigger e-IDSR alert for outbreak-prone diseases"""
        if not consultation.is_notifiable_disease:
            return None

        service = DHIS2Service()
        result = service.create_tracked_entity(
            patient=consultation.patient,
            disease_code=consultation.primary_diagnosis.code if consultation.primary_diagnosis else "UNKNOWN"
        )

        # Also send SMS alert to district health officer
        from apps.notifications.tasks import send_sms_async
        send_sms_async.delay(
            phone="+255700000000",  # DHO number
            message=f"ALERT: Notifiable disease detected at {consultation.facility.name}. "
                    f"Patient: {consultation.patient.get_full_name()}, "
                    f"Disease: {consultation.primary_diagnosis.code}",
            notification_type="alert"
        )

        return result
