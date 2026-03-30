"""Tests for schedule list/create, detail, and visit-list endpoints."""

from datetime import date

from rest_framework.test import APITestCase

from scheduling.models import Schedule

from ._helpers import (
    _make_pos,
    _make_promoter,
    _make_schedule,
    _make_user,
    _make_visit,
)


class ScheduleListAuthTest(APITestCase):
    def test_unauthenticated_returns_401(self):
        self.assertEqual(self.client.get("/api/schedules/").status_code, 401)


class ScheduleListTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)

    def test_empty_list(self):
        response = self.client.get("/api/schedules/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_returns_schedule(self):
        _make_schedule(self.user, "April", date(2026, 4, 1), date(2026, 4, 30))
        response = self.client.get("/api/schedules/")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "April")

    def test_ordered_newest_period_first(self):
        _make_schedule(self.user, "March", date(2026, 3, 1), date(2026, 3, 31))
        _make_schedule(self.user, "April", date(2026, 4, 1), date(2026, 4, 30))
        response = self.client.get("/api/schedules/")
        self.assertEqual(response.data[0]["name"], "April")
        self.assertEqual(response.data[1]["name"], "March")

    def test_serializes_expected_fields(self):
        _make_schedule(self.user, "April", date(2026, 4, 1), date(2026, 4, 30))
        data = self.client.get("/api/schedules/").data[0]
        for field in [
            "id",
            "name",
            "period_start",
            "period_end",
            "status",
            "score",
            "created_by",
            "created_at",
            "pos_count",
            "promoter_count",
        ]:
            self.assertIn(field, data)
        self.assertEqual(data["created_by"], "admin")
        self.assertEqual(data["status"], "Draft")

    def test_score_null_by_default(self):
        _make_schedule(self.user, "April", date(2026, 4, 1), date(2026, 4, 30))
        data = self.client.get("/api/schedules/").data[0]
        self.assertIsNone(data["score"])

    def test_pos_count_and_promoter_count(self):
        schedule = _make_schedule(
            self.user, "April", date(2026, 4, 1), date(2026, 4, 30)
        )
        schedule.included_pos.add(_make_pos())
        schedule.included_promoters.add(_make_promoter())
        data = self.client.get("/api/schedules/").data[0]
        self.assertEqual(data["pos_count"], 1)
        self.assertEqual(data["promoter_count"], 1)


class ScheduleListFilterTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)
        _make_schedule(
            self.user, "Draft S", date(2026, 4, 1), date(2026, 4, 30), "Draft"
        )
        _make_schedule(
            self.user, "Published S", date(2026, 5, 1), date(2026, 5, 31), "Published"
        )
        _make_schedule(
            self.user, "Archived S", date(2026, 2, 1), date(2026, 2, 28), "Archived"
        )

    def test_no_filter_returns_all(self):
        self.assertEqual(len(self.client.get("/api/schedules/").data), 3)

    def test_filter_by_draft(self):
        response = self.client.get("/api/schedules/?status=Draft")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Draft S")

    def test_filter_by_published(self):
        response = self.client.get("/api/schedules/?status=Published")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "Published")

    def test_filter_by_archived(self):
        response = self.client.get("/api/schedules/?status=Archived")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "Archived")

    def test_unknown_status_returns_empty(self):
        self.assertEqual(len(self.client.get("/api/schedules/?status=Bogus").data), 0)


class ScheduleCreateAuthTest(APITestCase):
    def test_unauthenticated_returns_401(self):
        self.assertEqual(self.client.post("/api/schedules/", {}).status_code, 401)


class ScheduleCreateTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)
        self.pos1 = _make_pos("POS001", "POS One")
        self.pos2 = _make_pos("POS002", "POS Two")
        self.promoter = _make_promoter("p1", "Alice", "Smith")

    def _payload(self, **overrides):
        data = {
            "name": "April 2026",
            "period_start": "2026-04-01",
            "period_end": "2026-04-30",
            "included_pos": [self.pos1.pk, self.pos2.pk],
            "included_promoters": [self.promoter.pk],
        }
        data.update(overrides)
        return data

    def test_valid_create_returns_201(self):
        self.assertEqual(
            self.client.post(
                "/api/schedules/", self._payload(), format="json"
            ).status_code,
            201,
        )

    def test_creates_with_draft_status(self):
        self.client.post("/api/schedules/", self._payload(), format="json")
        self.assertEqual(Schedule.objects.get().status, "Draft")

    def test_creates_with_current_user(self):
        self.client.post("/api/schedules/", self._payload(), format="json")
        self.assertEqual(Schedule.objects.get().created_by, self.user)

    def test_response_has_list_fields(self):
        response = self.client.post("/api/schedules/", self._payload(), format="json")
        for field in ["id", "name", "status", "pos_count", "promoter_count"]:
            self.assertIn(field, response.data)

    def test_pos_and_promoters_stored(self):
        self.client.post("/api/schedules/", self._payload(), format="json")
        schedule = Schedule.objects.get()
        self.assertEqual(schedule.included_pos.count(), 2)
        self.assertEqual(schedule.included_promoters.count(), 1)

    def test_period_end_before_start_returns_400(self):
        response = self.client.post(
            "/api/schedules/",
            self._payload(period_start="2026-04-30", period_end="2026-04-01"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_name_returns_400(self):
        payload = self._payload()
        del payload["name"]
        self.assertEqual(
            self.client.post("/api/schedules/", payload, format="json").status_code, 400
        )


class ScheduleDetailTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)
        self.schedule = _make_schedule(
            self.user, "April 2026", date(2026, 4, 1), date(2026, 4, 30)
        )

    def test_returns_schedule(self):
        response = self.client.get(f"/api/schedules/{self.schedule.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "April 2026")

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        self.assertEqual(
            self.client.get(f"/api/schedules/{self.schedule.pk}/").status_code, 401
        )

    def test_not_found_returns_404(self):
        self.assertEqual(self.client.get("/api/schedules/99999/").status_code, 404)


class ScheduleVisitListTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)
        self.schedule = _make_schedule(
            self.user, "April 2026", date(2026, 4, 1), date(2026, 4, 30)
        )
        self.pos = _make_pos()
        self.promoter = _make_promoter()

    def test_empty_list(self):
        response = self.client.get(f"/api/schedules/{self.schedule.pk}/visits/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_returns_visits(self):
        _make_visit(self.schedule, self.pos, self.promoter)
        response = self.client.get(f"/api/schedules/{self.schedule.pk}/visits/")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pos"]["cdb_code"], "POS001")

    def test_serializes_nested_pos_and_promoter(self):
        _make_visit(self.schedule, self.pos, self.promoter)
        data = self.client.get(f"/api/schedules/{self.schedule.pk}/visits/").data[0]
        self.assertIn("id", data["pos"])
        self.assertIn("name", data["pos"])
        self.assertIn("first_name", data["promoter"])
