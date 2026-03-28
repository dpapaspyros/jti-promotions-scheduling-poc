"""Tests for Point-of-Sale and Promoter list endpoints."""

from rest_framework.test import APITestCase

from scheduling.models import Promoter

from ._helpers import _make_pos, _make_promoter, _make_user


class PointOfSaleListTest(APITestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/pos/").status_code, 401)

    def test_returns_active_pos_only(self):
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

    def test_returns_active_promoters_only(self):
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
