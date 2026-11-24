# Findings

**Date:** 2026-11-24
**Artifact:** `https://alpo.ge/lean.tar.gz.part01` … `part14` (merged: 228.19 MB, extracted: 175,190 files)
**Note:** `https://alpo.ge/remark.pdf` (4 pages, read in full)
**Runner:** DeepSeek V4.1 Flash
**Status:** four checks done. Two more questions open, and we do not claim answers to them.

---

## What we measured

### Scale

| item | value |
|---|---|
| `.lean` files | **175,073** |
| total lines | **17,363,528** |
| archive parts | 14 (part01–13 ≈ 18,000,000 B each, part14 ≈ 5,272,000 B) |
| longest path | 327 chars (Windows tar.exe silently drops >260) |

The "roughly 17 million lines" figure in press reports matches what we counted.

**Note on the note:** the 4-page note does *not* state a page count or a line count.
It says the argument is "incredibly long" and that formalization "is finished".
The 250,000-page figure comes from press reporting, not from the note itself.

### Check 1 — `sorry`

```
0 occurrences
```

Method: regex `(?<![A-Za-z_])sorry(?![A-Za-z_])`, per line, after stripping `--` comments.
The checker was validated against 11 known-answer cases (11/11 pass,
including the false-positive traps `sorryFree`, `my_sorry_thing`, `sorryAx`,
and the false-negative trap `-- sorry` in a comment).

Files unreadable: **0** (after fixing a long-path bug — see "Mistakes we made" below).

### Check 2 — `axiom`

```
0 occurrences
```

This directly supports the note's claim:

> "Claude and I have also formalized the arguments without assumptions."

### Check 3 — bypass constructs

```
sorryAx          0
native_decide    0
implemented_by   0
extern           0
opaque           0
unsafe           0
```

88,114 `set_option` occurrences, top entries:

```
57,545  maxHeartbeats                (evaluation time limit — harmless)
11,203  autoImplicit                 (implicit variable binding)
 7,478  maxSynthPendingDepth         (typeclass inference depth)
 7,370  synthInstance.maxHeartbeats
 1,879  backward.isDefEq.respectTransparency
   ...
```

None of these disable proof checking. The high `maxHeartbeats` count is expected
for a codebase this size.

### Check 4 — what was actually stated

`src/Statements.lean` is 12 lines. The core definitions:

```lean
def RiemannZetaZerosOnLine : Prop :=
  ∀ s : ℂ, riemannZeta s = 0 →
    (¬∃ n : ℕ, s = -2 * ((n : ℂ) + 1)) →   -- exclude trivial zeros
    s ≠ 1 →                                  -- exclude the pole
    s.re = 1 / 2
```

```lean
def DirichletLNonvanishingRightOfHalf : Prop :=
  ∀ (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N) (s : ℂ),
    1 / 2 < s.re → (χ ≠ 1 ∨ s ≠ 1) → DirichletCharacter.LFunction χ s ≠ 0
```

Both are standard formulations.

**`src/Main.lean` is 7 lines:**

```lean
theorem riemannHypothesis : RiemannHypothesis := rhOfAll
```

**`RiemannHypothesis` here is Mathlib's, not a locally defined predicate.**
That matters: a locally defined "RiemannHypothesis" could be made trivially true.

---

## What we did NOT determine

### A. Whether `OpenImageCondition` is an assumption

`src/.../TemperedProductOfSquareIntegrable.lean:207`:

```lean
structure UpperTheory.LiteratureTheorems.OpenImageCondition : Prop where
  galoisRepOfPolarizedPairLit : _root_.UpperTheory.V.Z.Win.RowT
```

Roughly 176 theorems are named `..._of_open` and take this as a parameter.
**In at least some of them, the parameter does not appear in the proof body:**

```lean
theorem UpperTheory.LiteratureTheorems.elliptic_main_theorem_cm_of_open
    (O : OpenImageCondition) : GlobalTheory.Published.EllipticMainTheoremCM :=
  PositivityTheory.Prw.ellipticMainTheoremCM_holds
```

This is legal Lean — an unused parameter still type-checks — but it means the
`_of_open` suffix does not by itself imply a dependency on `OpenImageCondition`.

**We do not know whether this is packaging convention, a leftover from
generation, or something else. We did not determine it, and we are not
asserting it is a problem.**

### B. Whether the ~291 `LiteratureTheorems` correspond to real results

These are named after standard results (`deligne_ribet`, `global_artin_reciprocity`,
`siegel_klingen_deligne_ribet`, `bernstein_zelevinsky_finiteness`, …).
Verifying that each matches the published statement requires domain expertise
we do not have. We checked only that they are `theorem`s, not `axiom`s.

### C. Whether the mathematics is correct

We are not attempting to judge this. The checks above are about the artifact,
not the argument.

---

## Mistakes we made (recorded because they matter)

1. **Long-path bug.** First extraction used Windows `tar.exe`, which silently
   skipped 74,000 files with paths over 260 characters. First `sorry` scan read
   only 100,619 of 175,073 files. The "0" was meaningless. Fixed by extracting
   with Python and using the `\\?\` prefix; unreadable count is now reported.

2. **A bogus measurement.** A script counting whether `_of_open` theorems use
   their parameter matched on the single letter `O` across a 2000-character
   window. It reported 64/64 "used". Manual inspection shows at least one that
   does not. The script was wrong; the number was discarded.

3. **Reading a comment as code.** `strip_comments` only handles `--`, not
   multi-line `/- -/`. This can produce both false positives and false negatives.
   We did not find any case where it changed a result, but the method is weaker
   than it looks.

---

## Reproduction

```bash
python fetch.mjs      # ~3 min, 228 MB
python extract.py     # ~4 min, handles long paths
python check-sorry.py
python check-bypass.py
python test-checker.py
```

Everything needed is in this repository. If your numbers differ, please open an
issue with the output.
