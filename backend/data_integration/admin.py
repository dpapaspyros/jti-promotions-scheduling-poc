import glob
import os

from django.contrib import admin, messages
from django.http import HttpResponseRedirect

from data_integration.importers.metrics import import_metrics
from data_integration.importers.pos import import_pos
from data_integration.importers.promoters import import_promoters

from .models import DataSyncLog

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

SAMPLE_FILES = {
    DataSyncLog.SyncType.PROMOTERS: os.path.join(
        SAMPLE_DATA_DIR, "sample_promoters.csv"
    ),
    DataSyncLog.SyncType.POS: os.path.join(SAMPLE_DATA_DIR, "sample_pos.csv"),
}

IMPORTERS = {
    DataSyncLog.SyncType.PROMOTERS: import_promoters,
    DataSyncLog.SyncType.POS: import_pos,
    DataSyncLog.SyncType.METRICS: import_metrics,
}


@admin.register(DataSyncLog)
class DataSyncLogAdmin(admin.ModelAdmin):
    change_list_template = "admin/data_integration/datasynclog/change_list.html"
    list_display = (
        "sync_type",
        "status",
        "records_created",
        "records_updated",
        "records_skipped",
        "file_used",
        "triggered_by",
        "triggered_at",
    )
    list_filter = ("sync_type", "status")
    readonly_fields = (
        "sync_type",
        "triggered_at",
        "triggered_by",
        "status",
        "records_created",
        "records_updated",
        "records_skipped",
        "file_used",
        "notes",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def _pull_metrics(self, request):
        """Import all period_*.csv files from sample_data and log each one."""
        metric_files = sorted(glob.glob(os.path.join(SAMPLE_DATA_DIR, "period_*.csv")))
        if not metric_files:
            messages.warning(request, "No period_*.csv files found in sample_data.")
            return

        for file_path in metric_files:
            try:
                result = import_metrics(file_path)
                status = DataSyncLog.Status.SUCCESS
                notes = "; ".join(result.get("errors", []))
            except Exception as exc:
                result = {"created": 0, "updated": 0, "skipped": 0}
                status = DataSyncLog.Status.FAILED
                notes = str(exc)

            DataSyncLog.objects.create(
                sync_type=DataSyncLog.SyncType.METRICS,
                triggered_by=request.user,
                status=status,
                records_created=result.get("created", 0),
                records_updated=result.get("updated", 0),
                records_skipped=result.get("skipped", 0),
                file_used=os.path.basename(file_path),
                notes=notes,
            )

            if status == DataSyncLog.Status.SUCCESS:
                messages.success(
                    request,
                    f"Metrics {os.path.basename(file_path)} — "
                    f"{result['created']} created, "
                    f"{result['updated']} updated, "
                    f"{result['skipped']} skipped.",
                )
            else:
                messages.error(
                    request,
                    f"Metrics {os.path.basename(file_path)} failed: {notes}",
                )

    def changelist_view(self, request, extra_context=None):
        pull_type = request.POST.get("pull_type")
        if request.method == "POST" and pull_type in IMPORTERS:
            if pull_type == DataSyncLog.SyncType.METRICS:
                self._pull_metrics(request)
            else:
                file_path = SAMPLE_FILES[pull_type]
                importer = IMPORTERS[pull_type]
                try:
                    result = importer(file_path)
                    status = DataSyncLog.Status.SUCCESS
                    notes = "; ".join(result.get("errors", []))
                except Exception as exc:
                    result = {"created": 0, "updated": 0, "skipped": 0}
                    status = DataSyncLog.Status.FAILED
                    notes = str(exc)

                DataSyncLog.objects.create(
                    sync_type=pull_type,
                    triggered_by=request.user,
                    status=status,
                    records_created=result.get("created", 0),
                    records_updated=result.get("updated", 0),
                    records_skipped=result.get("skipped", 0),
                    file_used=os.path.basename(file_path),
                    notes=notes,
                )

                if status == DataSyncLog.Status.SUCCESS:
                    msg = (
                        f"Pull {pull_type} complete — "
                        f"{result['created']} created, "
                        f"{result['updated']} updated, "
                        f"{result['skipped']} skipped."
                    )
                    messages.success(request, msg)
                else:
                    messages.error(request, f"Pull {pull_type} failed: {notes}")

            return HttpResponseRedirect(request.path)

        return super().changelist_view(request, extra_context=extra_context)
