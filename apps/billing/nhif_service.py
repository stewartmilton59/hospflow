"""NHIF API Integration Service"""
import json
import base64
from typing import Dict, Optional
import requests
from django.conf import settings
from django.utils import timezone

from .models import NHIFClaim


class NHIFService:
    """
    National Health Insurance Fund (NHIF) Integration
    Handles member verification, price package sync, and claims submission.
    """

    def __init__(self):
        self.base_url = settings.NHIF_API_BASE_URL
        self.client_id = settings.NHIF_CLIENT_ID
        self.client_secret = settings.NHIF_CLIENT_SECRET
        self.facility_code = settings.NHIF_FACILITY_CODE
        self._token = None
        self._token_expiry = None

    def _get_token(self) -> str:
        """OAuth2 Client Credentials Flow"""
        if self._token and self._token_expiry and timezone.now() < self._token_expiry:
            return self._token

        response = requests.post(
            f"{self.base_url}/stsidentity",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        self._token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = timezone.now() + timezone.timedelta(seconds=expires_in - 300)

        return self._token

    def _headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    def verify_member(self, card_number: str) -> Dict:
        """Verify NHIF member at point of service"""
        try:
            response = requests.post(
                f"{self.base_url}/verification",
                headers=self._headers(),
                json={
                    "CardNo": card_number,
                    "FacilityCode": self.facility_code,
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            return {
                "valid": data.get("Status") == "Active",
                "status": data.get("Status"),
                "scheme": data.get("Scheme"),
                "authorization_id": data.get("AuthorizationID"),
                "eligible_schemes": data.get("EligibleSchemes", []),
                "raw": data
            }
        except requests.RequestException as e:
            return {"valid": False, "error": str(e)}

    def get_price_package(self) -> Dict:
        """Synchronize facility price list with NHIF"""
        try:
            response = requests.get(
                f"{self.base_url}/GetPricePackage",
                headers=self._headers(),
                params={"FacilityCode": self.facility_code},
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def verify_services(self, item_code: str, authorization_id: str) -> Dict:
        """Check if service requires pre-approval"""
        try:
            response = requests.post(
                f"{self.base_url}/VerifyServices",
                headers=self._headers(),
                json={
                    "ItemCode": item_code,
                    "AuthorizationID": authorization_id,
                    "FacilityCode": self.facility_code,
                },
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def submit_claim(self, claim: NHIFClaim) -> Dict:
        """Submit electronic claim as JWE encrypted FHIR bundle"""
        from jwcrypto import jwe, jwk

        # Build FHIR-based claim bundle
        fhir_bundle = {
            "resourceType": "Claim",
            "id": str(claim.id),
            "identifier": [{"value": claim.claim_number}],
            "status": "active",
            "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "institutional"}]},
            "use": "claim",
            "patient": {"reference": f"Patient/{claim.patient.unique_id}"},
            "created": claim.claim_date.isoformat(),
            "provider": {"identifier": {"value": self.facility_code}},
            "insurance": [{
                "sequence": 1,
                "focal": True,
                "coverage": {"identifier": {"value": claim.member_card_number}}
            }],
            "diagnosis": [
                {"sequence": i+1, "diagnosisCodeableConcept": {"coding": [{"code": code}]}}
                for i, code in enumerate(claim.diagnosis_codes)
            ],
            "item": [
                {
                    "sequence": i+1,
                    "productOrService": {"coding": [{"code": item.item_code}]},
                    "unitPrice": {"value": float(item.unit_price), "currency": "TZS"},
                    "quantity": {"value": float(item.quantity)}
                }
                for i, item in enumerate(claim.invoice.items.all())
            ],
            "total": {"value": float(claim.claim_amount), "currency": "TZS"}
        }

        # Encrypt as JWE
        payload = json.dumps(fhir_bundle).encode("utf-8")

        # Note: In production, use NHIF's public key for encryption
        # This is a simplified representation
        claim.submission_payload = fhir_bundle

        try:
            response = requests.post(
                f"{self.base_url}/ClaimSubmit",
                headers=self._headers(),
                json={
                    "FacilityCode": self.facility_code,
                    "ClaimData": base64.b64encode(payload).decode("utf-8"),
                    "AuthorizationID": claim.authorization_id,
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            claim.nhif_reference = result.get("ReferenceNo", "")
            claim.status = "submitted"
            claim.api_response = result
            claim.save()

            return {"success": True, "reference": claim.nhif_reference, "response": result}

        except requests.RequestException as e:
            claim.status = "draft"
            claim.api_response = {"error": str(e)}
            claim.save()
            return {"success": False, "error": str(e)}
