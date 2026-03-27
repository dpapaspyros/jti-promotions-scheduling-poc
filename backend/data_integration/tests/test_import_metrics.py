import os
import tempfile
from datetime import date, time

from django.test import TestCase

from data_integration.importers.metrics import (
    import_metrics,
    parse_period_from_filename,
)
from metrics.models import POSMetrics
from scheduling.models import PointOfSale

from .utils import write_csv

FIELDS = [
    "cdb_code",
    "window_date",
    "window_start",
    "window_end",
    "sales",
    "interviews",
]

PERIOD_START = date(2026, 4, 1)
PERIOD_END = date(2026, 4, 30)
REFERENCE_TYPE = "previous_year"


def _make_pos(cdb_code="60-000001"):
    return PointOfSale.objects.create(cdb_code=cdb_code, name="Test POS")


def _row(**kwargs):
    defaults = {
        "cdb_code": "60-000001",
        "window_date": "2025-04-03",
        "window_start": "17:00",
        "window_end": "19:00",
        "sales": "10",
        "interviews": "25",
    }
    return {**defaults, **kwargs}


def _metrics_csv(test_case, rows=None):
    """Write a temp metrics CSV with the standard period filename."""
    if rows is None:
        rows = [_row()]
    return write_csv(test_case, rows, FIELDS)


class ParsePeriodFromFilenameTest(TestCase):
    def test_parses_previous_year(self):
        path = "/data/period_2026-04-01_2026-04-30_previous_year_metrics.csv"
        start, end, ref = parse_period_from_filename(path)
        self.assertEqual(start, date(2026, 4, 1))
        self.assertEqual(end, date(2026, 4, 30))
        self.assertEqual(ref, "previous_year")

    def test_parses_previous_month(self):
        path = "/data/period_2026-03-01_2026-03-31_previous_month_metrics.csv"
        start, end, ref = parse_period_from_filename(path)
        self.assertEqual(start, date(2026, 3, 1))
        self.assertEqual(end, date(2026, 3, 31))
        self.assertEqual(ref, "previous_month")

    def test_raises_on_invalid_filename(self):
        with self.assertRaises(ValueError):
            parse_period_from_filename("/data/bad_filename.csv")

    def test_raises_on_unknown_reference_type(self):
        with self.assertRaises(ValueError):
            parse_period_from_filename(
                "/data/period_2026-04-01_2026-04-30_previous_decade_metrics.csv"
            )


class ImportMetricsCreateTest(TestCase):
    def setUp(self):
        _make_pos()

    def test_creates_new_metric_row(self):
        path = _metrics_csv(self)
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(POSMetrics.objects.count(), 1)

    def test_stores_all_fields_correctly(self):
        path = _metrics_csv(self)
        import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        m = POSMetrics.objects.get()
        self.assertEqual(m.window_date, date(2025, 4, 3))
        self.assertEqual(m.window_start, time(17, 0))
        self.assertEqual(m.window_end, time(19, 0))
        self.assertEqual(m.sales, 10)
        self.assertEqual(m.interviews, 25)
        self.assertEqual(m.reference_type, "previous_year")

    def test_creates_multiple_windows_for_same_pos(self):
        rows = [
            _row(window_date="2025-04-03", window_start="09:00", window_end="11:00"),
            _row(window_date="2025-04-03", window_start="17:00", window_end="19:00"),
            _row(window_date="2025-04-05", window_start="15:00", window_end="17:00"),
        ]
        path = write_csv(self, rows, FIELDS)
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["created"], 3)
        self.assertEqual(POSMetrics.objects.count(), 3)


class ImportMetricsUpdateTest(TestCase):
    def setUp(self):
        self.pos = _make_pos()
        POSMetrics.objects.create(
            pos=self.pos,
            reference_type=REFERENCE_TYPE,
            period_start=PERIOD_START,
            period_end=PERIOD_END,
            window_date=date(2025, 4, 3),
            window_start=time(17, 0),
            window_end=time(19, 0),
            sales=5,
            interviews=10,
        )

    def test_updates_existing_metric_row(self):
        path = _metrics_csv(self, [_row(sales="15", interviews="30")])
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 1)
        m = POSMetrics.objects.get()
        self.assertEqual(m.sales, 15)
        self.assertEqual(m.interviews, 30)

    def test_idempotent_on_double_import(self):
        path = _metrics_csv(self)
        import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(POSMetrics.objects.count(), 1)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 1)


class ImportMetricsSkipTest(TestCase):
    def setUp(self):
        _make_pos()

    def test_skips_row_with_missing_cdb_code(self):
        path = _metrics_csv(self, [_row(cdb_code="")])
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["created"], 0)
        self.assertEqual(len(result["errors"]), 1)

    def test_skips_row_with_unknown_pos(self):
        path = _metrics_csv(self, [_row(cdb_code="99-NOTEXIST")])
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_skips_row_with_invalid_numeric_values(self):
        path = _metrics_csv(self, [_row(sales="not_a_number")])
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["skipped"], 1)

    def test_skips_row_with_invalid_date(self):
        path = _metrics_csv(self, [_row(window_date="not-a-date")])
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["skipped"], 1)

    def test_skips_row_with_invalid_time(self):
        path = _metrics_csv(self, [_row(window_start="bad-time")])
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["skipped"], 1)

    def test_valid_rows_imported_despite_skipped_rows(self):
        rows = [
            _row(cdb_code="99-MISSING"),
            _row(cdb_code="60-000001", sales="8"),
        ]
        path = write_csv(self, rows, FIELDS)
        result = import_metrics(path, PERIOD_START, PERIOD_END, REFERENCE_TYPE)
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["skipped"], 1)


class ImportMetricsFilenameParsingTest(TestCase):
    def setUp(self):
        _make_pos()

    def test_period_parsed_from_filename_when_not_supplied(self):
        """Period and reference_type inferred from a correctly named temp file."""
        import csv as csv_mod

        rows = [_row()]
        path = os.path.join(
            tempfile.gettempdir(),
            "period_2026-04-01_2026-04-30_previous_year_metrics.csv",
        )
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv_mod.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(os.unlink, path)

        result = import_metrics(f.name)
        self.assertEqual(result["period_start"], "2026-04-01")
        self.assertEqual(result["period_end"], "2026-04-30")
        self.assertEqual(result["reference_type"], "previous_year")
        self.assertEqual(result["created"], 1)
