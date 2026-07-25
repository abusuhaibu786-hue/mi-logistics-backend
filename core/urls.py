from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    DashboardStatsView,
    NotificationViewSet,
    PublicTrackingView,
    ShipmentViewSet,
    StaffViewSet,
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'shipments', ShipmentViewSet, basename='shipment')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('track/<str:tracking_number>/', PublicTrackingView.as_view(), name='public-track'),
]
