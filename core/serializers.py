from rest_framework import serializers
from django.utils import timezone

from .models import Customer, Feedback, Notification, Shipment, Staff, TrackingEvent


class CustomerSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='code', read_only=True)
    totalShipments = serializers.IntegerField(source='total_shipments', read_only=True)
    totalSpent = serializers.DecimalField(source='total_spent', max_digits=10, decimal_places=2, read_only=True)
    joinDate = serializers.DateField(source='join_date', required=False)

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'email', 'phone', 'city', 'state', 'status',
            'joinDate', 'totalShipments', 'totalSpent',
        ]


class StaffSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='code', read_only=True)
    joinDate = serializers.DateField(source='join_date', required=False)
    deliveries = serializers.IntegerField(read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id', 'name', 'email', 'phone', 'role', 'department',
            'address', 'salary', 'status', 'joinDate', 'rating', 'deliveries',
        ]


class TrackingEventSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    desc = serializers.CharField(source='description')
    location = serializers.CharField()
    time = serializers.SerializerMethodField()
    done = serializers.BooleanField(source='is_completed')
    active = serializers.BooleanField(source='is_current')

    class Meta:
        model = TrackingEvent
        fields = ['title', 'desc', 'location', 'time', 'done', 'active']

    def get_time(self, obj):
        local_dt = timezone.localtime(obj.occurred_at)
        return local_dt.strftime('%d %b %Y, %I:%M %p')


class ShipmentListSerializer(serializers.ModelSerializer):
    """Lightweight shape for table/list views."""
    id = serializers.CharField(source='code', read_only=True)
    trackingNumber = serializers.CharField(source='tracking_number', read_only=True)
    customer = serializers.CharField(source='customer.name', read_only=True)
    customerId = serializers.CharField(source='customer.code', read_only=True)
    weight = serializers.SerializerMethodField()
    date = serializers.DateField(source='booked_date', required=False)
    deliveredDate = serializers.DateField(source='delivered_date', required=False, allow_null=True)
    staff = serializers.CharField(source='staff.name', read_only=True, default=None)
    phone = serializers.CharField(source='receiver_phone', read_only=True)
    address = serializers.CharField(source='delivery_address', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'trackingNumber', 'customer', 'customerId', 'origin', 'destination',
            'weight', 'status', 'priority', 'amount', 'date', 'deliveredDate',
            'staff', 'phone', 'address',
        ]

    def get_weight(self, obj):
        return f'{obj.weight_kg} kg'


class ShipmentDetailSerializer(ShipmentListSerializer):
    """Adds the writable/raw fields needed for create + update + the public tracker."""
    customerCode = serializers.SlugRelatedField(
        source='customer', slug_field='code', queryset=Customer.objects.all(),
        write_only=True, required=False,
    )
    staffCode = serializers.SlugRelatedField(
        source='staff', slug_field='code', queryset=Staff.objects.all(),
        write_only=True, required=False, allow_null=True,
    )
    trackingEvents = TrackingEventSerializer(source='tracking_events', many=True, read_only=True)
    senderName = serializers.CharField(source='sender_name', required=False, allow_blank=True)
    senderPhone = serializers.CharField(source='sender_phone', required=False, allow_blank=True)
    receiverName = serializers.CharField(source='receiver_name', required=False, allow_blank=True)
    receiverPhone = serializers.CharField(source='receiver_phone')
    pickupAddress = serializers.CharField(source='pickup_address', required=False, allow_blank=True)
    deliveryAddress = serializers.CharField(source='delivery_address')
    weightKg = serializers.DecimalField(source='weight_kg', max_digits=6, decimal_places=2, write_only=True)
    parcelType = serializers.CharField(source='parcel_type', required=False)
    paymentMethod = serializers.CharField(source='payment_method', required=False)
    estimatedDelivery = serializers.DateField(source='estimated_delivery', required=False, allow_null=True)

    class Meta(ShipmentListSerializer.Meta):
        fields = ShipmentListSerializer.Meta.fields + [
            'customerCode', 'staffCode',
            'senderName', 'senderPhone', 'receiverName', 'receiverPhone',
            'pickupAddress', 'deliveryAddress', 'weightKg', 'parcelType',
            'paymentMethod', 'estimatedDelivery', 'trackingEvents',

        ]



class PublicTrackingSerializer(serializers.ModelSerializer):
    """
    Reduced, public-safe shape for the customer-facing tracker — no
    pricing, no sender/staff PII beyond what's needed to confirm identity.
    """
    trackingNumber = serializers.CharField(source='tracking_number')
    status = serializers.CharField()
    statusLabel = serializers.CharField(source='get_status_display')
    origin = serializers.CharField()
    destination = serializers.CharField()
    eta = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    events = TrackingEventSerializer(source='tracking_events', many=True)

    class Meta:
        model = Shipment
        fields = ['trackingNumber', 'status', 'statusLabel', 'origin', 'destination', 'eta', 'weight', 'events']

    def get_weight(self, obj):
        return f'{obj.weight_kg} kg'

    def get_eta(self, obj):
        if obj.status == Shipment.Status.DELIVERED and obj.delivered_date:
            return f"Delivered {obj.delivered_date.strftime('%d %b %Y')}"
        if obj.estimated_delivery:
            return f"Expected {obj.estimated_delivery.strftime('%d %b %Y')}"
        return 'Awaiting dispatch'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'text', 'is_read', 'created_at']


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'name', 'email', 'mobile', 'comments', 'created_at']
        read_only_fields = ['id', 'created_at']
