from rest_framework import serializers
from .models import ClinicalRecord, LabResult, RadiologyReport


class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = ["id", "test_name", "loinc_code", "result_value", "reference_range", 
                  "unit", "is_abnormal", "result_file", "performed_by", "created_at"]


class RadiologyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologyReport
        fields = ["id", "study_type", "body_part", "findings", "impression", 
                  "images", "dicom_study_uid", "radiologist", "created_at"]


class ClinicalRecordSerializer(serializers.ModelSerializer):
    lab_results = LabResultSerializer(many=True, read_only=True)
    radiology_reports = RadiologyReportSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)

    class Meta:
        model = ClinicalRecord
        fields = [
            "id", "patient", "patient_name", "consultation", "record_date",
            "record_type", "diagnosis", "treatment_plan", "notes", "allergies",
            "lab_tests", "radiology_reports", "attachments", "lab_results",
            "recorded_by", "created_at"
        ]

    def create(self, validated_data):
        record = ClinicalRecord(**validated_data)
        # Encrypt fields
        record.diagnosis = validated_data.get("diagnosis", "")
        record.treatment_plan = validated_data.get("treatment_plan", "")
        record.notes = validated_data.get("notes", "")
        record.allergies = validated_data.get("allergies", "")
        record.save()
        return record
