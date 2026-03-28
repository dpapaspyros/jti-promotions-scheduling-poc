from rest_framework import serializers

from .models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "name",
            "period_start",
            "period_end",
            "status",
            "created_by",
            "created_at",
        ]
