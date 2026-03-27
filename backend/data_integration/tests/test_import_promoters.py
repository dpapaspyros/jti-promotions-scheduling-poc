from django.test import TestCase

from data_integration.importers.promoters import import_promoters
from scheduling.models import Promoter

from .utils import write_csv

FIELDS = [
    "code",
    "username",
    "first_name",
    "last_name",
    "programme_type",
    "base_city",
    "team",
    "is_active",
]


def _row(**kwargs):
    defaults = {
        "code": "GR_001",
        "username": "SPC_Test User",
        "first_name": "Test",
        "last_name": "User",
        "programme_type": "Permanent",
        "base_city": "Athens",
        "team": "SOUTH TEAM",
        "is_active": "true",
    }
    return {**defaults, **kwargs}


class ImportPromotersCreateTest(TestCase):
    def test_creates_new_promoter(self):
        path = write_csv(self, [_row()], FIELDS)
        result = import_promoters(path)
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertTrue(Promoter.objects.filter(username="SPC_Test User").exists())

    def test_stores_all_fields_correctly(self):
        path = write_csv(self, [_row()], FIELDS)
        import_promoters(path)
        p = Promoter.objects.get(username="SPC_Test User")
        self.assertEqual(p.code, "GR_001")
        self.assertEqual(p.first_name, "Test")
        self.assertEqual(p.programme_type, "Permanent")
        self.assertEqual(p.base_city, "Athens")
        self.assertEqual(p.team, "SOUTH TEAM")
        self.assertTrue(p.is_active)

    def test_radical_code_stored_as_none_when_blank(self):
        path = write_csv(
            self,
            [_row(code="", username="SPC_Radical User", programme_type="Radical")],
            FIELDS,
        )
        import_promoters(path)
        p = Promoter.objects.get(username="SPC_Radical User")
        self.assertIsNone(p.code)

    def test_creates_multiple_promoters(self):
        rows = [
            _row(code="GR_001", username="SPC_User One"),
            _row(code="GR_002", username="SPC_User Two"),
            _row(code="GR_003", username="SPC_User Three"),
        ]
        path = write_csv(self, rows, FIELDS)
        result = import_promoters(path)
        self.assertEqual(result["created"], 3)
        self.assertEqual(Promoter.objects.count(), 3)


class ImportPromotersUpdateTest(TestCase):
    def setUp(self):
        Promoter.objects.create(
            username="SPC_Test User",
            first_name="Old",
            last_name="User",
            programme_type="Permanent",
        )

    def test_updates_existing_promoter(self):
        path = write_csv(self, [_row(first_name="Updated")], FIELDS)
        result = import_promoters(path)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(
            Promoter.objects.get(username="SPC_Test User").first_name, "Updated"
        )

    def test_idempotent_on_double_import(self):
        path = write_csv(self, [_row()], FIELDS)
        import_promoters(path)
        result = import_promoters(path)
        self.assertEqual(Promoter.objects.count(), 1)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 1)


class ImportPromotersSkipTest(TestCase):
    def test_skips_row_with_missing_username(self):
        path = write_csv(self, [_row(username="")], FIELDS)
        result = import_promoters(path)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["created"], 0)
        self.assertEqual(len(result["errors"]), 1)

    def test_skips_row_with_invalid_programme_type(self):
        path = write_csv(self, [_row(programme_type="Unknown")], FIELDS)
        result = import_promoters(path)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["created"], 0)
        self.assertEqual(len(result["errors"]), 1)

    def test_valid_rows_imported_despite_skipped_rows(self):
        rows = [
            _row(username="", code="GR_BAD"),
            _row(username="SPC_Good User", code="GR_002"),
        ]
        path = write_csv(self, rows, FIELDS)
        result = import_promoters(path)
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["skipped"], 1)
