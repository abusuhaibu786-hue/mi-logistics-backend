from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from authentication.models import User
from core.models import Customer, Notification, Shipment, Staff, TrackingEvent


class Command(BaseCommand):
    help = 'Seeds the database with sample customers, staff, shipments and tracking events.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Delete existing Customer/Staff/Shipment/Notification rows before seeding.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.now().date()

        def ago(days):
            """ISO date string `days` days before today — keeps seed data inside
            the dashboard's rolling last-7-months window no matter when this
            command is run, instead of being pinned to a fixed 2024 date."""
            return (today - timedelta(days=days)).isoformat()

        if options['flush']:
            self.stdout.write('Flushing existing data...')
            TrackingEvent.objects.all().delete()
            Shipment.objects.all().delete()
            Customer.objects.all().delete()
            Staff.objects.all().delete()
            Notification.objects.all().delete()

        # ---------------------------------------------------------------
        # Admin login
        # ---------------------------------------------------------------
        if not User.objects.filter(email='admin@milogistics.in').exists():
            User.objects.create_superuser(
                email='admin@milogistics.in',
                username='admin',
                password='admin123',
                name='MI Logistics Admin',
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / admin123'))

        # ---------------------------------------------------------------
        # Customers
        # ---------------------------------------------------------------
        customers_data = [
            ('Arjun Sharma', 'arjun.sharma@email.com', '+91 9876543210', 'Chennai', 'Tamil Nadu', '2023-04-12', 'active'),
            ('Priya Nair', 'priya.nair@email.com', '+91 9765432109', 'Coimbatore', 'Tamil Nadu', '2023-06-22', 'active'),
            ('Vikram Patel', 'vikram.patel@email.com', '+91 9654321098', 'Mumbai', 'Maharashtra', '2023-02-08', 'active'),
            ('Meena Krishnan', 'meena.krishnan@email.com', '+91 9543210987', 'Madurai', 'Tamil Nadu', '2023-09-14', 'active'),
            ('Suresh Babu', 'suresh.babu@email.com', '+91 9432109876', 'Bengaluru', 'Karnataka', '2023-03-30', 'inactive'),
            ('Lakshmi Devi', 'lakshmi.devi@email.com', '+91 9321098765', 'Trichy', 'Tamil Nadu', '2023-07-19', 'active'),
            ('Ravi Shankar', 'ravi.shankar@email.com', '+91 9210987654', 'Delhi', 'Delhi', '2022-11-05', 'active'),
            ('Kavitha Sundaram', 'kavitha.sundaram@email.com', '+91 9109876543', 'Tirunelveli', 'Tamil Nadu', '2023-08-27', 'active'),
            ('Muthu Raj', 'muthu.raj@email.com', '+91 9098765432', 'Salem', 'Tamil Nadu', '2023-05-02', 'active'),
            ('Divya Menon', 'divya.menon@email.com', '+91 8987654321', 'Kochi', 'Kerala', '2023-01-17', 'active'),
        ]
        customers = {}
        for name, email, phone, city, state, join_date, cstatus in customers_data:
            cust, _ = Customer.objects.get_or_create(
                email=email,
                defaults=dict(
                    name=name, phone=phone, city=city, state=state,
                    join_date=date.fromisoformat(join_date), status=cstatus,
                ),
            )
            customers[name] = cust
        self.stdout.write(self.style.SUCCESS(f'Customers ready: {len(customers)}'))

        # ---------------------------------------------------------------
        # Staff
        # ---------------------------------------------------------------
        staff_data = [
            ('Ramesh Kumar', 'ramesh.kumar@milogistics.com', '+91 9876501234', 'Delivery Manager', 'Operations', '2021-03-15', 42000, 'active', 4.8, 'Virudhunagar'),
            ('Senthil Murugan', 'senthil.murugan@milogistics.com', '+91 9765012345', 'Senior Driver', 'Delivery', '2021-08-20', 28000, 'active', 4.6, 'Virudhunagar'),
            ('Karthik Raja', 'karthik.raja@milogistics.com', '+91 9654012345', 'Warehouse Staff', 'Warehouse', '2022-01-10', 22000, 'active', 4.5, 'Sivakasi'),
            ('Prabhakaran S', 'prabhakaran@milogistics.com', '+91 9543012345', 'Driver', 'Delivery', '2022-05-18', 25000, 'active', 4.3, 'Aruppukottai'),
            ('Jeevitha R', 'jeevitha@milogistics.com', '+91 9432012345', 'Customer Service', 'Support', '2022-09-05', 20000, 'active', 4.7, 'Virudhunagar'),
            ('Balamurugan T', 'balamurugan@milogistics.com', '+91 9321012345', 'Driver', 'Delivery', '2023-02-14', 23000, 'on-leave', 4.2, 'Rajapalayam'),
        ]
        staff = {}
        for name, email, phone, role, dept, join_date, salary, sstatus, rating, address in staff_data:
            s, _ = Staff.objects.get_or_create(
                email=email,
                defaults=dict(
                    name=name, phone=phone, role=role, department=dept,
                    join_date=date.fromisoformat(join_date), salary=salary,
                    status=sstatus, rating=rating, address=address,
                ),
            )
            staff[name] = s
        self.stdout.write(self.style.SUCCESS(f'Staff ready: {len(staff)}'))

        # ---------------------------------------------------------------
        # Shipments
        # ---------------------------------------------------------------
        shipments_data = [
            ('MIL-2024-001', 'Arjun Sharma', 'Chennai', '2.5', 'delivered', 'standard', 320, ago(12), ago(10), None, 'Ramesh Kumar', '+91 9876543210', '14, Anna Nagar, Chennai 600040'),
            ('MIL-2024-002', 'Priya Nair', 'Coimbatore', '5.0', 'in-transit', 'express', 750, ago(8), None, ago(2), 'Senthil Murugan', '+91 9765432109', '7, RS Puram, Coimbatore 641002'),
            ('MIL-2024-003', 'Vikram Patel', 'Mumbai', '12.0', 'pending', 'economy', 1200, ago(38), None, ago(20), 'Karthik Raja', '+91 9654321098', '52, Andheri West, Mumbai 400053'),
            ('MIL-2024-004', 'Meena Krishnan', 'Madurai', '1.2', 'delivered', 'express', 220, ago(6), ago(5), None, 'Ramesh Kumar', '+91 9543210987', '3, Goripalayam, Madurai 625002'),
            ('MIL-2024-005', 'Suresh Babu', 'Bengaluru', '8.0', 'in-transit', 'standard', 890, ago(65), None, ago(50), 'Senthil Murugan', '+91 9432109876', '88, Indiranagar, Bengaluru 560038'),
            ('MIL-2024-006', 'Lakshmi Devi', 'Trichy', '3.4', 'delivered', 'standard', 280, ago(95), ago(93), None, 'Karthik Raja', '+91 9321098765', '21, Thillai Nagar, Trichy 620018'),
            ('MIL-2024-007', 'Ravi Shankar', 'Delhi', '20.0', 'pending', 'economy', 2400, ago(3), None, ago(4), 'Ramesh Kumar', '+91 9210987654', '15, Rohini, Delhi 110085'),
            ('MIL-2024-008', 'Kavitha Sundaram', 'Tirunelveli', '4.5', 'in-transit', 'express', 420, ago(125), None, ago(110), 'Karthik Raja', '+91 9109876543', '9, Krishnapuram, Tirunelveli 627011'),
            ('MIL-2024-009', 'Muthu Raj', 'Salem', '7.0', 'delivered', 'standard', 560, ago(155), ago(153), None, 'Senthil Murugan', '+91 9098765432', '34, Fairlands, Salem 636016'),
            ('MIL-2024-010', 'Divya Menon', 'Kochi', '9.0', 'cancelled', 'express', 980, ago(180), None, None, 'Ramesh Kumar', '+91 8987654321', '5, Ernakulam, Kochi 682016'),
        ]

        shipments = {}
        for tn, cust_name, dest, weight, sstatus, priority, amount, booked, delivered, est_delivery, staff_name, phone, address in shipments_data:
            shipment, created = Shipment.objects.get_or_create(
                tracking_number=tn,
                defaults=dict(
                    customer=customers[cust_name],
                    staff=staff.get(staff_name),
                    destination=dest,
                    receiver_name=cust_name,
                    receiver_phone=phone,
                    delivery_address=address,
                    weight_kg=weight,
                    status=sstatus,
                    priority=priority,
                    amount=amount,
                    booked_date=date.fromisoformat(booked),
                    delivered_date=date.fromisoformat(delivered) if delivered else None,
                    estimated_delivery=date.fromisoformat(est_delivery) if est_delivery else None,
                ),
            )
            shipments[tn] = shipment
        self.stdout.write(self.style.SUCCESS(f'Shipments ready: {len(shipments)}'))

        # ---------------------------------------------------------------
        # Tracking events for the two demo shipments with full timelines
        # ---------------------------------------------------------------
        tracking_events_data = {
            'MIL-2024-002': [
                ('Package Picked Up', 'Package picked up from sender', 'Virudhunagar', '2024-02-10T09:00:00', True, False),
                ('Sorted at Facility', 'Package sorted at Virudhunagar hub', 'Virudhunagar Hub', '2024-02-10T14:00:00', True, False),
                ('Dispatched', 'Package dispatched to destination city', 'Virudhunagar', '2024-02-11T07:00:00', True, False),
                ('In Transit', 'Package is on the way to Coimbatore', 'Dindigul', '2024-02-14T11:00:00', False, True),
                ('Out for Delivery', 'Package is out for delivery', 'Coimbatore', '2024-02-16T09:00:00', False, False),
                ('Delivered', 'Package delivered to recipient', 'Coimbatore', '2024-02-16T09:00:00', False, False),
            ],
            'MIL-2024-001': [
                ('Package Picked Up', 'Package picked up from sender', 'Virudhunagar', '2024-02-10T09:00:00', True, False),
                ('Sorted at Facility', 'Package sorted at hub', 'Virudhunagar Hub', '2024-02-10T13:00:00', True, False),
                ('Dispatched', 'Package dispatched to Chennai', 'Virudhunagar', '2024-02-11T06:00:00', True, False),
                ('Arrived at City Hub', 'Package arrived at Chennai hub', 'Chennai Hub', '2024-02-11T18:00:00', True, False),
                ('Out for Delivery', 'Package out for delivery', 'Chennai', '2024-02-12T09:00:00', True, False),
                ('Delivered', 'Package successfully delivered', 'Anna Nagar, Chennai', '2024-02-12T14:30:00', True, True),
            ],
        }
        for tn, events in tracking_events_data.items():
            shipment = shipments[tn]
            if shipment.tracking_events.exists():
                continue
            for title, desc, location, occurred_at, done, active in events:
                TrackingEvent.objects.create(
                    shipment=shipment, title=title, description=desc, location=location,
                    occurred_at=timezone.make_aware(parse_datetime(occurred_at).replace(tzinfo=None)),
                    is_completed=done, is_current=active,
                )
        self.stdout.write(self.style.SUCCESS('Tracking events ready.'))

        # ---------------------------------------------------------------
        # Notifications
        # ---------------------------------------------------------------
        notifications_data = [
            ('New Shipment Booked', 'SHP010 booked for Kochi delivery'),
            ('Delivery Confirmed', 'MIL-2024-004 delivered to Madurai'),
            ('Payment Received', '₹1,200 received from Vikram Patel'),
            ('Staff Leave Request', 'Balamurugan T applied for leave'),
            ('New Customer Registration', 'Muthu Raj created an account'),
        ]
        for title, text in notifications_data:
            Notification.objects.get_or_create(title=title, text=text)
        self.stdout.write(self.style.SUCCESS('Notifications ready.'))

        self.stdout.write(self.style.SUCCESS('\nSeed complete. Login with admin@milogistics.in / admin123'))
