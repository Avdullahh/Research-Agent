# Design: Interview-Based Intake for the Research Report Workflow

**Date:** 2026-08-04
**Status:** Approved, pending implementation plan

## Problem

The research report workflow's only entry point is a hand-filled copy of
`workflows/brief_template.md`. Filling in eleven YAML fields before every research task is
the slowest and least pleasant part of using the system, and the two fields that matter
most — `role` and `questions` — are exactly the ones a user is least able to write cold.

## What changes, and what does not

**Changes:** who authors the brief.

**Does not change:** that a brief exists, its schema, or anything downstream of it.

The brief file is load-bearing in three places that are easy to overlook:

1. `research_report.md` Stage 0.3 copies it to `.tmp/<run_id>/brief.md` "so the run is
   self-contained and auditable." Stages 1–5 read fields from that file. The workflow's
   re-runnability promise depends on guidelines living in a file, not in chat scrollback.
2. CLAUDE.md's `used_briefs/<run_id>.md` archiving convention has nothing to archive if no
   brief file is produced.
3. Layer discipline: credibility rules, geography, role lens, and style live in the brief
   precisely so they are *not* hardcoded in tools.

A design that gathered guidelines conversationally and never wrote a file would break all
three. So: interview → agent writes the YAML brief → user confirms it → Stage 1 onward is
untouched.

## Flow

```
"research X"  ──▶ [Intake interview]  ──▶ .tmp/<run_id>/brief.md   (workflows/intake_interview.md)
                       │                        │
                       └─ user confirms YAML ───┘
                                                ▼
                  research_report.md Stage 1 (Discover) onward — unchanged
```

`run_id` is minted during intake so the brief is written directly into the run directory.
Stage 0's "copy the brief to `.tmp/<run_id>/brief.md`" becomes "intake already wrote it
there."

**The manual path stays.** If the user hands over a filled-in brief, skip the interview
entirely and proceed to Stage 0 as today. The interview is the new default, not the only
option.

## The interview

### Fields the agent asks

`topic`, `role`, `home_region` — the three required fields, and the three that cannot be
inferred. Asked as prose questions, not pick-lists; they need sentences.

**Adaptive pacing.** Ask these in one round when the topic is clear. Break into follow-ups
when the topic is ambiguous, spans two distinct research areas, or when an answer conflicts
with another.

**Role push-back rule.** If `role` comes back thin ("product manager", "analyst"), ask once
more for the *decision* the research feeds. A thin role is the most common cause of a
generic report. The good/weak examples in `brief_template.md` are the calibration bar.

### Fields the agent proposes

`depth`, `credibility_rules`, `recency`, `must_include`, `exclude`, and 4–6 draft research
`questions`. Each proposal carries a one-line reason tied to the stated topic. The user
edits, strikes, or approves.

`theme` stays `auto`; the agent states which theme it picked and why, as Stage 0 already
requires.

**Presentation split:** closed choices (`depth`, credibility presets) are offered as
pick-lists. `questions`, `must_include`, and `exclude` are offered as prose the user can
rewrite. Do not force prose fields through a pick-list.

### Anti-carryover rule

Proposals derive from `brief_template.md` and the current topic **only**. Never from
`used_briefs/`. Never from an earlier run in the same session.

This must be stated explicitly in `intake_interview.md`. An interview-based intake creates
a standing pull toward "use last run's settings as defaults," and that is exactly the
silent corruption the `used_briefs/` prohibition in CLAUDE.md exists to prevent. A future
session will reach for prior context unless the document forbids it.

### Confirmation gate

The agent prints the full assembled YAML and waits for explicit approval before any
searching begins.

The contradiction check that `research_report.md` currently applies to the user's brief now
applies to the agent's own draft, and runs *before* the brief is shown — the agent should
not hand over a brief that fights itself (e.g. `credibility_rules` says peer-reviewed only
while `must_include` names a vendor whitepaper).

## Files

| File | Change |
|---|---|
| `workflows/intake_interview.md` | New. The interview SOP: what to ask, what to propose, the role push-back rule, the anti-carryover rule, the confirmation gate, and how to write the brief. |
| `workflows/research_report.md` | "Required inputs" no longer mandates a hand-filled copy. Stage 0 references the intake SOP and drops the copy step. Contradiction check reframed as a pre-flight on the agent's own draft. |
| `workflows/brief_template.md` | Header line only. It stops describing itself as the sole entry point and becomes the field reference plus optional manual path. Body and examples unchanged — CLAUDE.md says this file never moves. |
| `CLAUDE.md` | The "Entry point is a filled-in copy of `workflows/brief_template.md`" line. |

No Python changes. No schema changes. No tool changes.

## Testing

There is no test suite, and this change touches only markdown SOPs, so verification is
behavioral rather than automated:

1. Run the intake on a fresh topic and confirm the produced `.tmp/<run_id>/brief.md` parses
   as valid YAML against every field name in `brief_template.md`.
2. Confirm `tools/render_report.py` is never reached with a differently-shaped brief —
   i.e. Stage 1 onward runs without modification.
3. Confirm the manual path still works: hand over a filled brief and check the interview is
   skipped.

The render smoke test in CLAUDE.md remains the check for anything touching templates; it is
unaffected by this change.

## Out of scope

- Changing the brief schema or adding fields.
- Any change to discovery, fetching, vetting, synthesis, or rendering.
- Persisting user preferences across runs — deliberately excluded; see the anti-carryover
  rule.
