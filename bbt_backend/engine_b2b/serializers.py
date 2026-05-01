from rest_framework import serializers
from engine_b2b.models import (
    PartnerProfile, PartnerStaff, StaffLeave, StaffSalaryRecord,
    PartnerGuestRecord, PartnerRoom, RoomAssignment, PartnerTask,
    PartnerVehicle, VehicleDriverLink, VehicleTripRecord,
    PartnerCommodity, CommodityAssignment, PartnerClosureDate,
    ActivityCategoryEligibility, PartnerActivityCertification,
    ActivityServiceAssignment,
)


class PartnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PartnerProfile
        fields = ['id', 'business_name', 'commission_rate', 'status',
                  'data_consent_given', 'data_consent_version',
                  'show_bbt_branding_on_receipt', 'created_at']
        read_only_fields = ['id', 'commission_rate', 'status', 'created_at']


class PartnerStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PartnerStaff
        fields = '__all__'
        read_only_fields = ['id', 'partner', 'created_at', 'updated_at']


class StaffLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StaffLeave
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class StaffSalaryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StaffSalaryRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class PartnerGuestRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PartnerGuestRecord
        fields = '__all__'
        read_only_fields = ['id', 'partner', 'created_at', 'updated_at']


class PartnerRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PartnerRoom
        fields = '__all__'
        read_only_fields = ['id', 'partner', 'created_at']


class RoomAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RoomAssignment
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class PartnerTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PartnerTask
        fields = '__all__'
        read_only_fields = ['id', 'partner', 'created_at', 'updated_at']


class PartnerVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PartnerVehicle
        fields = '__all__'
        read_only_fields = ['id', 'partner', 'created_at', 'updated_at']


class VehicleDriverLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VehicleDriverLink
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class VehicleTripRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VehicleTripRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class PartnerCommoditySerializer(serializers.ModelSerializer):
    class Meta:
        model  = PartnerCommodity
        fields = '__all__'
        read_only_fields = ['id', 'partner', 'created_at', 'updated_at']


class CommodityAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CommodityAssignment
        fields = '__all__'
        read_only_fields = ['id', 'assigned_at']


class PartnerClosureDateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PartnerClosureDate
        fields = '__all__'
        read_only_fields = ['id', 'partner', 'created_at']


class ActivityCategoryEligibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model  = ActivityCategoryEligibility
        fields = '__all__'
        read_only_fields = ['id', 'updated_at']


class PartnerActivityCertificationSerializer(serializers.ModelSerializer):
    is_active = serializers.ReadOnlyField()

    class Meta:
        model  = PartnerActivityCertification
        fields = '__all__'
        read_only_fields = ['id', 'partner', 'is_verified', 'verified_by',
                            'verified_at', 'created_at', 'updated_at']


class ActivityServiceAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ActivityServiceAssignment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']