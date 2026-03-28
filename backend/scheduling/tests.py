from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import PointOfSale, Promoter, Schedule, ScheduledVisit

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


def _make_pos(cdb_code="POS001", name="Test POS", is_active=True):
    return PointOfSale.objects.create(cdb_code=cdb_code, name=name, is_active=is_active)


def _make_promoter(username="promo1", first_name="Alice", last_name="Smith"):
    return Promoter.objects.create(
        username=username,
        first_name=first_name,
        last_name=last_name,
        programme_type="Permanent",
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
            "pos_count",
            "promoter_count",
        ]:
            self.assertIn(field, data)
        self.assertEqual(data["created_by"], "admin")
        self.assertEqual(data["status"], "Draft")

    def test_pos_count_and_promoter_count(self):
        schedule = _make_schedule(
            self.user, "April", date(2026, 4, 1), date(2026, 4, 30)
        )
        pos = _make_pos()
        promoter = _make_promoter()
        schedule.included_pos.add(pos)
        schedule.included_promoters.add(promoter)
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


class ScheduleCreateAuthTest(APITestCase):
    def test_unauthenticated_returns_401(self):
        response = self.client.post("/api/schedules/", {})
        self.assertEqual(response.status_code, 401)


class ScheduleCreateTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)
        self.pos1 = _make_pos("POS001", "POS One")
        self.pos2 = _make_pos("POS002", "POS Two")
        self.promoter1 = _make_promoter("p1", "Alice", "Smith")
        self.promoter2 = _make_promoter("p2", "Bob", "Jones")

    def _payload(self, **overrides):
        data = {
            "name": "April 2026",
            "period_start": "2026-04-01",
            "period_end": "2026-04-30",
            "included_pos": [self.pos1.pk, self.pos2.pk],
            "included_promoters": [self.promoter1.pk],
        }
        data.update(overrides)
        return data

    def test_valid_create_returns_201(self):
        response = self.client.post("/api/schedules/", self._payload(), format="json")
        self.assertEqual(response.status_code, 201)

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

    def test_overlapping_period_returns_400(self):
        _make_schedule(self.user, "Existing", date(2026, 4, 1), date(2026, 4, 30))
        response = self.client.post("/api/schedules/", self._payload(), format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_name_returns_400(self):
        payload = self._payload()
        del payload["name"]
        response = self.client.post("/api/schedules/", payload, format="json")
        self.assertEqual(response.status_code, 400)


class PointOfSaleListTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/pos/").status_code, 401)

    def test_returns_active_pos(self):
        _make_pos("A001", "Active POS", is_active=True)
        _make_pos("A002", "Inactive POS", is_active=False)
        response = self.client.get("/api/pos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["cdb_code"], "A001")

    def test_serializes_expected_fields(self):
        _make_pos()
        data = self.client.get("/api/pos/").data[0]
        for field in ["id", "cdb_code", "name", "city", "priority"]:
            self.assertIn(field, data)


class PromoterListTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/promoters/").status_code, 401)

    def test_returns_active_promoters(self):
        _make_promoter("active_user", "Alice", "Smith")
        Promoter.objects.create(
            username="inactive_user",
            first_name="Bob",
            last_name="Jones",
            programme_type="Permanent",
            is_active=False,
        )
        response = self.client.get("/api/promoters/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "active_user")

    def test_serializes_expected_fields(self):
        _make_promoter()
        data = self.client.get("/api/promoters/").data[0]
        for field in [
            "id",
            "username",
            "first_name",
            "last_name",
            "programme_type",
            "team",
        ]:
            self.assertIn(field, data)


# ── Schedule detail ─────────────────────────────────────────────────────────


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


# ── Visit list ──────────────────────────────────────────────────────────────


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
        ScheduledVisit.objects.create(
            schedule=self.schedule,
            pos=self.pos,
            promoter=self.promoter,
            date=date(2026, 4, 3),
            start_time="09:00",
            end_time="11:00",
            programme_type="Permanent",
            week_label="W1",
        )
        response = self.client.get(f"/api/schedules/{self.schedule.pk}/visits/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pos"]["cdb_code"], "POS001")

    def test_serializes_nested_pos_and_promoter(self):
        ScheduledVisit.objects.create(
            schedule=self.schedule,
            pos=self.pos,
            promoter=self.promoter,
            date=date(2026, 4, 3),
            start_time="09:00",
            end_time="11:00",
            programme_type="Permanent",
            week_label="W1",
        )
        data = self.client.get(f"/api/schedules/{self.schedule.pk}/visits/").data[0]
        self.assertIn("id", data["pos"])
        self.assertIn("name", data["pos"])
        self.assertIn("first_name", data["promoter"])


# ── AI generation ───────────────────────────────────────────────────────────

_MOCK_AI_RESULT = {
    "summary": "Scheduled 2 visits based on peak windows.",
    "visits": [
        {
            "pos_id": None,  # filled in setUp
            "promoter_id": None,
            "date": "2026-04-03",
            "start_time": "09:00",
            "end_time": "11:00",
            "reason": "Peak morning window.",
        },
        {
            "pos_id": None,
            "promoter_id": None,
            "date": "2026-04-10",
            "start_time": "15:00",
            "end_time": "17:00",
            "reason": "Afternoon peak.",
        },
    ],
    "usage": {"prompt_tokens": 500, "completion_tokens": 200, "total_tokens": 700},
}


@override_settings(OPENAI_API_KEY="test-key")
class ScheduleGenerateTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)
        self.pos = _make_pos()
        self.promoter = _make_promoter()
        self.schedule = _make_schedule(
            self.user, "April 2026", date(2026, 4, 1), date(2026, 4, 30)
        )
        self.schedule.included_pos.add(self.pos)
        self.schedule.included_promoters.add(self.promoter)

        # Patch mock result with real IDs
        self.mock_result = {
            **_MOCK_AI_RESULT,
            "visits": [
                {**v, "pos_id": self.pos.pk, "promoter_id": self.promoter.pk}
                for v in _MOCK_AI_RESULT["visits"]
            ],
        }

    def _post(self, payload=None):
        return self.client.post(
            f"/api/schedules/{self.schedule.pk}/generate/",
            payload or {},
            format="json",
        )

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        self.assertEqual(self._post().status_code, 401)

    @patch("scheduling.views.generate_schedule")
    def test_returns_200_with_visits(self, mock_gen):
        mock_gen.return_value = self.mock_result
        response = self._post({"optimization_goal": "sales * 10 + interviews"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["visits"]), 2)
        self.assertIn("summary", response.data)
        self.assertIn("usage", response.data)

    @patch("scheduling.views.generate_schedule")
    def test_clears_existing_visits_before_creating(self, mock_gen):
        mock_gen.return_value = self.mock_result
        # Pre-existing visit
        ScheduledVisit.objects.create(
            schedule=self.schedule,
            pos=self.pos,
            date=date(2026, 4, 1),
            start_time="09:00",
            end_time="11:00",
            programme_type="Permanent",
            week_label="W1",
        )
        self._post()
        self.assertEqual(
            ScheduledVisit.objects.filter(schedule=self.schedule).count(), 2
        )

    @patch("scheduling.views.generate_schedule")
    def test_visits_saved_to_db(self, mock_gen):
        mock_gen.return_value = self.mock_result
        self._post()
        visits = ScheduledVisit.objects.filter(schedule=self.schedule).order_by("date")
        self.assertEqual(visits.count(), 2)
        self.assertEqual(visits[0].date, date(2026, 4, 3))
        self.assertEqual(str(visits[0].start_time)[:5], "09:00")
        self.assertEqual(visits[0].promoter, self.promoter)
        self.assertEqual(visits[0].comments, "Peak morning window.")

    @patch("scheduling.views.generate_schedule")
    def test_week_label_computed_correctly(self, mock_gen):
        mock_gen.return_value = self.mock_result
        self._post()
        visits = ScheduledVisit.objects.filter(schedule=self.schedule).order_by("date")
        self.assertEqual(visits[0].week_label, "W1")  # Apr 3 = day 2 → W1
        self.assertEqual(visits[1].week_label, "W2")  # Apr 10 = day 9 → W2

    @patch("scheduling.views.generate_schedule")
    def test_unknown_pos_id_skipped_and_reported(self, mock_gen):
        bad_result = {
            **self.mock_result,
            "visits": [
                {
                    "pos_id": 99999,
                    "promoter_id": self.promoter.pk,
                    "date": "2026-04-03",
                    "start_time": "09:00",
                    "end_time": "11:00",
                    "reason": "test",
                }
            ],
        }
        mock_gen.return_value = bad_result
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["visits"]), 0)
        self.assertEqual(len(response.data["errors"]), 1)

    @patch("scheduling.views.generate_schedule")
    def test_ai_error_returns_502(self, mock_gen):
        mock_gen.side_effect = Exception("OpenAI timeout")
        response = self._post()
        self.assertEqual(response.status_code, 502)
        self.assertIn("error", response.data)

    @override_settings(OPENAI_API_KEY="")
    def test_missing_api_key_returns_503(self):
        response = self._post()
        self.assertEqual(response.status_code, 503)
