# Workflow: Research Intake Interview

## Objective

Turn a one-line research request into a complete, confirmed research brief at
`.tmp/<run_id>/brief.md`, without the user filling in a template by hand.

This workflow ends where `workflows/research_report.md` Stage 1 begins. It produces exactly
the same artifact the old hand-filled path produced — same eleven fields, same file
location — so nothing downstream changes.

## When to run this

The user asks for research on a topic without handing over a brief.

**Skip this workflow entirely** if the user hands over a filled-in brief (typically at
`.tmp/brief.md`). The manual path is still fully supported. Go straight to
`research_report.md` Stage 0.

## The one rule that matters most

**Every proposal in this interview derives from `workflows/brief_template.md` and the
user's current topic. Nothing else.**

Never source a default from `used_briefs/` — do not read, glob, or search that folder.
Never reuse the credibility rules, region, role lens, depth, or theme from an earlier run
in this same session. An interview-based intake creates a standing pull toward "use last
time's settings," and that is precisely the silent corruption the `used_briefs/`
prohibition in CLAUDE.md exists to prevent. Two research tasks that sound similar are not
the same task.

If the user explicitly says "same setup as last time," ask them to state what they want
carried over. Their memory of it is a legitimate input; your reading of the archive is not.

## No WebSearch anywhere in this workflow

Not even one orienting search to inform a Stage B proposal. Draft `credibility_rules`,
`must_include`, and `questions` from the topic as stated and from `brief_template.md` —
never from a search result. This holds for the entire interview, start to finish, not just
around fetching. The run's first search happens only after the user approves, at
`research_report.md` Stage 1.

## Stage A — Ask what cannot be inferred

Three fields: `topic`, `role`, `home_region`.

Ask these as **prose questions, not pick-lists**. They need sentences, and a pick-list
would cap the answer at whatever options you imagined.

**Pacing is adaptive:**

- Ask all three in a single message when the user's opening request already makes the topic
  clear.
- Break into follow-ups when the topic is ambiguous, spans two genuinely distinct research
  areas, or when one answer contradicts another (e.g. a Dutch home region with a topic that
  is inherently US-only — ask whether they want `subject_regions: ["US"]`).

**The role push-back rule.** If `role` comes back thin — "product manager", "analyst",
"engineer" — ask exactly once more, for the *decision* this research feeds. Compare against
the good/weak examples in `brief_template.md`; that is the bar. A thin `role` is the single
most common cause of a generic report, because `implication_for_role` is the point of the
whole exercise and it cannot be written through a lens that isn't there.

Ask once, then accept what you get. Do not interrogate.

## Stage B — Propose the rest

Eight fields: `depth`, `theme`, `recency`, `credibility_rules`, `subject_regions`,
`exclude`, `must_include`, `questions`.

Draft each one from the topic and present it with **a one-line reason tied to that topic**.
A bare proposal invites a rubber stamp; a reasoned one invites a correction, which is the
point.

**Presentation split:**

| Field | How to present |
|---|---|
| `depth` | Pick-list: `brief` (8–15 sources, ~3–6 pages) or `standard` (15–30 sources, ~8–15 pages). |
| `credibility_rules` | Pick-list of 2–3 drafted presets written for *this* topic, plus a free-text option. |
| `recency` | Pick-list, unless the topic has an obvious hard cutoff — then propose it as prose. |
| `questions` | Prose. Draft 4–6, numbered, so the user can strike or rewrite individually. |
| `must_include`, `exclude` | Prose. Propose what the topic implies; empty is a fine answer. |
| `subject_regions` | Only raise it if it differs from `home_region`. Otherwise leave at default. |
| `theme` | Leave at `auto`. State which theme you'd pick and why — do not make it a question. |

**`questions` is where this interview earns its keep.** `brief_template.md` calls it the
single most valuable field, and it is the one a user is least able to write cold. Draft
real, concrete, answerable questions — not restatements of the topic. Include at least one
that probes where credible sources disagree, since `conflicts[]` is a required part of the
report and an unprobed disagreement is one you will not find at synthesis time.

## Stage C — Pre-flight your own draft

Before showing anything, check your assembled brief against itself. `research_report.md`
used to run this check on the user's brief; now it runs on yours, earlier.

- Does `credibility_rules` forbid a source type that `must_include` requires?
- Does `exclude` remove a domain that `must_include` names?
- Does `recency` cut off a `must_include` source that predates it?
- Is `depth` plausible for the number of `questions`? Six questions at `brief` depth means
  roughly two sources per question. Either widen the depth or cut the questions.
- Would this topic honestly need 100 sources? If so, say so now and propose splitting it
  into two runs, as `research_report.md` requires.

Fix contradictions in your draft rather than presenting them. Raise them with the user only
where the fix is a genuine choice they should make.

## Stage D — Mint the run and write the brief

1. Mint `run_id` = `YYYYMMDD-HHMMSS-<topic-slug>`, matching `research_report.md`.
2. Create `.tmp/<run_id>/`.
3. Write `.tmp/<run_id>/brief.md`.

**Format:** a `---` line, then a fenced ` ```yaml ` block containing all eleven fields, then
a closing `---`. Same shape as `brief_template.md` below its own `---`, with the guidance
comments stripped and real values in place. Include fields left at their defaults with
their default values written out explicitly — an auditable brief states what it chose, not
just what it overrode.

Add one line above the opening `---`:

    Assembled by interview on <date>. Confirmed by the user before Stage 1.

## Stage E — The confirmation gate

Print the full assembled YAML in the chat and wait for explicit approval.

**Do not begin any WebSearch before the user approves.** The whole value of this gate is
that it is cheaper to fix a wrong role now than after twenty-five fetches — the same reason
`research_report.md` Stage 0 asks you to echo your interpretation back.

On approval, hand off to `workflows/research_report.md` at **Stage 1 (Discover)**. Stage 0
is already done: the run directory exists, the brief is in it, and the interpretation has
been confirmed.

If the user edits the brief in their reply, rewrite the file with their edits and show it
once more. Do not proceed on an unconfirmed version.

## Edge cases

**User gives only a topic and says "just go."** Run Stages B–E anyway with your best
inferences for `role` and `home_region`, and label them clearly as guesses in the printed
YAML. The confirmation gate still applies — a guessed `role` is the thing most worth
seeing before searching starts.

**User's topic is really two topics.** Say so at Stage A and propose splitting into two
runs before spending questions on either. Two shallow reports beat one that implies
coverage it doesn't have.

**User rejects every proposed question.** Their rewrite is authoritative. Ask what you
misread about the topic, then redraft once.

**User wants a field the brief doesn't have.** The schema is fixed. Fold the intent into
`credibility_rules` or `questions`, both of which are free text, and say that you did.

## Learnings

*Append findings here as this intake is used — topics where the proposals landed badly,
role phrasings that produced generic reports, question drafts that turned out unanswerable.
This section is why the interview gets better over time.*
