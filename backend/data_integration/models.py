from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class DataSyncLog(models.Model):
    class SyncType(models.TextChoices):
        PROMOTERS = "Promoters", "Promoters"
        POS = "POS", "Points of Sale"
        METRICS = "Metrics", "Metrics"

    class Status(models.TextChoices):
        SUCCESS = "Success", "Success"
        FAILED = "Failed", "Failed"

    sync_type = models.CharField(max_length=20, choices=SyncType.choices)
    triggered_at = models.DateTimeField(auto_now_add=True)
    triggered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sync_logs"
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    records_created = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    records_skipped = models.PositiveIntegerField(default=0)
    file_used = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-triggered_at"]
        verbose_name = "Data Sync Log"
        verbose_name_plural = "Data Sync Logs"

    def __str__(self):
        return (
            f"{self.sync_type} | {self.triggered_at:%Y-%m-%d %H:%M}" f" | {self.status}"
        )
