from django.contrib import admin

from .models import POSMetrics


@admin.register(POSMetrics)
class POSMetricsAdmin(admin.ModelAdmin):
    list_display = (
        "pos",
        "reference_type",
        "period_start",
        "period_end",
        "window_date",
        "window_start",
        "window_end",
        "sales",
        "interviews",
    )
    list_filter = ("reference_type", "period_start", "period_end")
    search_fields = ("pos__cdb_code", "pos__name")
    ordering = ("pos__cdb_code", "window_date", "window_start")
