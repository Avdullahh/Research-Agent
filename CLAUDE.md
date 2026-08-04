# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## Current State

One capability is built: the **research report workflow** (topic → vetted sources → themed PDF).

**Environment:** Python 3.11.9, pip installs to the user site-packages (no venv). Verified on Windows 11.

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium        # ~115MB, one time, to %LOCALAPPDATA%\ms-playwright
```

**Run the research workflow:** the user names a topic; read `workflows/intake_interview.md` and follow it to produce a confirmed brief, then read `workflows/research_report.md` and follow it from Stage 1. A hand-filled copy of `workflows/brief_template.md` is still accepted as an entry point — that route starts at Stage 0.

```bash
python tools/fetch_sources.py --run-id <run_id>              # stage 2; --force to re-fetch
python tools/render_report.py --run-id <run_id>              # stage 5
python tools/render_report.py --run-id <run_id> --theme market --keep-html   # theme compare + debug HTML
```

**Smoke test without doing any research** (renders the fixture in all four themes):

```bash
python tools/render_report.py --input tools/fixtures/report_fixture.json --theme academic --output output/_check.pdf
```

**There is no test suite.** `tools/fixtures/report_fixture.json` is the closest thing — it exercises every schema branch. Two checks worth running after touching templates or themes, because both catch failures that are invisible by eye (see the Learnings section of `workflows/research_report.md`):

1. **Computed styles** — load the `--keep-html` output in a headless page and read `getComputedStyle`. A bug that swallows the CSS still produces a plausible-looking screenshot.
2. **PDF pagination** — screenshots of the HTML cannot show page breaks, and page breaks are the whole difference between the HTML and the deliverable. Use `pypdf` to assert: cover alone on page 1, appendix starting at the top of its own page, `Page N of M` present on every page, no near-empty pages. `pdftoppm`/poppler is not installed here, so image-based PDF review is unavailable.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to pull data from a website, don't attempt it directly. Read `workflows/scrape_website.md`, figure out the required inputs, then execute `tools/scrape_single_site.py`

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
- Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**What goes where:**
- **Deliverables**: Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can access them directly
- **Intermediates**: Temporary processing files that can be regenerated

**Directory layout:**
```
.tmp/           # Per-run working dirs (<run_id>/: brief, candidates, fetched/, vetted, report). Disposable.
output/         # Generated PDFs. Gitignored.
tools/          # Python scripts for deterministic execution
  templates/    # report.html.j2, base.css, themes/*.css
  fixtures/     # report_fixture.json -- exercises every schema branch
  report_schema.json
workflows/      # Markdown SOPs defining what to do and how
.env            # API keys and environment variables (NEVER store secrets anywhere else)
credentials.json, token.json  # Google OAuth (gitignored)
```

**Deliverable exception:** PDFs are written locally to `output/` rather than to a cloud service. A Drive upload seam is documented in the workflow but not built.

## used_briefs/ — never read this folder

`used_briefs/` archives filled-in briefs whose PDF has been approved. **Do not read, glob, or search it when starting a new task, and never use its contents as context.** It is a record, not an input.

Every research task takes its guidelines fresh from a new brief. Carrying a previous task's credibility rules, region, role lens, or theme into the next one silently corrupts that report — which defeats the entire premise of the workflow.

**After the user approves a report PDF:** move that run's filled-in brief to `used_briefs/<run_id>.md`. Leave the blank `workflows/brief_template.md` in place — it is the reusable sample and never moves. Do not move a brief just because the render succeeded; wait for explicit approval.

**Core principle:** Local files are just for processing. Anything I need to see or use lives in cloud services. Everything in `.tmp/` is disposable.

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.
