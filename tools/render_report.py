"""Render a research report.json into a themed PDF.

Validates against tools/report_schema.json and fails loudly on a bad report
rather than emitting a silently half-empty PDF. Deterministic execution only --
no content is invented, reworded, or omitted here.

Usage:
    python tools/render_report.py --run-id 20260802-153000-eu-ai-act
    python tools/render_report.py --run-id <id> --theme market
    python tools/render_report.py --input path/to/report.json --output out.pdf
    python tools/render_report.py --run-id <id> --keep-html   # debug the layout
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup, escape

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
THEME_DIR = TEMPLATE_DIR / "themes"
SCHEMA_PATH = Path(__file__).resolve().parent / "report_schema.json"

VALID_THEMES = ["academic", "regulatory", "market", "technical"]

PAGE_MARGIN = {"top": "18mm", "bottom": "20mm", "left": "22mm", "right": "22mm"}


def paragraphs(text):
    """Blank-line-separated text -> <p> blocks. Escapes first; no HTML passes through."""
    if not text:
        return Markup("")
    blocks = [b.strip() for b in re.split(r"\n\s*\n", str(text).strip()) if b.strip()]
    if not blocks:
        return Markup("")
    return Markup("".join(f"<p>{escape(b)}</p>".replace("\n", "<br>") for b in blocks))


def validate(report):
    """Validate against the schema. Returns a list of human-readable error strings."""
    try:
        import jsonschema
    except ImportError:
        print("WARNING: jsonschema not installed -- skipping validation.", file=sys.stderr)
        return []

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(report), key=lambda e: list(e.path)):
        location = "report" + "".join(f"[{p!r}]" for p in err.path)
        errors.append(f"{location}: {err.message}")
    return errors


def check_citations(report):
    """Cross-check that every cited source_id resolves to a source. Schema can't do this."""
    known = {s["id"] for s in report.get("sources", [])}
    problems = []

    for i, f in enumerate(report.get("key_findings", []), 1):
        for sid in f.get("source_ids", []):
            if sid not in known:
                problems.append(
                    f"key_findings[{i}] ({f.get('heading', '?')[:40]}) cites "
                    f"unknown source id {sid!r}"
                )

    for i, c in enumerate(report.get("conflicts", []), 1):
        for key in ("supporting_ids", "contradicting_ids"):
            for sid in c.get(key, []):
                if sid not in known:
                    problems.append(f"conflicts[{i}].{key} cites unknown source id {sid!r}")

    seen = set()
    for s in report.get("sources", []):
        if s["id"] in seen:
            problems.append(f"duplicate source id {s['id']!r}")
        seen.add(s["id"])

    cited = {
        sid for f in report.get("key_findings", []) for sid in f.get("source_ids", [])
    }
    uncited = known - cited
    if uncited:
        # Not fatal -- appendix-only context sources are legitimate.
        print(
            f"NOTE: {len(uncited)} source(s) in the appendix are not cited by any "
            f"finding: {', '.join(sorted(uncited))}",
            file=sys.stderr,
        )

    return problems


def format_generated(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%d %B %Y")
    except (ValueError, TypeError):
        return str(value)


def build_html(report, theme):
    theme_path = THEME_DIR / f"{theme}.css"
    if not theme_path.exists():
        sys.exit(
            f"ERROR: theme {theme!r} not found at {theme_path}.\n"
            f"Available: {', '.join(sorted(p.stem for p in THEME_DIR.glob('*.css')))}"
        )

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["paragraphs"] = paragraphs

    sources = report.get("sources", [])
    tier_counts = {t: sum(1 for s in sources if s.get("tier") == t) for t in "ABC"}

    prox_order = ["local", "regional", "global"]
    raw_geo = {
        t: sum(1 for s in sources if s.get("proximity_tier") == t) for t in prox_order
    }
    geo_counts = [(t, n) for t, n in ((t, raw_geo[t]) for t in prox_order) if n]
    geo_max = max((n for _, n in geo_counts), default=1)

    template = env.get_template("report.html.j2")
    return template.render(
        report=report,
        # Markup(), not a plain str: autoescape would turn every quoted font name
        # into &#34; and silently drop the whole declaration. These are local
        # trusted files, never user input.
        base_css=Markup((TEMPLATE_DIR / "base.css").read_text(encoding="utf-8")),
        theme_css=Markup(theme_path.read_text(encoding="utf-8")),
        tier_counts=tier_counts,
        geo_counts=geo_counts,
        geo_max=geo_max,
        generated_display=format_generated(report.get("generated_at")),
    )


def render_pdf(html, out_path, report):
    from playwright.sync_api import sync_playwright

    label = escape(f"{report.get('topic', '')[:70]}")
    footer = f"""
    <div style="width:100%;font-family:Georgia,serif;font-size:7pt;color:#8b847b;
                padding:0 22mm;display:flex;justify-content:space-between;">
      <span>{label}</span>
      <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
    </div>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.emulate_media(media="print")
        page.pdf(
            path=str(out_path),
            format="A4",
            print_background=True,
            margin=PAGE_MARGIN,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=footer,
        )
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", help="run directory under .tmp/ containing report.json")
    ap.add_argument("--input", help="explicit path to a report.json (overrides --run-id)")
    ap.add_argument("--output", help="explicit output PDF path")
    ap.add_argument("--theme", choices=VALID_THEMES, help="override the report's theme")
    ap.add_argument("--keep-html", action="store_true", help="also write the HTML, for debugging")
    args = ap.parse_args()

    if not args.run_id and not args.input:
        ap.error("one of --run-id or --input is required")

    report_path = Path(args.input) if args.input else TMP_DIR / args.run_id / "report.json"
    if not report_path.exists():
        sys.exit(f"ERROR: {report_path} not found. Stage 4 writes this file.")

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: {report_path} is not valid JSON: {exc}")

    errors = validate(report)
    if errors:
        print(f"ERROR: {report_path} failed schema validation:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(
            "\nRefusing to render an invalid report. Fix report.json and re-run -- "
            "no re-fetching needed."
        )

    problems = check_citations(report)
    if problems:
        print("ERROR: citation integrity check failed:\n", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit("\nEvery cited source id must exist in sources[]. Refusing to render.")

    theme = args.theme or report.get("theme") or "academic"
    html = build_html(report, theme)

    if args.output:
        out_path = Path(args.output)
    else:
        stem = report.get("run_id", "report")
        suffix = f"-{theme}" if args.theme else ""
        out_path = OUTPUT_DIR / f"{stem}{suffix}.pdf"

    if args.keep_html:
        html_path = out_path.with_suffix(".html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html, encoding="utf-8")
        print(f"HTML: {html_path}")

    render_pdf(html, out_path, report)

    size_kb = out_path.stat().st_size / 1024
    print(
        f"OK  {out_path}  ({size_kb:.0f} KB, theme: {theme}, "
        f"{len(report.get('key_findings', []))} findings, "
        f"{len(report.get('sources', []))} sources)"
    )


if __name__ == "__main__":
    main()
