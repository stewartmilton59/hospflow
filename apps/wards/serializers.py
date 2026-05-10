"""Wards Serializers"""
from rest_framework import serializers
from .models import Ward, Bed, Admission, NursingNote, MedicationAdministrationRecord


class WardSerializer(serializers.ModelSerializer):
    available_beds = serializers.IntegerField(read_only=True)
    occupancy_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Ward
        fields = ["id", "name", "code", "ward_type", "floor", "capacity", "available_beds", "occupancy_rate", "is_active"]


class BedSerializer(serializers.ModelSerializer):
    ward_name = serializers.CharField(source="ward.name", read_only=True)

    class Meta:
        model = Bed
        fields = ["id", "ward", "ward_name", "bed_number", "bed_type", "status"]


class AdmissionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    bed_number = serializers.CharField(source="bed.bed_number", read_only=True)
    ward_name = serializers.CharField(source="ward.name", read_only=True)
    days_admitted = serializers.SerializerMethodField()

    class Meta:
        model = Admission
        fields = [
            "id", "patient", "patient_name", "bed", "bed_number", "ward", "ward_name",
            "admission_date", "discharge_date", "status", "admitting_diagnosis",
            "discharge_diagnosis", "discharge_summary", "discharge_disposition",
            "daily_rate", "total_bill", "review_due", "review_overdue", "days_admitted"
        ]

    def get_days_admitted(self, obj):
        from django.utils import timezone
        end = obj.discharge_date or timezone.now()
        return (end - obj.admission_date).days or 1


class NursingNoteSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True)

    class Meta:
        model = NursingNote
        fields = ["id", "admission", "note", "vital_temperature", "vital_blood_pressure",
                  "vital_pulse", "vital_respiration", "vital_spo2", "recorded_by", "recorded_by_name", "created_at"]


class MARSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="prescription.medication.name", read_only=True)
    administered_by_name = serializers.CharField(source="administered_by.get_full_name", read_only=True)

    class Meta:
        model = MedicationAdministrationRecord
        fields = [
            "id", "admission", "prescription", "medication_name", "scheduled_time",
            "administered_time", "dose_given", "route", "administered_by", "administered_by_name",
            "notes", "missed", "missed_reason"
        ]
