"""Shared test fixtures and factory helpers."""

import io
from datetime import date

import openpyxl
from django.contrib.auth import get_user_model

from scheduling.models import PointOfSale, Promoter, Schedule, ScheduledVisit

User = get_user_model()


def _make_user(username="admin"):
    return User.objects.create_user(username=username, password="pass")


def _make_schedule(user, name, period_start, period_end, status="Draft"):
    return Schedule.objects.create(
        name=name,
        period_start=period_start,
        period_end=period_end,
        status=status,
        created_by=user,
    )


def _make_pos(cdb_code="POS001", name="Test POS", city="Athens", is_active=True):
    return PointOfSale.objects.create(
        cdb_code=cdb_code, name=name, city=city, is_active=is_active
    )


def _make_promoter(username="promo1", first_name="Alice", last_name="Smith"):
    return Promoter.objects.create(
        username=username,
        first_name=first_name,
        last_name=last_name,
        programme_type="Permanent",
    )


def _make_visit(schedule, pos, promoter=None, visit_date=None, **kwargs):
    return ScheduledVisit.objects.create(
        schedule=schedule,
        pos=pos,
        promoter=promoter,
        date=visit_date or date(2026, 4, 3),
        start_time=kwargs.get("start_time", "09:00"),
        end_time=kwargs.get("end_time", "11:00"),
        programme_type=kwargs.get("programme_type", "Permanent"),
        week_label=kwargs.get("week_label", "W1"),
        comments=kwargs.get("comments", ""),
    )


def _make_xlsx(rows):
    """Create an in-memory xlsx with the standard import header + given rows."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        [
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
    )
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    buf.name = "schedule.xlsx"
    return buf
