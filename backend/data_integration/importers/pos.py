import csv

from scheduling.models import PointOfSale

VALID_PRIORITIES = {c.value for c in PointOfSale.Priority}


def import_pos(file_path):
    """
    Upsert Points of Sale from CSV. Matches on cdb_code.
    Returns dict with created/updated/skipped counts and any row errors.
    """
    created = updated = skipped = 0
    errors = []

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            cdb_code = (row.get("cdb_code") or "").strip()
            if not cdb_code:
                errors.append(f"Row {i}: missing cdb_code, skipped.")
                skipped += 1
                continue

            priority = (row.get("priority") or "").strip()
            if priority and priority not in VALID_PRIORITIES:
                priority = ""

            defaults = {
                "name": (row.get("name") or "").strip(),
                "pos_type": (row.get("pos_type") or "").strip(),
                "priority": priority,
                "address": (row.get("address") or "").strip(),
                "city": (row.get("city") or "").strip(),
                "county": (row.get("county") or "").strip(),
                "department": (row.get("department") or "").strip(),
                "district": (row.get("district") or "").strip(),
                "territory": (row.get("territory") or "").strip(),
                "warehouse": (row.get("warehouse") or "").strip(),
                "chain": (row.get("chain") or "").strip(),
                "contractor": (row.get("contractor") or "").strip(),
                "telephone": (row.get("telephone") or "").strip(),
                "mobile": (row.get("mobile") or "").strip(),
                "is_active": row.get("is_active", "true").strip().lower() != "false",
            }

            _, was_created = PointOfSale.objects.update_or_create(
                cdb_code=cdb_code, defaults=defaults
            )
            if was_created:
                created += 1
            else:
                updated += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
