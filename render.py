#!/usr/bin/env python3
"""
render.py — WorkinX PM Report Renderer
Takes Claude's compact JSON blob → generates full branded HTML report.
Zero Claude API tokens consumed here.

Usage:
  python render.py <json_file_or_stdin> [output.html]

Examples:
  python render.py kavitha_data.json kavitha_report.html
  echo '{...}' | python render.py - report.html
  python render.py kavitha_data.json          # outputs to kavitha_report.html
"""

import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
TEMPLATE_PATH = SCRIPT_DIR / "template.html"

IST = timezone(timedelta(hours=5, minutes=30))

# ── health scoring ───────────────────────────────────────────────────────────
def compute_health(data: dict) -> tuple[str, str, str]:
    """Returns (css_class, icon, label) from the JSON or recomputes from tasks."""
    # Try to use health from JSON if provided
    h = data.get("health", "").upper()
    if not h:
        esc = sum(1 for b in data["brands"] for t in b["tasks"] if "ESCALATION" in t.get("flags", []))
        incomplete = sum(1 for b in data["brands"] for t in b["tasks"] if "INCOMPLETE" in t.get("flags", []))
        if esc > 2 or incomplete > 15:
            h = "RED"
        elif esc <= 2 or incomplete <= 15:
            h = "YELLOW" if (esc > 0 or incomplete > 5) else "GREEN"
        else:
            h = "GREEN"

    mapping = {
        "GREEN":  ("health-green",  "🟢", "GREEN"),
        "YELLOW": ("health-yellow", "🟡", "YELLOW"),
        "RED":    ("health-red",    "🔴", "RED"),
    }
    return mapping.get(h, mapping["GREEN"])

# ── render ────────────────────────────────────────────────────────────────────
def render(data: dict, template_str: str) -> str:
    pm_name    = data.get("pm_name", "PM")
    report_type = data.get("report_type", "MORNING BRIEF")  # MORNING BRIEF | EOD REPORT
    generated_at = data.get("generated_at", datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST"))
    date_label   = data.get("date_label", datetime.now(IST).strftime("%A, %d %b %Y"))

    health_class, health_icon, health_label = compute_health(data)

    report_title = f"WorkinX {report_type} — {pm_name} | {date_label}"
    footer_text  = f"WorkinX PM Intelligence · {report_type} · {pm_name} · {generated_at} · Auto-generated — do not edit manually"

    # Embed JSON for JS
    report_data_json = json.dumps(data, ensure_ascii=False)

    html = template_str
    replacements = {
        "{{REPORT_TITLE}}":      report_title,
        "{{HEALTH_CLASS}}":      health_class,
        "{{HEALTH_ICON}}":       health_icon,
        "{{HEALTH_LABEL}}":      health_label,
        "{{GENERATED_AT}}":      generated_at,
        "{{FOOTER_TEXT}}":       footer_text,
        "{{REPORT_DATA_JSON}}":  report_data_json,
    }
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    return html

# ── validate JSON schema ──────────────────────────────────────────────────────
def validate(data: dict) -> list[str]:
    errors = []
    if "brands" not in data:
        errors.append("Missing 'brands' key at root")
        return errors
    for i, brand in enumerate(data["brands"]):
        if "name" not in brand:
            errors.append(f"brands[{i}] missing 'name'")
        for j, task in enumerate(brand.get("tasks", [])):
            if "id" not in task:
                errors.append(f"brands[{i}].tasks[{j}] missing 'id'")
            if "name" not in task:
                errors.append(f"brands[{i}].tasks[{j}] missing 'name'")
            if "flags" not in task:
                errors.append(f"brands[{i}].tasks[{j}] missing 'flags'")
    return errors

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    # ── load template ──
    if not TEMPLATE_PATH.exists():
        print(f"ERROR: template.html not found at {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)
    template_str = TEMPLATE_PATH.read_text(encoding="utf-8")

    # ── determine input ──
    if len(sys.argv) < 2:
        print("Usage: python render.py <input.json|-> [output.html]", file=sys.stderr)
        sys.exit(1)

    input_arg = sys.argv[1]
    if input_arg == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(input_arg).read_text(encoding="utf-8")

    # Strip code fences if Claude wrapped the JSON in ```json ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    # ── validate ──
    errors = validate(data)
    if errors:
        for err in errors:
            print(f"WARN: {err}", file=sys.stderr)

    # ── determine output path ──
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        # derive from input filename
        stem = Path(input_arg).stem if input_arg != "-" else "report"
        out_path = SCRIPT_DIR / f"{stem}_report.html"

    # ── render + write ──
    html = render(data, template_str)
    out_path.write_text(html, encoding="utf-8")
    print(out_path.resolve())  # stdout: path to generated file (used by shell script)

if __name__ == "__main__":
    main()
