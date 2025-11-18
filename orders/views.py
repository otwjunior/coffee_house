# orders/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, BooleanField, Q
from  rest_framework import permissions
from .models import Order
from .serializers import (
    OrderCreateSerializer,
    OrderListRetrieveSerializer,
    OrderStatusUpdateSerializer,
)


# ────────────────────── PERMISSIONS ────────────────────── #
class IsOwnerOrStaff(permissions.BasePermission):
    """Customer sees own orders, staff sees all, guests see nothing"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_manager or request.user.is_owner:
            return True
        return obj.user == request.user or obj.user is None


class IsBaristaOrBetter(permissions.BasePermission):
    """Baristas and above can update status"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_barista or request.user.is_manager or request.user.is_owner)
        )


# ────────────────────── MAIN VIEWSET ────────────────────── #
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('user').prefetch_related('items__product')
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ['list', 'retrieve', 'active']:
            return [IsAuthenticated(), IsOwnerOrStaff()]
        if self.action == 'update_status':
            return [IsBaristaOrBetter()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderListRetrieveSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff or self.request.user.is_manager or self.request.user.is_owner:
            return qs
        if self.request.user.is_authenticated:
            return qs.filter(user=self.request.user)
        return Order.objects.none()  # guests can't list

    # ────────────────────── 1. CREATE ORDER (guest + logged-in) ────────────────────── #
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Attach user if logged in
        if request.user.is_authenticated:
            serializer.validated_data['user'] = request.user
        # Guest checkout: require name
        elif not serializer.validated_data.get('customer_name'):
            return Response(
                {"customer_name": ["This field is required for guest checkout."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = serializer.save()
        return Response(
            OrderListRetrieveSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    # ────────────────────── 2. BARISTA: Update status ────────────────────── #
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Auto-mark as paid when confirming (common café flow)
        if serializer.validated_data.get('status') == 'CONFIRMED':
            if not order.is_paid:
                order.is_paid = True
                order.save(update_fields=['is_paid'])

        return Response(OrderListRetrieveSerializer(order).data)

    # ────────────────────── 3. BARISTA DASHBOARD: Active orders ────────────────────── #
    @action(detail=False, methods=['get'], permission_classes=[IsBaristaOrBetter])
    def active(self, request):
        """The iPad behind the counter — shows only current orders"""
        active_statuses = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY']
        now = timezone.now()

        orders = self.get_queryset().filter(status__in=active_statuses)

        # Highlight late orders
        orders = orders.annotate(
            is_late=Case(
                When(
                    Q(requested_pickup_time__lt=now) &
                    Q(status__in=['PREPARING', 'READY']),
                    then=True
                ),
                default=False,
                output_field=BooleanField()
            )
        ).order_by('is_late', 'requested_pickup_time')

        page = self.paginate_queryset(orders)
        serializer = OrderListRetrieveSerializer(page or orders, many=True)
        return self.get_paginated_response(serializer.data)