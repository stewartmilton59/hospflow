from rest_framework import serializers
from .models import DHIS2Report, DHIS2DataElement


class DHIS2DataElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DHIS2DataElement
        fields = ["id", "dhis2_uid", "name", "code", "mtuha_book", "mtuha_indicator"]


class DHIS2ReportSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source="facility.name", read_only=True)

    class Meta:
        model = DHIS2Report
        fields = ["id", "report_period", "facility", "facility_name", "report_type", 
                  "data_values", "status", "dhis2_response", "created_at"]
