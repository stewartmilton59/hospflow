"""Patient Serializers"""
from rest_framework import serializers
from .models import Patient, NextOfKin, ConsentLog


class NextOfKinSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextOfKin
        fields = ["id", "full_name", "relationship", "phone_number", "email", "address", "is_primary"]


class ConsentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentLog
        fields = ["id", "action", "method", "performed_by", "timestamp"]
        read_only_fields = ["timestamp"]


class PatientListSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(source="get_age", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "unique_id", "patient_number", "first_name", "last_name", 
            "gender", "date_of_birth", "age", "phone_number", "facility", "is_active"
        ]


class PatientDetailSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(source="get_age", read_only=True)
    next_of_kin = NextOfKinSerializer(many=True, read_only=True)
    consent_logs = ConsentLogSerializer(many=True, read_only=True)
    can_process = serializers.BooleanField(source="can_process_data", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "unique_id", "patient_number", "nida_nin", "biometric_verified",
            "first_name", "middle_name", "last_name", "date_of_birth", "age",
            "gender", "marital_status", "phone_number", "email",
            "region", "district", "ward", "village_street",
            "nhif_card_number", "insurance_scheme", "insurance_expiry",
            "occupation", "education_level",
            "consent_status", "consent_date", "consent_method", 
            "consent_withdrawn", "can_process",
            "facility", "registered_by", "is_active", "deceased",
            "next_of_kin", "consent_logs", "created_at", "updated_at"
        ]
        read_only_fields = ["unique_id", "patient_number", "created_at", "updated_at"]


class PatientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "nida_nin", "first_name", "middle_name", "last_name",
            "date_of_birth", "gender", "marital_status",
            "phone_number", "email", "emergency_contact_name", "emergency_contact_phone",
            "region", "district", "ward", "village_street",
            "nhif_card_number", "insurance_scheme", "occupation", "education_level",
            "facility"
        ]

    def validate_nida_nin(self, value):
        if value and Patient.objects.filter(nida_nin=value).exists():
            raise serializers.ValidationError("Patient with this NIN already exists.")
        return value
