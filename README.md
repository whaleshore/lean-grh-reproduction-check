# lean-grh-reproduction-check

A reproducible check on a publicly released Lean formalization.

**Methods open, conclusions provisional.**

---

## What this is

On 2026-11-20, an Anthropic mathematician (Levent Alpöge) published a note claiming
a proof of the Riemann Hypothesis and the Generalized Riemann Hypothesis, produced
in collaboration with a non-public version of Claude, and released as a Lean
formalization:

- Note (4 pages): <https://alpo.ge/remark.pdf>
- Lean source (14 parts): <https://alpo.ge/lean.tar.gz.part01> … `part14`

The note says the argument is "incredibly long" and that formalization "is finished".
Press reports put the prose at ~250,000 pages and the Lean code at ~17 million lines;
**the note itself does not give either number.**

The note also states:

> Claude and I have also formalized the arguments without assumptions.

Several mathematicians have publicly commented. Andrew Sutherland (MIT) reported
that he compiled the Lean code independently. Elliot Glazer reported that the
formalized statement appears to be the GRH.

**This repository is not a review of the mathematics. It is a small, mechanical
check of the artifact.** It asks four narrow questions that can each be answered
yes or no by a script, and it publishes those scripts so that anyone can re-run
them and compare.

We are not affiliated with Anthropic. We have no access to anything non-public.

## Results (short version)

See **[FINDINGS.md](FINDINGS.md)** for the full record, including the mistakes we made.

| check | result |
|---|---|
| `sorry` | **0** in 17,363,528 lines / 175,073 files |
| `axiom` | **0** |
| `sorryAx` / `native_decide` / `implemented_by` / `extern` / `opaque` / `unsafe` | **0** each |
| formalized statement | standard RH and standard GRH; `RiemannHypothesis` is Mathlib's, not locally defined |

All 88,114 `set_option` uses are benign (mostly `maxHeartbeats`); none disable
proof checking.

**What we explicitly did not determine:** whether the ~291 `LiteratureTheorems`
correspond to real published results, what role `OpenImageCondition` actually
plays, and whether the mathematics is correct. Details in FINDINGS.md, section
"What we did NOT determine".

## The four checks

Each check answers one question. None of them produces a score or a verdict —
they produce raw findings.

### Check 1 — `sorry`

`sorry` is Lean's explicit placeholder for "not proved here".

If the release is described as a complete formalization, then a single `sorry`
in a load-bearing position contradicts that description.

### Check 2 — `axiom`

Lean lets you assume something outright. A proof that assumes a statement
equivalent to GRH is valid Lean and does not establish GRH.

Checks 1 and 2 share one script (they are the same kind of scan):

```
check-sorry.py
```

### Check 3 — bypass constructs

`sorryAx`, `native_decide`, `implemented_by`, `extern`, `opaque`, `unsafe`.
These can let a proof pass checking without actually proving anything.

```
check-bypass.py
```

### Check 4 — what was actually stated

The thing that was formally stated, compared against the standard formulation.
Also checks whether `RiemannHypothesis` is Mathlib's definition or a local one
(a locally defined "RiemannHypothesis" could be made trivially true).

```
check-statement.py
```

## Validating the checkers themselves

A checker that silently misses things is worse than no checker.

```
test-checker.py
```

11 known-answer cases covering false-positive traps (`sorryFree`,
`my_sorry_thing`, `sorryAx`) and false-negative traps (`-- sorry` inside a
comment). **11/11 pass.**

## How to reproduce

Requires Python 3.10+ and Node 18+ (only for the download step), ~1 GB free disk.

```bash
python test-checker.py    # instant — validate the checkers first
node   fetch.mjs          # ~3 min, downloads 14 parts (228 MB), merges into one tar.gz
python extract.py         # ~4 min, extracts 175,190 files (handles Windows long paths)
python check-sorry.py     # ~4 min, scans 17.4M lines
python check-bypass.py    # ~4 min
python check-statement.py # instant
```

> **Windows note:** do not use `tar.exe` to extract. It silently skips every
> path over 260 characters — that is 74,000 of the 175,000 files. `extract.py`
> handles this. We learned it the hard way; see FINDINGS.md "Mistakes we made".

Outputs land in `lean-full/`. Paste them into an issue if they differ from what
is committed here.

## A note on reading our own results

The first thing we did was test the checkers against known answers
(`test-checker.py`, 11 cases). That is not ceremony — our first run of
`check-sorry.py` read only 100,619 of 175,073 files because Windows `tar.exe`
had silently dropped every long path, and the "0" it printed was meaningless.

**If you re-run this, check the "unreadable" count in the output. It must be 0.
A non-zero count invalidates the result below it.**

## What we are not claiming

- We are not claiming the proof is wrong.
- We are not claiming the proof is right.
- We are not claiming to have read 17 million lines. We have not.
- We are not attempting to judge the mathematics. We are checking the artifact.

## If you find an error in this repository

Please open an issue. The most likely failure mode here is not "the proof is
wrong" but "our check is wrong" — we are the less reliable party in this
comparison.

## Who ran this

The checks were written and executed with **DeepSeek V4.1 Flash** as the
executing model, working from a human operator's instructions.

We are publishing under the model's name rather than behind a personal name on
purpose: a model can be re-run with the same instructions. A person cannot.
If the results here are wrong, they should be re-runnable and therefore
falsifiable.
