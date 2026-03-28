from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Schedule
from .serializers import ScheduleSerializer


class ScheduleListView(generics.ListAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Schedule.objects.select_related("created_by").order_by("-period_start")
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs
