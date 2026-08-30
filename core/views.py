from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Customer, Feedback, Notification, Shipment, Staff, TrackingEvent
from .serializers import (
    CustomerSerializer,
    FeedbackSerializer,
    NotificationSerializer,
    PublicTrackingSerializer,
    ShipmentDetailSerializer,
    ShipmentListSerializer,
    StaffSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'city']
    search_fields = ['name', 'email', 'phone', 'code']
    ordering_fields = ['join_date', 'name']
    lookup_field = 'code'
    lookup_url_kwarg = 'code'


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'department']
    search_fields = ['name', 'email', 'phone', 'code', 'role']
    ordering_fields = ['join_date', 'name', 'rating']
    lookup_field = 'code'
    lookup_url_kwarg = 'code'


class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.select_related('customer', 'staff').prefetch_related('tracking_events')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'origin', 'destination']
    search_fields = ['tracking_number', 'code', 'customer__name', 'receiver_name', 'destination']
    ordering_fields = ['booked_date', 'created_at', 'amount']
    lookup_field = 'code'
    lookup_url_kwarg = 'code'

    def get_serializer_class(self):
        if self.action in ('list',):
            return ShipmentListSerializer
        return ShipmentDetailSerializer

    @action(detail=False, methods=['get'], url_path='by-tracking-number/(?P<tracking_number>[^/.]+)')
    def by_tracking_number(self, request, tracking_number=None):
        """
        GET /api/shipments/by-tracking-number/{tracking_number}/
        Authenticated lookup by tracking number (e.g. MIL-2024-002), as
        opposed to the internal shipment code (e.g. SHP002) used by the
        viewset's default detail route. Used by the dashboard's internal
        Tracking page, which is what customers and staff actually type in.
        """
        shipment = self.get_queryset().filter(tracking_number__iexact=tracking_number).first()
        if not shipment:
            return Response({'detail': 'No shipment found for this tracking number.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ShipmentDetailSerializer(shipment).data)

    @action(detail=True, methods=['post'])
    def add_event(self, request, code=None):
        """POST /api/shipments/{code}/add_event/ — append a manifest update."""
        shipment = self.get_object()
        title = request.data.get('title')
        if not title:
            return Response({'detail': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark any previously-current event as no longer current.
        shipment.tracking_events.filter(is_current=True).update(is_current=False)

        event = TrackingEvent.objects.create(
            shipment=shipment,
            title=title,
            description=request.data.get('desc', ''),
            location=request.data.get('location', ''),
            is_completed=request.data.get('done', True),
            is_current=request.data.get('active', True),
        )

        new_status = request.data.get('status')
        if new_status in Shipment.Status.values:
            shipment.status = new_status
            if new_status == Shipment.Status.DELIVERED:
                shipment.delivered_date = timezone.now().date()
            shipment.save()

        return Response(ShipmentDetailSerializer(shipment).data, status=status.HTTP_201_CREATED)


class PublicTrackingView(generics.RetrieveAPIView):
    """
    GET /api/track/<tracking_number>/
    No auth required — this is what the public parcel-tracking page calls.
    """
    queryset = Shipment.objects.select_related('customer').prefetch_related('tracking_events')
    serializer_class = PublicTrackingSerializer
    permission_classes = [AllowAny]
    lookup_field = 'tracking_number'
    lookup_url_kwarg = 'tracking_number'


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(Q(user=user) | Q(user__isnull=True))

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response(NotificationSerializer(notif).data)


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    POST /api/feedback/        — public submit (Feedback page, no auth needed)
    GET  /api/feedback/        — authenticated staff list, pulled straight
                                  from the `feedback` table (most recent first)
    GET  /api/feedback/{id}/   — authenticated staff detail
    """
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'mobile']
    ordering_fields = ['created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]


class DashboardStatsView(generics.GenericAPIView):
    """
    GET /api/dashboard/stats/
    Aggregate numbers for the dashboard's summary cards + charts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shipments = Shipment.objects.all()
        total_revenue = shipments.aggregate(total=Sum('amount'))['total'] or 0

        status_breakdown = shipments.values('status').annotate(count=Count('id'))
        status_counts = {row['status']: row['count'] for row in status_breakdown}

        return Response({
            'totalShipments': shipments.count(),
            'totalCustomers': Customer.objects.count(),
            'totalStaff': Staff.objects.filter(status=Staff.Status.ACTIVE).count(),
            'totalRevenue': total_revenue,
            'statusBreakdown': status_counts,
            'pendingShipments': status_counts.get(Shipment.Status.PENDING, 0),
            'inTransitShipments': status_counts.get(Shipment.Status.IN_TRANSIT, 0),
            'deliveredShipments': status_counts.get(Shipment.Status.DELIVERED, 0),
        })


def _add_months(d, n):
    """Return the 1st of the month that is n months after d (n can be negative)."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return d.replace(year=year, month=month, day=1)


class MonthlyStatsView(generics.GenericAPIView):
    """
    GET /api/dashboard/monthly/?months=7
    Real month-by-month revenue/shipment/delivered figures computed from
    actual Shipment rows (grouped by booked_date's month). Replaces the
    frontend's old hardcoded MONTHLY_DATA mock used by the Dashboard and
    Reports charts/tables — every number here comes from the database.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        months_back = int(request.query_params.get('months', 7))
        start_month = _add_months(timezone.now().date().replace(day=1), -(months_back - 1))

        rows = (
            Shipment.objects
            .filter(booked_date__gte=start_month)
            .annotate(month=TruncMonth('booked_date'))
            .values('month')
            .annotate(
                shipments=Count('id'),
                delivered=Count('id', filter=Q(status=Shipment.Status.DELIVERED)),
                revenue=Sum('amount'),
            )
        )
        by_month = {row['month']: row for row in rows}

        labels, revenue, shipments, delivered = [], [], [], []
        cursor = start_month
        for _ in range(months_back):
            row = by_month.get(cursor)
            labels.append(cursor.strftime('%b'))
            revenue.append(float(row['revenue']) if row and row['revenue'] else 0)
            shipments.append(row['shipments'] if row else 0)
            delivered.append(row['delivered'] if row else 0)
            cursor = _add_months(cursor, 1)

        return Response({'labels': labels, 'revenue': revenue, 'shipments': shipments, 'delivered': delivered})
