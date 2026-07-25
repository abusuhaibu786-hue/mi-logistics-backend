from datetime import date

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    code = models.CharField(max_length=20, unique=True, editable=False)  # e.g. C001
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default='Tamil Nadu')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    join_date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} - {self.name}'

    def save(self, *args, **kwargs):
        if not self.code:
            last = Customer.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.code = f'C{next_id:03d}'
        super().save(*args, **kwargs)

    @property
    def total_shipments(self):
        return self.shipments.count()

    @property
    def total_spent(self):
        return self.shipments.aggregate(total=models.Sum('amount'))['total'] or 0


class Staff(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ON_LEAVE = 'on-leave', 'On Leave'
        INACTIVE = 'inactive', 'Inactive'

    class Department(models.TextChoices):
        OPERATIONS = 'Operations', 'Operations'
        DELIVERY = 'Delivery', 'Delivery'
        WAREHOUSE = 'Warehouse', 'Warehouse'
        SUPPORT = 'Support', 'Support'

    code = models.CharField(max_length=20, unique=True, editable=False)  # e.g. ST001
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='staff_profile',
        help_text='Linked login account, if this staff member has dashboard access.'
    )
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=100)  # e.g. "Senior Driver"
    department = models.CharField(max_length=20, choices=Department.choices, default=Department.DELIVERY)
    address = models.CharField(max_length=255, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    join_date = models.DateField(default=date.today)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff'
        ordering = ['-created_at']
        verbose_name_plural = 'staff'

    def __str__(self):
        return f'{self.code} - {self.name}'

    def save(self, *args, **kwargs):
        if not self.code:
            last = Staff.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.code = f'ST{next_id:03d}'
        super().save(*args, **kwargs)

    @property
    def deliveries(self):
        return self.shipments.filter(status=Shipment.Status.DELIVERED).count()


class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_TRANSIT = 'in-transit', 'In Transit'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class Priority(models.TextChoices):
        ECONOMY = 'economy', 'Economy'
        STANDARD = 'standard', 'Standard'
        EXPRESS = 'express', 'Express'

    code = models.CharField(max_length=20, unique=True, editable=False)            # SHP001
    tracking_number = models.CharField(max_length=30, unique=True, editable=False)  # MIL-2026-001

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='shipments')
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')

    # Sender / receiver — kept distinct from the Customer record since a
    # customer can book parcels for someone else.
    sender_name = models.CharField(max_length=150, blank=True)
    sender_phone = models.CharField(max_length=20, blank=True)
    receiver_name = models.CharField(max_length=150, blank=True)
    receiver_phone = models.CharField(max_length=20, blank=True)

    origin = models.CharField(max_length=150, default='Virudhunagar')
    destination = models.CharField(max_length=150)
    pickup_address = models.TextField(blank=True)
    delivery_address = models.TextField(blank=True)

    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])
    parcel_type = models.CharField(max_length=100, blank=True, default='Documents')

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.STANDARD)

    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, default='COD')

    booked_date = models.DateField(default=date.today)
    delivered_date = models.DateField(null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shipments'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tracking_number} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.code or not self.tracking_number:
            last = Shipment.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            year = timezone.now().year
            self.code = self.code or f'SHP{next_id:03d}'
            self.tracking_number = self.tracking_number or f'MIL-{year}-{next_id:03d}'
        super().save(*args, **kwargs)


class TrackingEvent(models.Model):
    """One row per manifest scan/update for a shipment's timeline."""

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_events')
    title = models.CharField(max_length=150)          # "Package Picked Up"
    description = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=150, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False)
    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = 'tracking_events'
        ordering = ['occurred_at']

    def __str__(self):
        return f'{self.shipment.tracking_number}: {self.title}'


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications',
        null=True, blank=True, help_text='Leave blank to show to all dashboard users.'
    )
    title = models.CharField(max_length=150)
    text = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
