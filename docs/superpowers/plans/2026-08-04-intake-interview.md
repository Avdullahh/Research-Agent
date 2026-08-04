# Interview-Based Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hand-filled research brief as the workflow's entry point with an adaptive interview that the agent runs, producing the same YAML brief for the user to confirm.

**Architecture:** A new SOP, `workflows/intake_interview.md`, defines the interview. It asks the three fields that cannot be inferred (`topic`, `role`, `home_region`), proposes the remaining eight from the topic, and writes `.tmp/<run_id>/brief.md`. `research_report.md` Stage 1 onward is untouched — it still reads the same eleven-field YAML. Three existing files get pointer edits so the interview becomes the default path.

**Tech Stack:** Markdown only. No Python, no schema, no tool changes.

## Global Constraints

- **No Python changes.** No file under `tools/` is created, modified, or deleted by this plan.
- **No schema changes.** The brief's eleven field names and their meanings are fixed by `workflows/brief_template.md`. Do not add, rename, or remove a field.
- **`workflows/brief_template.md` never moves and its body never changes.** CLAUDE.md guarantees this — it is the reusable sample. Only its line 3 header instruction is editable.
- **Never read `used_briefs/`.** This holds during implementation as well as at runtime. Do not open, glob, or grep that folder to see "how briefs usually look" — `brief_template.md` is the reference.
- **Do not commit.** The user has explicitly asked that this work stay uncommitted for now; the repo has no commits yet and the initial commit is their decision. Skip every `git commit` step you would normally add.
- **The manual path must keep working.** A user who hands over a filled-in brief skips the interview entirely. Every edit must preserve that route.

---

### Task 1: Write the intake interview SOP

**Files:**
- Create: `workflows/intake_interview.md`
- Read for reference: `workflows/brief_template.md` (field list, good/weak examples)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: the file path `workflows/intake_interview.md`, referenced by name in Tasks 2 and 3. Its contract with the rest of the system is that it ends by having written `.tmp/<run_id>/brief.md` containing valid YAML with the eleven `brief_template.md` field names, and having obtained explicit user approval of that YAML.

- [ ] **Step 1: Re-read the field reference**

Read `workflows/brief_template.md` in full. You need the exact field names, their defaults, and the good/weak examples for `topic` and `role` — the SOP you are about to write refers to them as its calibration bar, so they must match.

- [ ] **Step 2: Create `workflows/intake_interview.md` with this content**

```markdown
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
```

- [ ] **Step 3: Verify the field names match the template**

This extracts field names from the template's fenced YAML block only (not its prose),
asserts there are exactly eleven, and checks each one is *handled* by the SOP — meaning it
appears in Stage A's list or Stage B's table, not merely somewhere in the prose. A plain
substring search would pass unconditionally, since `topic` occurs inside `topic-slug` and
`exclude` occurs in ordinary sentences.

Run:

```bash
python -c "import re; t=open('workflows/brief_template.md',encoding='utf-8').read(); i=open('workflows/intake_interview.md',encoding='utf-8').read(); f=sorted(set(re.findall(r'^([a-z_]+):',re.search(r'\`\`\`yaml\n(.*?)\n\`\`\`',t,re.S).group(1),re.M))); handled=set(re.findall(r'\`([a-z_]+)\`',i.split('## Stage A')[1].split('## Stage C')[0])); print('template fields:',f); print('count:',len(f)); print('unhandled:',[x for x in f if x not in handled])"
```

Expected: `count: 11`, the eleven names are `credibility_rules`, `depth`, `exclude`,
`home_region`, `must_include`, `questions`, `recency`, `role`, `subject_regions`, `theme`,
`topic`, and `unhandled: []`.

If `count` is not 11, your regex found template prose — check the fenced block. If a field
is reported unhandled, Stages A and B between them never tell the agent what to do with it.
Add it to the Stage B table and re-run.

- [ ] **Step 4: Verify the anti-carryover rule is present and unambiguous**

Confirm by reading that `workflows/intake_interview.md` contains all three of: an explicit
"do not read `used_briefs/`" instruction, a prohibition on reusing settings from an earlier
run in the same session, and a stated reason for both. A rule without its reason gets
rationalized away by a future session.

---

### Task 2: Rewire `research_report.md` to the new entry point

**Files:**
- Modify: `workflows/research_report.md` — "Required inputs" section (lines 14–21) and Stage 0 (lines 47–53)

**Interfaces:**
- Consumes: `workflows/intake_interview.md` from Task 1, referenced by path. Relies on that SOP's guarantee that `.tmp/<run_id>/brief.md` exists and has been confirmed before Stage 1 runs.
- Produces: a `research_report.md` whose Stage 1 through Stage 5 text is byte-identical to what it is today.

- [ ] **Step 1: Replace the "Required inputs" section**

Find this block:

```markdown
## Required inputs

A filled `workflows/brief_template.md` copy, typically at `.tmp/brief.md`.
Required fields: `topic`, `role`, `home_region`. Everything else has a default.

**Before starting, check the brief for contradictions** — e.g. `credibility_rules` says
peer-reviewed only but `must_include` names a vendor whitepaper. Raise it with the user
rather than silently resolving it.
```

Replace it with:

```markdown
## Required inputs

A confirmed brief at `.tmp/<run_id>/brief.md`, carrying the eleven fields defined in
`workflows/brief_template.md`. Required fields: `topic`, `role`, `home_region`. Everything
else has a default.

**Two ways to get one:**

1. **Interview (default).** The user names a topic; you run `workflows/intake_interview.md`,
   which asks what it must, proposes the rest, and writes the confirmed brief. Contradiction
   checking happens there, on your draft, before the user ever sees it.
2. **Hand-filled.** The user gives you a filled-in `brief_template.md` copy, typically at
   `.tmp/brief.md`. **Check it for contradictions before starting** — e.g.
   `credibility_rules` says peer-reviewed only but `must_include` names a vendor whitepaper.
   Raise it with the user rather than silently resolving it.
```

- [ ] **Step 2: Replace Stage 0**

Find this block:

```markdown
### Stage 0 — Set up the run

1. Read the brief. Parse the YAML block.
2. Mint `run_id`. Create `.tmp/<run_id>/`.
3. Copy the brief to `.tmp/<run_id>/brief.md` so the run is self-contained and auditable.
4. Echo back your interpretation: topic, role lens, home region, depth, chosen theme
   (and why, if `auto`). Cheap to confirm now, expensive to discover after 25 fetches.
```

Replace it with:

```markdown
### Stage 0 — Set up the run

**If the brief came from the interview**, this stage is already done — `intake_interview.md`
minted the `run_id`, created `.tmp/<run_id>/`, wrote the brief there, and got the user's
confirmation at its own gate. Go to Stage 1.

**If the user hand-filled a brief:**

1. Read the brief. Parse the YAML block.
2. Mint `run_id`. Create `.tmp/<run_id>/`.
3. Copy the brief to `.tmp/<run_id>/brief.md` so the run is self-contained and auditable.
4. Echo back your interpretation: topic, role lens, home region, depth, chosen theme
   (and why, if `auto`). Cheap to confirm now, expensive to discover after 25 fetches.
```

- [ ] **Step 3: Update the stage diagram**

Find this line in the ASCII flow diagram:

```
brief.md ──▶ [1 Discover]   ──▶ candidates.json    (you)
```

Replace with:

```
brief.md ──▶ [1 Discover]   ──▶ candidates.json    (you)
   ▲
   └── interview (workflows/intake_interview.md) or hand-filled
```

- [ ] **Step 4: Verify Stages 1–5 are untouched**

Run:

```bash
git diff --stat workflows/research_report.md
git diff workflows/research_report.md
```

Expected: every changed hunk falls inside the "Required inputs" section, Stage 0, or the
diagram. Zero changes at or below the `### Stage 1 — Discover` heading. If the diff touches
Stage 1–5 text, the schema contract with `tools/render_report.py` may have shifted — revert
those hunks.

---

### Task 3: Update the two pointer files and dry-run the intake

**Files:**
- Modify: `workflows/brief_template.md` — line 3 only
- Modify: `CLAUDE.md` — the "Run the research workflow" line under Current State

**Interfaces:**
- Consumes: `workflows/intake_interview.md` (Task 1) and the rewired `research_report.md` (Task 2), both referenced by path.
- Produces: nothing later tasks depend on. This is the last task.

- [ ] **Step 1: Update `workflows/brief_template.md` line 3**

Find:

```markdown
Copy this file to `.tmp/brief.md`, fill it in, then tell me: **"Run the research workflow on `.tmp/brief.md`"**.
```

Replace with:

```markdown
**You don't have to fill this in.** Just name a topic and I'll run
`workflows/intake_interview.md` — I ask what I can't infer, propose the rest, and you
confirm the finished brief. This file is the field reference that interview is built from.

Prefer to do it by hand? Copy this file to `.tmp/brief.md`, fill it in, then tell me:
**"Run the research workflow on `.tmp/brief.md`"**. That path still works.
```

Change nothing else in this file. The YAML block, its comments, and the Notes section stay
exactly as they are — CLAUDE.md guarantees this file as the reusable sample.

- [ ] **Step 2: Update `CLAUDE.md`**

Find:

```markdown
**Run the research workflow:** read `workflows/research_report.md` and follow it. Entry point is a filled-in copy of `workflows/brief_template.md`.
```

Replace with:

```markdown
**Run the research workflow:** the user names a topic; read `workflows/intake_interview.md` and follow it to produce a confirmed brief, then read `workflows/research_report.md` and follow it from Stage 1. A hand-filled copy of `workflows/brief_template.md` is still accepted as an entry point — that route starts at Stage 0.
```

- [ ] **Step 3: Dry-run the interview against a throwaway topic**

Do not run real research. Walk Stages A–D of `workflows/intake_interview.md` yourself using
the topic *"whether small UK accountancy firms are adopting AI bookkeeping tools"*.

Write the assembled brief to your session's scratchpad directory (the path given in your
environment), as `dryrun_brief.md`. Keep it out of `.tmp/` — that directory holds real run
directories, and a fake one there is a trap for the next session. Nothing to create and
nothing to clean up afterward; the scratchpad is disposable by definition.

Stop before Stage E. This is a shape check, not a research run.

- [ ] **Step 4: Verify the dry-run brief is well-formed and complete**

`pyyaml` is **not installed** on this machine and must not be installed for this check —
nothing in `requirements.txt` needs it, and the agent parses briefs by reading them, not
with a library. This check is therefore structural rather than a real YAML parse.

Substitute your scratchpad path for `<SCRATCH>` and run:

```bash
python -c "import re,sys; t=open(r'<SCRATCH>/dryrun_brief.md',encoding='utf-8').read(); b=re.search(r'\`\`\`yaml\n(.*?)\n\`\`\`',t,re.S).group(1); keys=re.findall(r'^([a-z_]+):',b,re.M); req=['topic','role','home_region','subject_regions','depth','theme','recency','credibility_rules','exclude','must_include','questions']; print('keys:',sorted(keys)); print('missing:',[k for k in req if k not in keys]); print('duplicated:',[k for k in set(keys) if keys.count(k)>1]); print('comment lines left in:',[l for l in b.splitlines() if l.strip().startswith('#')]); print('question count:',len([l for l in b.split('questions:')[1].splitlines() if l.strip().startswith('-')]) if 'questions:' in b else 0)"
```

Expected: `missing: []`, `duplicated: []`, `comment lines left in: []` (the guidance
comments must be stripped — a brief that ships the template's instructions is not a brief),
and `question count:` between 4 and 6.

- [ ] **Step 5: Verify the confirmation gate reads as a hard stop**

This is the behavior the whole design rests on, and no structural check can catch it. Read
Stage E of `workflows/intake_interview.md` with fresh eyes and confirm all three:

1. The prohibition on searching before approval is stated as a hard stop, not as one item in
   an ordered list a reader can skim past.
2. Its reason is given — cheaper to fix a wrong role now than after twenty-five fetches.
3. The "just go" edge case still routes through the gate rather than around it.

A future session under time pressure will look for permission to skip this. If any of the
three is weak, strengthen the wording now. This is the same check applied to the
anti-carryover rule in Task 1 Step 4, for the same reason: a rule without its reason gets
rationalized away.

- [ ] **Step 6: Report, do not commit**

Summarize for the user: the three files created or modified, the dry-run result, and the
confirmation that Stages 1–5 of `research_report.md` are unchanged. Leave everything
uncommitted — the initial commit of this repo is the user's call.

---

## Self-Review

- **Spec coverage:** Flow → Task 2 Steps 2–3. Interview Stage A + role push-back → Task 1
  Step 2. Stage B proposals and presentation split → Task 1 Step 2. Anti-carryover →
  Task 1 Steps 2 and 4. Confirmation gate and pre-flight contradiction check → Task 1
  Step 2. Manual path preserved → Task 2 Step 1, Task 3 Step 1. Four-file table → Tasks 1–3.
  Spec's three testing items → Task 3 Step 4 (well-formed brief), Task 2 Step 4 (Stage 1+
  untouched), Task 3 Step 1 (manual path documented). No gaps.
- **Behavioral checks:** two rules carry the design and neither is structurally verifiable,
  so each gets an explicit read-and-confirm gate — anti-carryover at Task 1 Step 4, the
  no-searching-before-approval gate at Task 3 Step 5.
- **`pyyaml` is not installed** and the plan does not install it; Task 3 Step 4 verifies the
  brief structurally instead. Confirmed by running `python -c "import yaml"` while writing
  this plan.
- **Placeholders:** none. Every edit shows exact find/replace text; every verification shows
  the exact command and expected output.
- **Consistency:** the path `workflows/intake_interview.md`, the artifact
  `.tmp/<run_id>/brief.md`, and the `run_id` format `YYYYMMDD-HHMMSS-<topic-slug>` are
  spelled identically in all three tasks and match `research_report.md`.
- **Deviation from the skill's default shape:** this plan has no TDD cycle and no commit
  steps. The change is four markdown SOPs with no executable surface, so verification is
  structural (field-name and YAML-parse checks) rather than unit tests; and the user has
  asked that the work stay uncommitted.
