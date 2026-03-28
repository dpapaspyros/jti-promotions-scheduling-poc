"""Shared constants and helper functions used across view modules."""

import datetime

from ..models import ScheduledVisit

_XLSX_HEADERS = [
    "Week",
    "Date",
    "Start Time",
    "End Time",
    "CDB Code",
    "POS Name",
    "City",
    "Priority",
    "Promoter",
    "Programme",
    "AI Reasoning",
]
_XLSX_COL_WIDTHS = [8, 13, 11, 11, 13, 28, 16, 13, 28, 13, 55]


def _create_visits_from_ai(schedule, visit_data, pos_map, promoter_map):
    """
    Delete all existing visits for *schedule* and create new ones from
    the AI-generated *visit_data* list (dicts with pos_id, promoter_id, …).

    Returns (created_visits, errors).
    """
    schedule.visits.all().delete()
    created, errors = [], []

    for v in visit_data:
        pos = pos_map.get(v.get("pos_id"))
        if pos is None:
            errors.append(f"Unknown pos_id {v.get('pos_id')} — skipped.")
            continue
        promoter = promoter_map.get(v.get("promoter_id"))
        try:
            date_obj = datetime.date.fromisoformat(v["date"])
            week_num = (date_obj - schedule.period_start).days // 7 + 1
            visit = ScheduledVisit.objects.create(
                schedule=schedule,
                pos=pos,
                promoter=promoter,
                date=date_obj,
                start_time=v["start_time"],
                end_time=v["end_time"],
                programme_type=(promoter.programme_type if promoter else "Radical"),
                week_label=f"W{week_num}",
                comments=v.get("reason", ""),
            )
            created.append(visit)
        except Exception as exc:
            errors.append(str(exc))

    return created, errors


def _parse_xlsx_time(val) -> str:
    """Return HH:MM string from an openpyxl cell value."""
    if isinstance(val, datetime.time):
        return val.strftime("%H:%M")
    if isinstance(val, datetime.datetime):
        return val.strftime("%H:%M")
    return str(val).strip()[:5]


def _parse_xlsx_date(val) -> datetime.date:
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    return datetime.date.fromisoformat(str(val).strip())
