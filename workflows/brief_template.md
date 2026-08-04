# Research Brief

Copy this file to `.tmp/brief.md`, fill it in, then tell me: **"Run the research workflow on `.tmp/brief.md`"**.

Everything below the `---` is the machine-read part. Fill in the YAML block; leave optional
fields blank and I'll use the stated default. The `questions` list is the single most
valuable field — the more specific it is, the more useful the report.

---

```yaml
# ---- REQUIRED ----

topic: >
  # One or two sentences. What are you actually trying to learn?
  # Good: "Whether the EU AI Act's GPAI obligations apply to companies that fine-tune
  #        third-party open-weight models, and what compliance work that triggers."
  # Weak: "AI regulation."

role: >
  # Who you are FOR THIS TASK, and what decision this research feeds.
  # This is the lens every summary gets written through — it is not boilerplate.
  # Good: "Head of Product at a 40-person B2B SaaS company. Deciding whether to ship
  #        an LLM feature in the EU this quarter or wait. I need to know what I'd be
  #        signing up for operationally, not the legal theory."
  # Weak: "Product manager."

home_region: >
  # The jurisdiction/market you care about most. Drives source proximity tiering.
  # e.g. "Netherlands", "EU", "UK", "US federal", "California", "global"

# ---- OPTIONAL (defaults shown) ----

subject_regions: []
  # Regions the FINDINGS should be about, if different from home_region.
  # Example: you sit in the Netherlands (home_region) but want to know what happened
  # in the US market (subject_regions: ["US"]).
  # Default: same as home_region.

depth: brief
  # brief    -> 8-15 sources, ~3-6 pages.  Exec summary, key findings, role
  #             implications, source appendix.
  # standard -> 15-30 sources, ~8-15 pages. Adds per-theme sections and explicit
  #             conflicting-evidence callouts.
  # Default: brief

theme: auto
  # academic   - serif, restrained, citation-forward. Science, medicine, literature review.
  # regulatory - formal, high-contrast, clause-like numbering. Law, policy, compliance.
  # market     - modern sans, data-forward, accent color. Industry/competitive/market research.
  # technical  - monospace accents, code-friendly. Engineering, security, infrastructure.
  # auto       - I pick based on topic and tell you which I chose and why.
  # Default: auto

recency: >
  # e.g. "hard cutoff: nothing before 2024-01-01"
  #      "prefer last 18 months, older OK for foundational/primary sources"
  # Default: prefer last 24 months, no hard cutoff.

credibility_rules: >
  # Extra musts and must-nots FOR THIS TOPIC ONLY. This is where topic-specific
  # judgment gets encoded. Free text — write it the way you'd brief a colleague.
  # Examples:
  #   "Peer-reviewed or preprint-with-named-institution only. No press releases,
  #    no vendor blogs, no 'study finds' journalism summarizing a study I can't reach."
  #   "Primary regulatory text and official guidance outranks law-firm commentary.
  #    Law-firm pieces OK for practical interpretation but must be labelled as such."
  #   "Vendor content is acceptable here since they're the only ones with the data,
  #    but flag the commercial interest on every one."
  # Default: the standard rubric in research_report.md.

exclude: []
  # Domains or source types to skip entirely. Recorded in the report so it's visible
  # why something is absent.
  # e.g. ["medium.com", "content-farm blogs", "anything paywalled"]

must_include: []
  # Specific sources, organizations, or authors that MUST be covered. I'll run
  # targeted queries for these and tell you if I can't reach one.
  # e.g. ["the actual EU AI Act text", "any DNB or AFM guidance", "Stanford HAI index"]

questions: []
  # The specific questions the report must answer. Each becomes a finding section.
  # Be concrete — vague questions produce vague reports.
  # e.g.
  #   - "Does fine-tuning an open-weight model make us a 'provider' under the Act?"
  #   - "What are the actual deadlines and which have already passed?"
  #   - "What does a minimum-viable compliance posture look like for a company our size?"
  #   - "Where do credible sources genuinely disagree on this?"
```

---

## Notes

- **Blank optional fields are fine.** Only `topic`, `role`, and `home_region` are required.
- **`role` does real work.** The same topic briefed as a Head of Product versus a General
  Counsel produces different sources, different framing, and different implications. If
  the report reads generic, `role` was probably too thin.
- **Contradictory guidelines**: if `credibility_rules` conflicts with `must_include` (e.g.
  peer-reviewed only, but you require a vendor report), I'll flag it before starting rather
  than silently picking one.
- **Coverage gaps are reported, not hidden.** If your `home_region` has thin coverage on
  this topic, the report says so instead of quietly substituting global sources.
