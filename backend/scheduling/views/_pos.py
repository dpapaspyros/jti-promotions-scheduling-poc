"""Point-of-Sale and Promoter list views."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import PointOfSale, Promoter
from ..serializers import PointOfSaleSerializer, PromoterSerializer


class PointOfSaleListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointOfSaleSerializer
    queryset = PointOfSale.objects.filter(is_active=True).order_by("name")


class PromoterListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PromoterSerializer
    queryset = Promoter.objects.filter(is_active=True).order_by(
        "last_name", "first_name"
    )
