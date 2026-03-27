import csv

from scheduling.models import Promoter


def import_promoters(file_path):
    """
    Upsert promoters from CSV. Matches on username.
    Returns dict with created/updated/skipped counts and any row errors.
    """
    created = updated = skipped = 0
    errors = []

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            username = (row.get("username") or "").strip()
            if not username:
                errors.append(f"Row {i}: missing username, skipped.")
                skipped += 1
                continue

            programme_type = (row.get("programme_type") or "").strip()
            if programme_type not in Promoter.ProgrammeType.values:
                errors.append(
                    f"Row {i}: invalid programme_type '{programme_type}', skipped."
                )
                skipped += 1
                continue

            defaults = {
                "code": (row.get("code") or "").strip() or None,
                "first_name": (row.get("first_name") or "").strip(),
                "last_name": (row.get("last_name") or "").strip(),
                "programme_type": programme_type,
                "base_city": (row.get("base_city") or "").strip(),
                "team": (row.get("team") or "").strip(),
                "is_active": row.get("is_active", "true").strip().lower() != "false",
            }

            _, was_created = Promoter.objects.update_or_create(
                username=username, defaults=defaults
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
