from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Schedule

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


class ScheduleListAuthTest(APITestCase):
    def test_unauthenticated_returns_401(self):
        response = self.client.get("/api/schedules/")
        self.assertEqual(response.status_code, 401)


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
            "created_by",
            "created_at",
        ]:
            self.assertIn(field, data)
        self.assertEqual(data["created_by"], "admin")
        self.assertEqual(data["status"], "Draft")


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
        response = self.client.get("/api/schedules/")
        self.assertEqual(len(response.data), 3)

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
        response = self.client.get("/api/schedules/?status=Bogus")
        self.assertEqual(len(response.data), 0)
