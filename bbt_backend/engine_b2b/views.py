import hashlib
import logging
from django.db import models
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from engine_b2b.models import (
    PartnerProfile, PartnerStaff, StaffLeave, StaffSalaryRecord,
    PartnerGuestRecord, PartnerRoom, RoomAssignment, PartnerTask,
    PartnerVehicle, VehicleDriverLink, VehicleTripRecord,
    PartnerCommodity, CommodityAssignment, PartnerClosureDate,
    PartnerActivityCertification, ActivityServiceAssignment,
)
from engine_b2b.serializers import (
    PartnerProfileSerializer, PartnerStaffSerializer,
    StaffLeaveSerializer, StaffSalaryRecordSerializer,
    PartnerGuestRecordSerializer, PartnerRoomSerializer,
    RoomAssignmentSerializer, PartnerTaskSerializer,
    PartnerVehicleSerializer, VehicleDriverLinkSerializer,
    VehicleTripRecordSerializer, PartnerCommoditySerializer,
    CommodityAssignmentSerializer, PartnerClosureDateSerializer,
    PartnerActivityCertificationSerializer,
    ActivityServiceAssignmentSerializer,
)

logger = logging.getLogger(__name__)


def _get_partner(user):
    try:
        return user.partner_profile
    except Exception:
        return None


# ── Profile and consent ───────────────────────────────────────────────────────

class PartnerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'Partner profile not found.'}, status=404)
        return Response(PartnerProfileSerializer(partner).data)

    def patch(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'Partner profile not found.'}, status=404)
        s = PartnerProfileSerializer(partner, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)


class DataConsentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'Partner profile not found.'}, status=404)
        if not request.data.get('consent_given'):
            return Response({'error': 'consent_given must be true.'}, status=400)
        version = request.data.get('consent_version', 'v1.0')
        partner.data_consent_given   = True
        partner.data_consent_version = version
        partner.data_consented_at    = timezone.now()
        partner.data_consent_ip      = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '')
        )
        partner.save()
        return Response({
            'message':         'Data consent recorded.',
            'consent_version': version,
            'consented_at':    partner.data_consented_at,
        })


# ── Staff ─────────────────────────────────────────────────────────────────────

class StaffListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        qs = partner.staff.all()
        if request.query_params.get('status'):
            qs = qs.filter(status=request.query_params['status'])
        return Response(PartnerStaffSerializer(qs, many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = PartnerStaffSerializer(data=request.data)
        if s.is_valid():
            s.save(partner=partner)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class StaffDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _staff(self, partner, staff_id):
        try:
            return partner.staff.get(id=staff_id)
        except PartnerStaff.DoesNotExist:
            return None

    def get(self, request, staff_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        staff = self._staff(partner, staff_id)
        if not staff:
            return Response({'error': 'Staff not found.'}, status=404)
        return Response(PartnerStaffSerializer(staff).data)

    def patch(self, request, staff_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        staff = self._staff(partner, staff_id)
        if not staff:
            return Response({'error': 'Staff not found.'}, status=404)
        s = PartnerStaffSerializer(staff, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def delete(self, request, staff_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        staff = self._staff(partner, staff_id)
        if not staff:
            return Response({'error': 'Staff not found.'}, status=404)
        staff.status = 'terminated'
        staff.employment_end = timezone.now().date()
        staff.save()
        return Response({'message': 'Staff marked as terminated.'})


class StaffLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, staff_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        leaves = StaffLeave.objects.filter(
            staff__partner=partner, staff_id=staff_id)
        return Response(StaffLeaveSerializer(leaves, many=True).data)

    def post(self, request, staff_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            staff = partner.staff.get(id=staff_id)
        except PartnerStaff.DoesNotExist:
            return Response({'error': 'Staff not found.'}, status=404)
        s = StaffLeaveSerializer(data=request.data)
        if s.is_valid():
            s.save(staff=staff)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class StaffSalaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, staff_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        records = StaffSalaryRecord.objects.filter(
            staff__partner=partner,
            staff_id=staff_id).order_by('-paid_on')
        return Response(StaffSalaryRecordSerializer(records, many=True).data)

    def post(self, request, staff_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            staff = partner.staff.get(id=staff_id)
        except PartnerStaff.DoesNotExist:
            return Response({'error': 'Staff not found.'}, status=404)
        s = StaffSalaryRecordSerializer(data=request.data)
        if s.is_valid():
            s.save(staff=staff)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


# ── Guest Records ─────────────────────────────────────────────────────────────

class GuestRecordListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        qs = partner.guest_records.all()
        if request.query_params.get('status'):
            qs = qs.filter(status=request.query_params['status'])
        if request.query_params.get('source'):
            qs = qs.filter(source=request.query_params['source'])
        return Response(PartnerGuestRecordSerializer(qs, many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        data = request.data.copy()
        # Auto-populate from BBT booking if ref provided
        if data.get('bbt_booking_ref'):
            data = _autofill_from_bbt(data, data['bbt_booking_ref'])
        # Hash Aadhaar number if provided raw
        raw_aadhaar = data.pop('aadhaar_number', None)
        if raw_aadhaar:
            data['aadhaar_hash'] = hashlib.sha256(
                str(raw_aadhaar).encode()).hexdigest()
        s = PartnerGuestRecordSerializer(data=data)
        if s.is_valid():
            s.save(partner=partner)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class GuestRecordDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _record(self, partner, record_id):
        try:
            return partner.guest_records.get(id=record_id)
        except PartnerGuestRecord.DoesNotExist:
            return None

    def get(self, request, record_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        record = self._record(partner, record_id)
        if not record:
            return Response({'error': 'Record not found.'}, status=404)
        return Response(PartnerGuestRecordSerializer(record).data)

    def patch(self, request, record_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        record = self._record(partner, record_id)
        if not record:
            return Response({'error': 'Record not found.'}, status=404)
        s = PartnerGuestRecordSerializer(record, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            if request.data.get('status') == 'checked_out':
                _trigger_checkout_tasks(partner, record)
            return Response(s.data)
        return Response(s.errors, status=400)


# ── Rooms ─────────────────────────────────────────────────────────────────────

class RoomListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        qs = partner.rooms.all()
        if request.query_params.get('status'):
            qs = qs.filter(status=request.query_params['status'])
        return Response(PartnerRoomSerializer(qs, many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = PartnerRoomSerializer(data=request.data)
        if s.is_valid():
            s.save(partner=partner)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class RoomDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, room_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            room = partner.rooms.get(id=room_id)
        except PartnerRoom.DoesNotExist:
            return Response({'error': 'Room not found.'}, status=404)
        s = PartnerRoomSerializer(room, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)


class RoomAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = RoomAssignmentSerializer(data=request.data)
        if s.is_valid():
            assignment = s.save()
            assignment.room.status = 'occupied'
            assignment.room.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


# ── Tasks ─────────────────────────────────────────────────────────────────────

class TaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        qs = partner.tasks.all()
        if request.query_params.get('status'):
            qs = qs.filter(status=request.query_params['status'])
        if request.query_params.get('task_type'):
            qs = qs.filter(task_type=request.query_params['task_type'])
        if request.query_params.get('assigned_to'):
            qs = qs.filter(assigned_to_id=request.query_params['assigned_to'])
        return Response(PartnerTaskSerializer(qs, many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = PartnerTaskSerializer(data=request.data)
        if s.is_valid():
            s.save(partner=partner)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            task = partner.tasks.get(id=task_id)
        except PartnerTask.DoesNotExist:
            return Response({'error': 'Task not found.'}, status=404)
        if request.data.get('status') == 'done':
            task.completed_at = timezone.now()
        s = PartnerTaskSerializer(task, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)


# ── Vehicles ──────────────────────────────────────────────────────────────────

class VehicleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        return Response(PartnerVehicleSerializer(
            partner.vehicles.all(), many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = PartnerVehicleSerializer(data=request.data)
        if s.is_valid():
            s.save(partner=partner)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class VehicleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, vehicle_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            vehicle = partner.vehicles.get(id=vehicle_id)
        except PartnerVehicle.DoesNotExist:
            return Response({'error': 'Vehicle not found.'}, status=404)
        s = PartnerVehicleSerializer(vehicle, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)


class VehicleDriverLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, vehicle_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        links = VehicleDriverLink.objects.filter(
            vehicle__partner=partner, vehicle_id=vehicle_id)
        return Response(VehicleDriverLinkSerializer(links, many=True).data)

    def post(self, request, vehicle_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            partner.vehicles.get(id=vehicle_id)
        except PartnerVehicle.DoesNotExist:
            return Response({'error': 'Vehicle not found.'}, status=404)
        try:
            partner.staff.get(id=request.data.get('driver'), role='driver')
        except PartnerStaff.DoesNotExist:
            return Response(
                {'error': 'Driver not found or not a driver role.'}, status=400)
        s = VehicleDriverLinkSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class TripRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        qs = VehicleTripRecord.objects.filter(
            vehicle__partner=partner).order_by('-created_at')
        if request.query_params.get('status'):
            qs = qs.filter(status=request.query_params['status'])
        return Response(VehicleTripRecordSerializer(qs, many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = VehicleTripRecordSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


# ── Commodities ───────────────────────────────────────────────────────────────

class CommodityListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        qs = partner.commodities.filter(is_active=True)
        if request.query_params.get('category'):
            qs = qs.filter(category=request.query_params['category'])
        return Response(PartnerCommoditySerializer(qs, many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = PartnerCommoditySerializer(data=request.data)
        if s.is_valid():
            s.save(partner=partner)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class CommodityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, commodity_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            commodity = partner.commodities.get(id=commodity_id)
        except PartnerCommodity.DoesNotExist:
            return Response({'error': 'Commodity not found.'}, status=404)
        s = PartnerCommoditySerializer(commodity, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)


class CommodityAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = CommodityAssignmentSerializer(data=request.data)
        if s.is_valid():
            assignment = s.save()
            c = assignment.commodity
            c.quantity = max(0, c.quantity - assignment.quantity)
            c.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)

    def patch(self, request, assignment_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            assignment = CommodityAssignment.objects.get(
                id=assignment_id, commodity__partner=partner)
        except CommodityAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found.'}, status=404)
        assignment.returned_at = timezone.now()
        assignment.condition_on_return = request.data.get(
            'condition_on_return', 'good')
        assignment.save()
        c = assignment.commodity
        c.quantity += assignment.quantity
        c.save()
        return Response(CommodityAssignmentSerializer(assignment).data)


# ── Closure Dates ─────────────────────────────────────────────────────────────

class ClosureDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        return Response(PartnerClosureDateSerializer(
            partner.closure_dates.all().order_by('date'), many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = PartnerClosureDateSerializer(data=request.data)
        if s.is_valid():
            s.save(partner=partner)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)

    def delete(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        date_str = request.data.get('date')
        if not date_str:
            return Response({'error': 'date required.'}, status=400)
        partner.closure_dates.filter(date=date_str).delete()
        return Response({'message': 'Closure date removed.'})


# ── Activity Certifications ───────────────────────────────────────────────────

class ActivityCertificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        certs = partner.activity_certifications.all()
        return Response(
            PartnerActivityCertificationSerializer(certs, many=True).data)

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        s = PartnerActivityCertificationSerializer(data=request.data)
        if s.is_valid():
            s.save(partner=partner)
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


# ── Activity Service Assignments ──────────────────────────────────────────────

class ServiceAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        qs = ActivityServiceAssignment.objects.filter(
            provider_partner=partner).order_by('-created_at')
        if request.query_params.get('status'):
            qs = qs.filter(status=request.query_params['status'])
        return Response(
            ActivityServiceAssignmentSerializer(qs, many=True).data)

    def patch(self, request, assignment_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        try:
            assignment = ActivityServiceAssignment.objects.get(
                id=assignment_id, provider_partner=partner)
        except ActivityServiceAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found.'}, status=404)
        s = ActivityServiceAssignmentSerializer(
            assignment, data=request.data, partial=True)
        if s.is_valid():
            if request.data.get('status') == 'completed':
                assignment.completed_at = timezone.now()
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _autofill_from_bbt(data: dict, booking_ref: str) -> dict:
    """
    Populates guest fields from a BBT booking reference.
    Phase 5 will implement the full resolver once Booking model exists.
    For now marks source and passes through.
    """
    try:
        data['source'] = 'bbt_booking'
    except Exception as e:
        logger.debug(f'BBT autofill failed for ref {booking_ref}: {e}')
    return data


def _trigger_checkout_tasks(partner, guest_record):
    """Auto-creates housekeeping task on guest checkout."""
    try:
        assignment = guest_record.room_assignments.filter(
            actual_check_out__isnull=True).first()
        if not assignment:
            return
        assignment.room.status = 'cleaning'
        assignment.room.save()
        assignment.actual_check_out = timezone.now()
        assignment.save()
        PartnerTask.objects.create(
            partner=partner,
            task_type='housekeeping',
            title=f'Room {assignment.room.room_number} — post checkout clean',
            priority='high',
            linked_room=assignment.room,
            linked_guest=guest_record,
            status='open',
        )
    except Exception as e:
        logger.error(f'Checkout task trigger failed: {e}')


class PartnerConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, line_item_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'Partner profile required.'}, status=403)
        from engine_b2c.tasks.booking_confirmation import partner_confirm_line_item
        partner_confirm_line_item.delay(str(line_item_id), str(partner.id))
        return Response({'message': 'Confirmation queued.'})


class PartnerRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, line_item_id):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'Partner profile required.'}, status=403)
        reason = request.data.get('reason', '')
        from engine_b2c.tasks.booking_confirmation import partner_reject_line_item
        partner_reject_line_item.delay(str(line_item_id), str(partner.id), reason)
        return Response({'message': 'Rejection queued.'})


class PartnerPendingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'Partner profile required.'}, status=403)
        from engine_b2c.models import BookingLineItem
        items = BookingLineItem.objects.filter(
            partner_id=str(partner.id),
            status__in=('pending', 'pending_confirmation'),
        ).order_by('confirmation_deadline')
        return Response([
            {
                'id':                 str(li.id),
                'service':            li.activity_name,
                'date':               str(li.scheduled_date),
                'pax':                li.quantity,
                'value':              str(li.subtotal),
                'status':             li.status,
                'customer':           'Guest', # Booking model usually has customer info
            }
            for li in items
        ])

class PartnerNotificationView(APIView):
    """
    GET /api/v1/partner/notifications/
    Partner's own notification stream — approvals, rejections, new bookings.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        from engine_b2c.models import Notification
        base_qs = Notification.objects.filter(user_id=str(request.user.id))
        unread = base_qs.filter(is_read=False).count()
        nots = base_qs.order_by('-created_at')[:20]
        return Response({
            'unread_count':  unread,
            'notifications': [n.to_dict() for n in nots],
        })

    def post(self, request):
        """Mark all partner notifications as read."""
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        from engine_b2c.models import Notification
        from django.utils import timezone
        Notification.objects.filter(
            user_id = str(request.user.id),
            is_read = False,
        ).update(is_read=True, read_at=timezone.now())
        return Response({'marked_read': True})


class PartnerBookingUpdateView(APIView):
    """PATCH /api/v1/partner/bookings/<id>/ — handles confirm/reject from portal."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, line_item_id):
        partner = _get_partner(request.user)
        if not partner: return Response(status=403)
        
        status = request.data.get('status')
        from engine_b2c.tasks.booking_confirmation import partner_confirm_line_item, partner_reject_line_item
        
        if status == 'confirmed':
            partner_confirm_line_item.delay(str(line_item_id), str(partner.id))
            return Response({'message': 'Confirmation queued.'})
        elif status == 'rejected':
            reason = request.data.get('reason', 'Rejected via portal')
            partner_reject_line_item.delay(str(line_item_id), str(partner.id), reason)
            return Response({'message': 'Rejection queued.'})
        
        return Response({'error': 'Invalid status.'}, status=400)



# ── Aggregate Views for Frontend ──────────────────────────────────────────────

class PartnerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner:
            return Response({'error': 'No partner profile.'}, status=403)
        
        from engine_b2c.models import BookingLineItem
        
        # Stats
        print(f"DEBUG DASHBOARD: partner_id={partner.id} (str={str(partner.id)})")
        pending_count = BookingLineItem.objects.filter(
            partner_id=str(partner.id),
            status__in=('pending', 'pending_confirmation')
        ).count()
        print(f"DEBUG DASHBOARD: pending_count={pending_count}")
        
        # This month's earnings
        now = timezone.now()
        monthly_earnings = partner.earnings.filter(
            created_at__year=now.year,
            created_at__month=now.month
        ).aggregate(models.Sum('amount_net'))['amount_net__sum'] or 0
        
        return Response({
            'partner': {
                'id': str(partner.id),
                'name': partner.business_name,
                'commission_rate': partner.commission_rate,
            },
            'stats': {
                'pendingBookings': pending_count,
                'bookingsThisMonth': 0, # Placeholder for now
                'monthlyEarnings': f"{monthly_earnings:,.0f}",
                'monthlyEarningsDigit': float(monthly_earnings),
                'averageRating': '4.9',
            }
        })

class PartnerAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner: return Response(status=403)
        from engine_b2b.models import PartnerAvailabilitySlot
        slots = PartnerAvailabilitySlot.objects.filter(partner=partner)
        return Response({
            'slots': [{'date': str(s.date), 'status': s.status} for s in slots]
        })

    def post(self, request):
        partner = _get_partner(request.user)
        if not partner: return Response(status=403)
        from engine_b2b.models import PartnerAvailabilitySlot
        date = request.data.get('date')
        status = request.data.get('status', 'available')
        slot, _ = PartnerAvailabilitySlot.objects.update_or_create(
            partner=partner, date=date,
            defaults={'status': status}
        )
        return Response({'date': str(slot.date), 'status': slot.status})

class PartnerPayoutsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner: return Response(status=403)
        from engine_b2b.models import PartnerEarning
        from engine_b2b.models import PartnerEarning
        earnings_qs = PartnerEarning.objects.filter(partner=partner).order_by('-created_at')
        
        now = timezone.now()
        this_month = earnings_qs.filter(created_at__year=now.year, created_at__month=now.month).aggregate(models.Sum('amount_net'))['amount_net__sum'] or 0
        this_year = earnings_qs.filter(created_at__year=now.year).aggregate(models.Sum('amount_net'))['amount_net__sum'] or 0
        pending_payout = earnings_qs.filter(status='verified').aggregate(models.Sum('amount_net'))['amount_net__sum'] or 0
        
        summary = {
            'this_month': float(this_month),
            'this_year': float(this_year),
            'pending_payout': float(pending_payout),
            'commission_rate': partner.commission_rate
        }
        
        return Response({
            'summary': summary,
            'payouts': [
                {
                    'earning_id': str(e.id),
                    'gross': str(e.amount_gross),
                    'net': str(e.amount_net),
                    'status': e.status,
                    'created_at': e.created_at.isoformat()
                } for e in earnings_qs[:50]
            ],
            'monthly_chart': {} # Optional: could aggregate by month
        })

class PartnerServicesView(APIView):
    """Aggregates all inventory types (Rooms, Vehicles, etc.) for the partner."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        partner = _get_partner(request.user)
        if not partner: return Response(status=403)
        
        services = []
        
        # Vehicles
        for v in partner.vehicles.all():
            services.append({
                'service_id': str(v.id),
                'service_type': 'vehicle',
                'name': f"{v.make} {v.model}",
                'reg_number': v.registration_no,
                'category': v.vehicle_type,
                'capacity': v.capacity_persons,
                'price': 'N/A', # Pricing would come from a different model or field
                'active': v.status == 'available'
            })
            
        # Rooms
        for r in partner.rooms.all():
            services.append({
                'service_id': str(r.id),
                'service_type': 'accommodation',
                'name': f"Room {r.room_number}",
                'category': r.room_type,
                'capacity': r.capacity,
                'price': 'N/A',
                'active': r.status == 'available'
            })
            
        return Response({'services': services})

