from django.test import TestCase

from data_integration.importers.pos import import_pos
from scheduling.models import PointOfSale

from .utils import write_csv

FIELDS = [
    "cdb_code",
    "name",
    "pos_type",
    "priority",
    "address",
    "city",
    "county",
    "department",
    "district",
    "territory",
    "warehouse",
    "chain",
    "contractor",
    "telephone",
    "mobile",
    "is_active",
]


def _row(**kwargs):
    defaults = {
        "cdb_code": "60-000001",
        "name": "Test POS",
        "pos_type": "ΠΕΡΙΠΤΕΡΟ",
        "priority": "Strategic",
        "address": "Test Street 1",
        "city": "Athens",
        "county": "Attica",
        "department": "ΑΤΤΙΚΗ",
        "district": "CENTRAL (DKR)",
        "territory": "C_01. TEST",
        "warehouse": "TEST WH",
        "chain": "",
        "contractor": "JTI",
        "telephone": "2101234567",
        "mobile": "",
        "is_active": "true",
    }
    return {**defaults, **kwargs}


class ImportPOSCreateTest(TestCase):
    def test_creates_new_pos(self):
        path = write_csv(self, [_row()], FIELDS)
        result = import_pos(path)
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertTrue(PointOfSale.objects.filter(cdb_code="60-000001").exists())

    def test_stores_all_fields_correctly(self):
        path = write_csv(self, [_row()], FIELDS)
        import_pos(path)
        pos = PointOfSale.objects.get(cdb_code="60-000001")
        self.assertEqual(pos.name, "Test POS")
        self.assertEqual(pos.priority, "Strategic")
        self.assertEqual(pos.city, "Athens")
        self.assertEqual(pos.contractor, "JTI")
        self.assertTrue(pos.is_active)

    def test_creates_multiple_pos(self):
        rows = [
            _row(cdb_code="60-000001", name="POS One"),
            _row(cdb_code="60-000002", name="POS Two"),
        ]
        path = write_csv(self, rows, FIELDS)
        result = import_pos(path)
        self.assertEqual(result["created"], 2)
        self.assertEqual(PointOfSale.objects.count(), 2)


class ImportPOSUpdateTest(TestCase):
    def setUp(self):
        PointOfSale.objects.create(cdb_code="60-000001", name="Old Name")

    def test_updates_existing_pos(self):
        path = write_csv(self, [_row(name="New Name")], FIELDS)
        result = import_pos(path)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(PointOfSale.objects.get(cdb_code="60-000001").name, "New Name")

    def test_idempotent_on_double_import(self):
        path = write_csv(self, [_row()], FIELDS)
        import_pos(path)
        result = import_pos(path)
        self.assertEqual(PointOfSale.objects.count(), 1)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 1)


class ImportPOSSkipTest(TestCase):
    def test_skips_row_with_missing_cdb_code(self):
        path = write_csv(self, [_row(cdb_code="")], FIELDS)
        result = import_pos(path)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["created"], 0)
        self.assertEqual(len(result["errors"]), 1)

    def test_invalid_priority_stored_as_blank(self):
        path = write_csv(self, [_row(priority="InvalidTier")], FIELDS)
        import_pos(path)
        pos = PointOfSale.objects.get(cdb_code="60-000001")
        self.assertEqual(pos.priority, "")

    def test_valid_rows_imported_despite_skipped_rows(self):
        rows = [
            _row(cdb_code=""),
            _row(cdb_code="60-000002", name="Valid POS"),
        ]
        path = write_csv(self, rows, FIELDS)
        result = import_pos(path)
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["skipped"], 1)
