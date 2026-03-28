"""Schedule publish view."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Schedule
from ..serializers import ScheduleSerializer


class SchedulePublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        schedule = get_object_or_404(
            Schedule.objects.select_related("created_by"), pk=pk
        )
        if schedule.status != Schedule.Status.DRAFT:
            return Response(
                {"error": "Only Draft schedules can be published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        schedule.status = Schedule.Status.PUBLISHED
        schedule.save(update_fields=["status"])
        return Response(ScheduleSerializer(schedule).data)
