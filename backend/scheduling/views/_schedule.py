"""Schedule list/create, detail, and visit-list views."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Schedule, ScheduledVisit
from ..serializers import (
    ScheduleCreateSerializer,
    ScheduledVisitSerializer,
    ScheduleSerializer,
)


class ScheduleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ScheduleCreateSerializer
        return ScheduleSerializer

    def get_queryset(self):
        qs = Schedule.objects.select_related("created_by").order_by("-period_start")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        out = ScheduleSerializer(serializer.instance, context={"request": request})
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)


class ScheduleDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduleSerializer
    queryset = Schedule.objects.select_related("created_by")


class ScheduleVisitListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduledVisitSerializer

    def get_queryset(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs["pk"])
        return (
            ScheduledVisit.objects.filter(schedule=schedule)
            .select_related("pos", "promoter")
            .order_by("date", "start_time")
        )
