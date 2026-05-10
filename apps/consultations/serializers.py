"""Consultation Serializers"""
from rest_framework import serializers
from .models import Consultation, Prescription, ICD10Code


class ICD10CodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ICD10Code
        fields = ["id", "code", "description", "category", "is_sdh"]


class PrescriptionSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.name", read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id", "medication", "medication_name", "dosage", "frequency",
            "duration_days", "quantity_prescribed", "instructions",
            "dispensed", "dispensed_by", "dispensed_at"
        ]


class ConsultationListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    primary_diagnosis_code = serializers.CharField(source="primary_diagnosis.code", read_only=True)

    class Meta:
        model = Consultation
        fields = [
            "id", "patient", "patient_name", "doctor", "doctor_name",
            "visit_date", "status", "priority", "primary_diagnosis_code", "disposition"
        ]


class ConsultationDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    primary_diagnosis = ICD10CodeSerializer(read_only=True)
    secondary_diagnoses = ICD10CodeSerializer(many=True, read_only=True)
    sdoh_codes = ICD10CodeSerializer(many=True, read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)

    class Meta:
        model = Consultation
        fields = [
            "id", "patient", "patient_name", "doctor", "doctor_name", "facility",
            "visit_date", "status", "priority", "visit_type",
            "vital_temperature", "vital_blood_pressure_sys", "vital_blood_pressure_dia",
            "vital_heart_rate", "vital_respiratory_rate", "vital_oxygen_saturation",
            "vital_weight_kg", "vital_height_cm", "vital_bmi",
            "chief_complaint", "history_of_present_illness", 
            "physical_examination", "assessment_and_plan",
            "primary_diagnosis", "secondary_diagnoses", "sdoh_codes",
            "disposition", "referral_facility",
            "consultation_fee", "is_nhif_claimable",
            "is_notifiable_disease", "prescriptions",
            "created_at", "updated_at"
        ]
