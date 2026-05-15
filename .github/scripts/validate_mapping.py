#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ALLOWED_ROLES = {"setter", "closer", "manager", "founder", "ops"}
ALLOWED_FLAGS = {"veteran", "leader"}
ALLOWED_MARKETS = {"AZ", "UT"}
SLACK_ID_RE = re.compile(r"^U[A-Z0-9]{8,11}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED_FIELDS = {
    "name", "ghl_name", "emails", "slack_id", "slack_display_name",
    "markets", "role", "flags", "include_in_brief", "ghl_user_id",
    "active", "inactive_since", "notes",
}


def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def main():
    path = Path("rep-slack-mapping.json")
    if not path.exists():
        fail("rep-slack-mapping.json not found at repo root")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        fail(f"Invalid JSON: {e}")

    if data.get("version") != 1:
        fail("Top-level 'version' must equal 1")

    reps = data.get("reps")
    if not isinstance(reps, list):
        fail("Top-level 'reps' must be an array")

    seen_slack_ids = {}
    seen_emails = {}
    errors = []

    for i, rep in enumerate(reps):
        prefix = f"reps[{i}] ({rep.get('name', '?')})"
        missing = REQUIRED_FIELDS - set(rep.keys())
        if missing:
            errors.append(f"{prefix}: missing fields: {sorted(missing)}")
            continue

        if not isinstance(rep["name"], str) or not rep["name"].strip():
            errors.append(f"{prefix}: 'name' must be a non-empty string")

        if rep["ghl_name"] is not None and not isinstance(rep["ghl_name"], str):
            errors.append(f"{prefix}: 'ghl_name' must be string or null")

        if not isinstance(rep["emails"], list) or not rep["emails"]:
            errors.append(f"{prefix}: 'emails' must be a non-empty array")
        else:
            for email in rep["emails"]:
                if not isinstance(email, str) or not EMAIL_RE.match(email):
                    errors.append(f"{prefix}: invalid email format: {email!r}")
                email_lc = email.lower() if isinstance(email, str) else ""
                if email_lc in seen_emails:
                    errors.append(
                        f"{prefix}: duplicate email {email_lc!r} "
                        f"also used by {seen_emails[email_lc]}"
                    )
                else:
                    seen_emails[email_lc] = rep.get("name", f"reps[{i}]")

        if rep["slack_id"] is not None:
            if not isinstance(rep["slack_id"], str) or not SLACK_ID_RE.match(rep["slack_id"]):
                errors.append(f"{prefix}: invalid slack_id format: {rep['slack_id']!r}")
            elif rep["slack_id"] in seen_slack_ids:
                errors.append(
                    f"{prefix}: duplicate slack_id {rep['slack_id']!r} "
                    f"also used by {seen_slack_ids[rep['slack_id']]}"
                )
            else:
                seen_slack_ids[rep["slack_id"]] = rep.get("name", f"reps[{i}]")

        if not isinstance(rep["markets"], list):
            errors.append(f"{prefix}: 'markets' must be an array")
        else:
            for m in rep["markets"]:
                if m not in ALLOWED_MARKETS:
                    errors.append(
                        f"{prefix}: market {m!r} not in {sorted(ALLOWED_MARKETS)}"
                    )

        if rep["role"] not in ALLOWED_ROLES:
            errors.append(
                f"{prefix}: role {rep['role']!r} not in {sorted(ALLOWED_ROLES)}"
            )

        if not isinstance(rep["flags"], list):
            errors.append(f"{prefix}: 'flags' must be an array")
        else:
            for f in rep["flags"]:
                if f not in ALLOWED_FLAGS:
                    errors.append(
                        f"{prefix}: flag {f!r} not in {sorted(ALLOWED_FLAGS)}"
                    )

        if not isinstance(rep["include_in_brief"], bool):
            errors.append(f"{prefix}: 'include_in_brief' must be boolean")

        if not isinstance(rep["active"], bool):
            errors.append(f"{prefix}: 'active' must be boolean")

        if rep["active"] is False and rep["inactive_since"] is None:
            errors.append(f"{prefix}: active=false requires inactive_since (ISO date)")
        if rep["inactive_since"] is not None:
            if not isinstance(rep["inactive_since"], str) or not ISO_DATE_RE.match(rep["inactive_since"]):
                errors.append(
                    f"{prefix}: inactive_since must be ISO date YYYY-MM-DD, got {rep['inactive_since']!r}"
                )

    if errors:
        for e in errors:
            print(f"::error::{e}")
        print(f"\n{len(errors)} validation error(s)")
        sys.exit(1)

    print(f"OK — {len(reps)} reps validated, no errors")


if __name__ == "__main__":
    main()
