import csv
import re
from datetime import date, time

from metrics.models import POSMetrics
from scheduling.models import PointOfSale

_PERIOD_RE = re.compile(
    r"period_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})"
    r"_(previous_year|previous_month)_metrics"
)


def parse_period_from_filename(file_path):
    """
    Extract period_start, period_end, and reference_type from filenames like:
      period_2026-04-01_2026-04-30_previous_year_metrics.csv
    Returns (date, date, str) or raises ValueError.
    """
    import os

    stem = os.path.splitext(os.path.basename(file_path))[0]
    match = _PERIOD_RE.search(stem)
    if not match:
        raise ValueError(
            f"Cannot parse period from filename '{file_path}'. "
            "Expected: period_YYYY-MM-DD_YYYY-MM-DD_"
            "(previous_year|previous_month)_metrics.csv"
        )
    return (
        date.fromisoformat(match.group(1)),
        date.fromisoformat(match.group(2)),
        match.group(3),
    )


def _parse_time(value):
    """Parse HH:MM or HH:MM:SS string to time."""
    parts = str(value).strip().split(":")
    return time(int(parts[0]), int(parts[1]))


def import_metrics(file_path, period_start=None, period_end=None, reference_type=None):
    """
    Upsert POSMetrics time-window rows from CSV.
    Matches on (pos, reference_type, period_start, period_end,
                window_date, window_start, window_end).

    Period and reference_type are parsed from the filename if not supplied.

    CSV columns: cdb_code, window_date, window_start, window_end,
                 sales, interviews
    """
    if period_start is None or period_end is None or reference_type is None:
        period_start, period_end, reference_type = parse_period_from_filename(file_path)

    if reference_type not in POSMetrics.ReferenceType.values:
        raise ValueError(f"Unknown reference_type '{reference_type}'.")

    created = updated = skipped = 0
    errors = []

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            cdb_code = (row.get("cdb_code") or "").strip()
            if not cdb_code:
                errors.append(f"Row {i}: missing cdb_code, skipped.")
                skipped += 1
                continue

            try:
                pos = PointOfSale.objects.get(cdb_code=cdb_code)
            except PointOfSale.DoesNotExist:
                errors.append(f"Row {i}: POS '{cdb_code}' not found, skipped.")
                skipped += 1
                continue

            try:
                window_date = date.fromisoformat((row.get("window_date") or "").strip())
                window_start = _parse_time(row.get("window_start", ""))
                window_end = _parse_time(row.get("window_end", ""))
                sales = int(row.get("sales") or 0)
                interviews = int(row.get("interviews") or 0)
            except (ValueError, IndexError) as exc:
                errors.append(f"Row {i}: parse error for POS '{cdb_code}': {exc}")
                skipped += 1
                continue

            _, was_created = POSMetrics.objects.update_or_create(
                pos=pos,
                reference_type=reference_type,
                period_start=period_start,
                period_end=period_end,
                window_date=window_date,
                window_start=window_start,
                window_end=window_end,
                defaults={"sales": sales, "interviews": interviews},
            )
            if was_created:
                created += 1
            else:
                updated += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "period_start": str(period_start),
        "period_end": str(period_end),
        "reference_type": reference_type,
    }
