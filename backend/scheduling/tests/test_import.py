"""Tests for the XLSX schedule import endpoint."""

import io
from datetime import date

from rest_framework.test import APITestCase

from scheduling.models import ScheduledVisit

from ._helpers import (
    _make_pos,
    _make_promoter,
    _make_schedule,
    _make_user,
    _make_visit,
    _make_xlsx,
)


class ScheduleImportTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)
        self.pos = _make_pos("POS001", "Test POS")
        self.promoter = _make_promoter("alice", "Alice", "Smith")
        self.schedule = _make_schedule(
            self.user, "April 2026", date(2026, 4, 1), date(2026, 4, 30)
        )

    def _post_xlsx(self, rows):
        buf = _make_xlsx(rows)
        return self.client.post(
            f"/api/schedules/{self.schedule.pk}/import/",
            {"file": buf},
            format="multipart",
        )

    def _valid_row(self, **overrides):
        row = [
            "W1",
            "2026-04-03",
            "09:00",
            "11:00",
            "POS001",
            "Test POS",
            "Athens",
            "Strategic",
            "Alice Smith",
            "Permanent",
            "Peak window.",
        ]
        for i, val in overrides.items():
            row[i] = val
        return row

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.post(
            f"/api/schedules/{self.schedule.pk}/import/", {}, format="multipart"
        )
        self.assertEqual(response.status_code, 401)

    def test_not_found_returns_404(self):
        buf = _make_xlsx([self._valid_row()])
        self.assertEqual(
            self.client.post(
                "/api/schedules/99999/import/", {"file": buf}, format="multipart"
            ).status_code,
            404,
        )

    def test_no_file_returns_400(self):
        self.assertEqual(
            self.client.post(
                f"/api/schedules/{self.schedule.pk}/import/", {}, format="multipart"
            ).status_code,
            400,
        )

    def test_invalid_file_returns_400(self):
        bad_file = io.BytesIO(b"not an xlsx file")
        bad_file.name = "bad.xlsx"
        self.assertEqual(
            self.client.post(
                f"/api/schedules/{self.schedule.pk}/import/",
                {"file": bad_file},
                format="multipart",
            ).status_code,
            400,
        )

    def test_valid_import_creates_visit(self):
        response = self._post_xlsx([self._valid_row()])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["visits"]), 1)
        self.assertEqual(
            ScheduledVisit.objects.filter(schedule=self.schedule).count(), 1
        )

    def test_imported_visit_has_correct_fields(self):
        self._post_xlsx([self._valid_row()])
        visit = ScheduledVisit.objects.get(schedule=self.schedule)
        self.assertEqual(visit.pos, self.pos)
        self.assertEqual(visit.date, date(2026, 4, 3))
        self.assertEqual(str(visit.start_time)[:5], "09:00")
        self.assertEqual(str(visit.end_time)[:5], "11:00")
        self.assertEqual(visit.week_label, "W1")

    def test_import_clears_existing_visits(self):
        _make_visit(self.schedule, self.pos, self.promoter)
        self._post_xlsx([self._valid_row()])
        self.assertEqual(
            ScheduledVisit.objects.filter(schedule=self.schedule).count(), 1
        )

    def test_promoter_resolved_by_full_name(self):
        self._post_xlsx([self._valid_row()])
        self.assertEqual(
            ScheduledVisit.objects.get(schedule=self.schedule).promoter, self.promoter
        )

    def test_unknown_promoter_name_leaves_promoter_null(self):
        row = self._valid_row()
        row[8] = "Unknown Person"
        self._post_xlsx([row])
        self.assertIsNone(ScheduledVisit.objects.get(schedule=self.schedule).promoter)

    def test_unknown_cdb_code_skipped_with_error(self):
        row = self._valid_row()
        row[4] = "BADCODE"
        response = self._post_xlsx([row])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["visits"]), 0)
        self.assertEqual(len(response.data["errors"]), 1)
        self.assertIn("BADCODE", response.data["errors"][0])

    def test_date_outside_period_skipped_with_error(self):
        row = self._valid_row()
        row[1] = "2026-06-01"
        response = self._post_xlsx([row])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["visits"]), 0)
        self.assertEqual(len(response.data["errors"]), 1)

    def test_missing_date_skipped_with_error(self):
        row = self._valid_row()
        row[1] = None
        response = self._post_xlsx([row])
        self.assertEqual(len(response.data["visits"]), 0)
        self.assertEqual(len(response.data["errors"]), 1)

    def test_missing_cdb_code_skipped_with_error(self):
        row = self._valid_row()
        row[4] = None
        response = self._post_xlsx([row])
        self.assertEqual(len(response.data["visits"]), 0)

    def test_multiple_rows_partial_success(self):
        bad_row = self._valid_row()
        bad_row[4] = "BADCODE"
        response = self._post_xlsx([self._valid_row(), bad_row])
        self.assertEqual(len(response.data["visits"]), 1)
        self.assertEqual(len(response.data["errors"]), 1)

    def test_week_label_falls_back_to_computed(self):
        row = self._valid_row()
        row[0] = None
        self._post_xlsx([row])
        self.assertEqual(
            ScheduledVisit.objects.get(schedule=self.schedule).week_label, "W1"
        )
