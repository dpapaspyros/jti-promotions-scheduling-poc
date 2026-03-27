import csv
import os
import tempfile


def write_csv(test_case, rows, fieldnames):
    """Write rows to a temp CSV file; auto-deletes when test ends."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
    )
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    f.close()
    test_case.addCleanup(os.unlink, f.name)
    return f.name
