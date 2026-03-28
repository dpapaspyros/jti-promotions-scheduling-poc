"""Tests for the schedule publish endpoint."""

from datetime import date

from rest_framework.test import APITestCase

from ._helpers import _make_schedule, _make_user


class SchedulePublishTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)
        self.schedule = _make_schedule(
            self.user, "April 2026", date(2026, 4, 1), date(2026, 4, 30), "Draft"
        )

    def _post(self, pk=None):
        return self.client.post(f"/api/schedules/{pk or self.schedule.pk}/publish/")

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        self.assertEqual(self._post().status_code, 401)

    def test_not_found_returns_404(self):
        self.assertEqual(self._post(pk=99999).status_code, 404)

    def test_draft_publish_returns_200(self):
        self.assertEqual(self._post().status_code, 200)

    def test_status_set_to_published(self):
        self._post()
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.status, "Published")

    def test_response_contains_published_status(self):
        self.assertEqual(self._post().data["status"], "Published")

    def test_response_serializes_schedule_fields(self):
        response = self._post()
        for field in ["id", "name", "status", "period_start", "period_end"]:
            self.assertIn(field, response.data)

    def test_publishing_already_published_returns_400(self):
        self.schedule.status = "Published"
        self.schedule.save()
        self.assertEqual(self._post().status_code, 400)

    def test_publishing_archived_returns_400(self):
        self.schedule.status = "Archived"
        self.schedule.save()
        self.assertEqual(self._post().status_code, 400)

    def test_400_response_contains_error_message(self):
        self.schedule.status = "Published"
        self.schedule.save()
        self.assertIn("error", self._post().data)
