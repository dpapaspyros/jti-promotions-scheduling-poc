from django.db import models


class POSMetrics(models.Model):
    class ReferenceType(models.TextChoices):
        PREVIOUS_YEAR = "previous_year", "Previous Year"
        PREVIOUS_MONTH = "previous_month", "Previous Month"

    pos = models.ForeignKey(
        "scheduling.PointOfSale",
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    reference_type = models.CharField(max_length=20, choices=ReferenceType.choices)
    period_start = models.DateField()
    period_end = models.DateField()
    window_date = models.DateField()
    window_start = models.TimeField()
    window_end = models.TimeField()
    sales = models.PositiveIntegerField(default=0)
    interviews = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [
            (
                "pos",
                "reference_type",
                "period_start",
                "period_end",
                "window_date",
                "window_start",
                "window_end",
            )
        ]
        verbose_name = "POS Metrics"
        verbose_name_plural = "POS Metrics"
        ordering = ["pos__cdb_code", "window_date", "window_start"]

    def __str__(self):
        return (
            f"{self.pos.cdb_code} | {self.window_date}"
            f" {self.window_start:%H:%M}–{self.window_end:%H:%M}"
            f" | sales={self.sales} interviews={self.interviews}"
        )
