# orders/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import permissions

from .models import Order
from .serializers import (
    OrderCreateSerializer,
    OrderListRetrieveSerializer,
    OrderStatusUpdateSerializer,
)


class IsOwnerOrStaff(permissions.BasePermission):
    """Customer can see own orders, staff can see all"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user or obj.user is None  # guest orders belong to no one → allow if staff


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('user').prefetch_related('items__product')
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at', 'requested_pickup_time', 'total_amount']
    search_fields = ['order_number', 'customer_name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]  # guests can order
        elif self.action in ['list', 'retrieve', 'active']:
            permission_classes = [IsAuthenticated, IsOwnerOrStaff]
        elif self.action == 'update_status':
            permission_classes = [IsAuthenticated, permissions.IsAdminUser]  # or custom IsBarista
        else:
            permission_classes = [permissions.IsAdminUser]
        return [perm() for perm in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderListRetrieveSerializer

    # ────────────────────── 1. CREATE ORDER (guests allowed) ────────────────────── #
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Attach authenticated user (if any) – guest stays null
        if request.user.is_authenticated:
            serializer.validated_data['user'] = request.user

        # For guest orders – require customer_name
        if not request.user.is_authenticated and not serializer.validated_data.get('customer_name'):
            return Response(
                {"customer_name": ["This field is required for guest checkout."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = serializer.save()
        return Response(
            OrderListRetrieveSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    # ────────────────────── 2. LIST & RETRIEVE (filtered for customers) ────────────────────── #
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        return Order.objects.none()  # non-auth never sees list

    # ────────────────────── 3. CUSTOM ACTION: update status (barista dashboard) ────────────────────── #
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Auto-mark as paid when confirming (optional coffee shop logic)
        if serializer.validated_data.get('status') == 'CONFIRMED' and not order.is_paid:
            if request.data.get('is_paid') or request.data.get('is_paid') is None:
                order.is_paid = True
                order.save()

        return Response(OrderListRetrieveSerializer(order).data)

    # ────────────────────── 4. STAFF DASHBOARD: active orders ────────────────────── #
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def active(self, request):
        """For barista screen – shows PENDING, CONFIRMED, PREPARING, READY"""
        active_statuses = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY']
        orders = self.get_queryset().filter(status__in=active_statuses)

        # Optional: highlight orders that are late
        now = timezone.now()
        orders = orders.annotate(
            is_late=models.Case(
                models.When(requested_pickup_time__lt=now, status__in=['PREPARING', 'READY'], then=True),
                default=False,
                output_field=models.BooleanField()
            )
        )

        page = self.paginate_queryset(orders)
        serializer = OrderListRetrieveSerializer(page or orders, many=True)
        return self.get_paginated_response(serializer.data)

