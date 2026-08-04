# Workflow: Research Report → PDF

## Objective

Given a filled-in research brief, find the most credible sources available (weighted by
geography), synthesize findings through the lens of the role stated in the brief, and
produce a PDF styled to fit the subject matter.

**The defining constraint of this workflow:** the guidelines vary per task. Credibility
rules, geographic scope, role lens, depth, and visual style are *inputs*, not constants.
Nothing topic-specific is hardcoded in a tool. If you find yourself wanting to add a
"prefer .gov domains" rule to a Python file, stop — that belongs in a brief.

## Required inputs

A filled `workflows/brief_template.md` copy, typically at `.tmp/brief.md`.
Required fields: `topic`, `role`, `home_region`. Everything else has a default.

**Before starting, check the brief for contradictions** — e.g. `credibility_rules` says
peer-reviewed only but `must_include` names a vendor whitepaper. Raise it with the user
rather than silently resolving it.

## Layer discipline (from CLAUDE.md)

| Belongs to | What |
|---|---|
| **You (agent)** | Discovery queries, credibility judgment, geo classification, synthesis, role framing, theme choice |
| **Tools** | Fetching, extraction, schema validation, PDF rendering. No judgment, ever. |

Rule of thumb: if a step requires an opinion, you do it. If it has exactly one correct
output for a given input, a tool does it.

## Stages

`run_id` = `YYYYMMDD-HHMMSS-<topic-slug>`. Every stage persists its output to
`.tmp/<run_id>/` so any stage can be re-run without redoing earlier work. **Never re-run
discovery or fetching because rendering failed.**

```
brief.md ──▶ [1 Discover]   ──▶ candidates.json    (you)
             [2 Fetch]      ──▶ fetched/*.json     (tools/fetch_sources.py)
             [3 Vet]        ──▶ vetted.json        (you)
             [4 Synthesize] ──▶ report.json        (you)
             [5 Render]     ──▶ output/<run_id>.pdf (tools/render_report.py)
```

### Stage 0 — Set up the run

1. Read the brief. Parse the YAML block.
2. Mint `run_id`. Create `.tmp/<run_id>/`.
3. Copy the brief to `.tmp/<run_id>/brief.md` so the run is self-contained and auditable.
4. Echo back your interpretation: topic, role lens, home region, depth, chosen theme
   (and why, if `auto`). Cheap to confirm now, expensive to discover after 25 fetches.

### Stage 1 — Discover (you, using WebSearch)

This is the only stage with no tool behind it, and it's where the geographic requirement
is actually enforced. Built-in WebSearch has **no country/region parameter** — geo
targeting comes entirely from how you construct queries.

**Run separate query passes per proximity tier, local first:**

- **Local** (`home_region` itself): jurisdiction-qualified phrasings — `"<topic> Netherlands"`,
  `"<topic> AFM"`, `"<topic> Rijksoverheid"`. Name the region's actual institutions,
  regulators, statistical agencies, and universities rather than just the country name.
  Use local-language query variants where the region warrants it (a Dutch topic will have
  Dutch-language primary sources that an English query never surfaces).
  Use `site:` and TLD scoping against known-authoritative domains for that region.
- **Regional** (the bloc/continent containing `home_region`): EU bodies for a Dutch brief,
  ASEAN for a Singaporean one, etc.
- **Global**: the unqualified topic, plus the acknowledged international authorities.

**Other discovery rules:**

- **`must_include` runs first**, as its own targeted queries. If you can't reach one,
  note it — it goes in `coverage_notes`, it does not get silently dropped.
- **`exclude` filters after** search, not before. Record what you excluded and why, so
  the report can show that a source's absence was a decision rather than an oversight.
- **Over-collect.** Vetting rejects some candidates. Gather roughly 2× the depth tier's
  final count: brief → ~20-30 candidates for 8-15 survivors; standard → ~40-60 for 15-30.
- **Prefer the primary source over anything describing it.** If a search result summarizes
  a study, a regulation, or a dataset, find the original and add *that* as the candidate.
- **Note thin local coverage as you observe it.** If the local pass returns three weak
  results, that's a finding about the topic, not just a search failure. It feeds
  `coverage_notes`.

Write `.tmp/<run_id>/candidates.json` yourself:

```json
[{"url": "...", "title": "...", "why_selected": "...", "proximity_tier_guess": "local|regional|global"}]
```

`proximity_tier_guess` is provisional — confirm or correct it at stage 3 once you've seen
the page.

### Stage 2 — Fetch (tool)

```
python tools/fetch_sources.py --run-id <run_id>
```

Reads `candidates.json`, writes one JSON per source to `.tmp/<run_id>/fetched/`. It
records failures rather than raising, and skips URLs already fetched unless `--force`.

Expect some failures — that is normal and not a bug. Paywalls, bot walls, and dead links
are part of research. Read the summary line it prints, and if too many succeeded-but-empty,
check whether the sites are JS-rendered (see Learnings).

### Stage 3 — Vet (you)

Read the fetched text. **Judgment happens here, and it happens after fetching** because
credibility signals — named author, methodology section, corrections policy, citation
quality, funding disclosure — live in the page, not in a search snippet.

**Apply `credibility_rules` from the brief first.** It overrides the default rubric below
wherever they conflict. The default rubric, in rough priority order:

1. **Publisher type and independence** — primary institution / regulator / peer-reviewed
   journal > established press with editorial standards > trade press > vendor content >
   anonymous blog. Vendor content isn't automatically disqualified (sometimes they hold
   the only data), but the commercial interest gets flagged on the source.
2. **Primary vs. secondary vs. aggregated** — the regulation itself beats the law firm's
   summary beats the newsletter's summary of the summary.
3. **Named author with checkable credentials** — beats a byline-free institutional post.
4. **Dates present and recent enough** — publication *and* last-modified. Undated content
   on a fast-moving topic is a serious mark against.
5. **Methodology and citations shown** — can you see how they know it? Are the citations
   real and reachable?
6. **Funding and conflict disclosure** — present and clean, present and concerning, or absent.
7. **Corrections policy** — does the publisher visibly fix errors?

Assign each surviving source:

- **Tier A** — primary, authoritative, directly on-topic. Would stand alone.
- **Tier B** — credible and useful, but secondary, partial, or slightly off-scope.
- **Tier C** — usable for context or as a pointer, with a stated caveat. Never the sole
  support for a claim.

Below C: drop it, and record why in the drop list.

**Also record the three geo fields per source** (they are orthogonal — do not collapse them):

- `publisher_jurisdiction` — where the publisher sits / is regulated
- `subject_regions[]` — which regions the findings are *about*
- `proximity_tier` — `local` / `regional` / `global` relative to `home_region`

**Geo preference rule:** prefer local, widen to regional, then global. When local coverage
is genuinely thin, say so explicitly in `coverage_notes` rather than quietly substituting
global sources and presenting them as if they were locally applicable. A finding drawn
from US data being applied to a Dutch decision is a caveat the reader must see.

Write `.tmp/<run_id>/vetted.json`: the surviving sources with tier, rationale, which brief
guideline each satisfied, and the geo fields. Include the dropped list with reasons.

### Stage 4 — Synthesize (you)

Write `.tmp/<run_id>/report.json`. This is the contract with the render tool — see the
schema in `tools/report_schema.json`.

**Non-negotiables:**

- **Every claim carries `source_ids`.** A finding with no source ID is not a finding.
- **`implication_for_role` is the point of the whole exercise.** Not "what this says" but
  "what this means for someone in the brief's role, making the brief's decision." Written
  in that role's vocabulary. If a sentence would be identical for any reader, it's filler.
- **Answer the brief's `questions` explicitly.** Each one should map to findings. If the
  research couldn't answer one, say that plainly in `coverage_notes`.
- **Surface disagreement, don't average it.** Where credible sources conflict, that goes in
  `conflicts[]` with both sides and your assessment. Averaging two contradictory positions
  into a bland middle is the most common way research reports become useless.
- **`coverage_notes` is mandatory and specific.** Thin local coverage, unreachable
  `must_include` sources, paywalled misses, questions left unanswered. Vague hedging
  ("some limitations apply") is worse than nothing.

### Stage 5 — Render (tool)

```
python tools/render_report.py --run-id <run_id> [--theme market]
```

Validates `report.json` against the schema and **fails loudly on a missing field** rather
than emitting a half-empty PDF. `--theme` overrides the brief, so themes can be compared
without re-running any research.

Output: `output/<run_id>.pdf`, where `<run_id>` is the value of the `run_id` **field inside
report.json**, not the `--run-id` directory argument. They are normally identical; if you
ever copy a report between run directories they will diverge, and the field wins. Report
the actual printed path to the user rather than assuming it.

## Theme selection (when `theme: auto`)

| Theme | Use for | Look |
|---|---|---|
| `academic` | Science, medicine, systematic review, literature | Serif, restrained, citation-forward |
| `regulatory` | Law, policy, compliance, government | Formal, high-contrast, clause-like numbering |
| `market` | Industry, competitive, commercial, trend research | Modern sans, data-forward, accent color |
| `technical` | Engineering, security, infrastructure, tooling | Monospace accents, code-friendly |

Pick from the topic, and **tell the user which you chose and why** at stage 0. If a topic
straddles two (e.g. "security compliance"), pick by what the *reader* is doing with it —
the brief's `role` decides. A GC reading about security gets `regulatory`; an SRE reading
about the same rules gets `technical`.

## Edge cases

**Thin local coverage.** Widen to regional, then global — but label every widened source's
`proximity_tier` honestly and state the gap in `coverage_notes`. Never present a global
source as though it were locally authoritative.

**Paywalls.** The fetch tool records what it got. Don't circumvent paywalls. If the
abstract or summary carries the finding, use it and mark the source as partially accessed.
If it doesn't, drop it and note the miss — a known unreachable source is useful information.

**Conflicting evidence.** Goes in `conflicts[]`. Give both sides their strongest form, then
assess — usually on methodology, recency, or independence. "Sources disagree" alone is not
an assessment.

**Dead links / fetch failures.** Expected. If a Tier-A-looking candidate fails, try once
more (transient), then try the publisher's own site directly, then drop it with a note.

**JS-rendered sites returning empty text.** The fetch tool is plain HTTP. If a source is
important and comes back empty, fetch it yourself with WebFetch and hand-write the JSON
into `fetched/`. Don't add a browser to the tool for one page.

**Topic too broad.** If the brief's topic would need 100 sources to cover honestly, say so
at stage 0 and propose splitting it into two runs. Don't produce a thin report on a wide
topic and let the page count imply coverage.

**A `must_include` source is unreachable.** Say so prominently. The user asked for it
specifically, which means they'll notice its absence — better to explain it than to have
them find it themselves.

## Learnings

*Append findings here as the workflow is used. Rate limits, sites that need special
handling, query patterns that work well for particular regions, theme choices that landed
badly. This section is why the workflow gets better over time.*

- **2026-08-02 — Render path.** Playwright + headless Chromium confirmed working on this
  Windows machine (Python 3.11.9). Chromium is ~115MB, downloaded once to
  `%LOCALAPPDATA%\ms-playwright`. WeasyPrint was rejected as primary because it needs GTK
  system libraries on Windows. Full CSS support including grid, `@page`, and web fonts.
- **2026-08-02 — Layer boundary.** Credibility scoring was deliberately *not* built as a
  tool. It varies per brief, which makes it agent judgment by definition. Resist the pull
  to codify it later; a scoring script would silently override the user's per-task rules.
- **2026-08-02 — Jinja autoescape silently ate the CSS.** `Environment(autoescape=True)`
  escapes *every* rendered variable, including `{{ base_css }}` injected into `<style>`.
  Every quoted font name became `&#34;`, so all four themes silently fell back to Times
  New Roman at browser-default size while still looking superficially "different" because
  unquoted color values survived. Screenshots did not make this obvious. Fixed by wrapping
  both CSS strings in `Markup()`. **Lesson: verify styling with `getComputedStyle`, not by
  eye** — `tools/` has no test suite, so a computed-style probe is the cheapest real check
  when touching templates or themes.
- **2026-08-02 — `httpbin.org` is unreliable for testing.** Returned 503 during fetch-tool
  testing. Use `example.com` and `iana.org` for reachability tests instead.

### From the first live run (Saudi Arabia AI automation, brief depth, 18 candidates → 12 sources)

- **Saudi government domains largely refuse this machine.** `monshaat.gov.sa` and
  `sdaia.gov.sa` connect-timeout or drop the connection; `vision2030.gov.sa` and
  `spa.gov.sa` return no extractable content (JS-rendered). `pif.gov.sa` works fine.
  **Budget for recovering KSA government sources by hand** via WebFetch — do not assume
  a `.gov.sa` candidate will fetch. Same likely applies to other Gulf government domains.
- **`robots.txt` blocks some of the best sources.** OECD publication PDFs and
  `news.sap.com` are both disallowed. When a tier-A source is blocked, retrieve it with
  WebFetch and hand-write the record into `fetched/` (see below). Do not use `--no-robots`
  to bypass it.
- **Large PDFs: WebFetch returns raw PDF bytes, not text.** It saves the file locally and
  prints the path. Extract with `pypdf` (already installed) rather than giving up:
  `PdfReader(path)` then `"".join(p.extract_text() for p in r.pages)`. This is how the
  62-page OECD paper was read. `pdftoppm` is *not* available, so the Read tool cannot open
  PDFs on this machine.
- **Hand-written `fetched/` records must match the tool's filename scheme** or the fetch
  tool will re-fetch them: `f"{netloc}-{sha256(url)[:12]}.json"`. Add a `recovery_note`
  field so the manual retrieval is visible at vetting time.
- **"Top N companies in <country>" searches return almost pure SEO spam.** Every result
  was a vendor listicle published by an agency appearing in its own ranking. Competitive
  landscape is the *hardest* question to source credibly. Better angles: the state-backed
  champion's own announcements, national statistics offices, and foreign trade-promotion
  bodies (`trade.gov` was tier A here and is independent of local promotional framing).
- **Watch for false conflicts across survey years.** 27.6% and 33% adoption looked like
  contradictory sources but were consecutive years of the same GASTAT series. The *real*
  conflict was national statistics (33% of all establishments) versus a consultancy survey
  of 70 self-selected tech leaders (76% expecting ROI). Always check what population each
  number describes before writing a `conflicts[]` entry.
- **National statistics often omit the firm-size split** that an SMB-focused brief needs.
  When that happens, say so plainly and label any imported base rate (here, OECD G7 data)
  as `global` proximity with an explicit non-transferability caveat. Do not let a
  non-local base rate read as a local measurement.
- **Brief depth ran to 11 pages, not the stated 3–6.** Body was ~6 pages; the appendix was
  4–5 because every source carries a full rationale and caveat. The source *count* guidance
  (8–15) held. Either treat the page range as advisory or trim appendix rationales — the
  count is the reliable lever, not the page estimate.
