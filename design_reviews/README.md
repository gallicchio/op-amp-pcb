# Design reviews

Independent reviews of the board before it is ordered, by other LLMs and by the
author, each in its own dated directory so that several can run at once without
touching each other or the project:

    design_reviews/
      DESIGN_REVIEW_PROMPT.md           the brief to give a reviewer
      <YYYY-MM-DD>_<Model-Version>/     one reviewer's directory: REPORT.md and
                                        everything it made or copied
      <YYYY-MM-DD>_<Model-Version>/project/   a reviewer's working copy of the
                                        project (gitignored; never committed)

A reviewer only ever writes inside its own directory. The brief says what to review,
how to work and what the report must contain. A later round gets a later date, so the
rounds sort themselves.

## Round 1, 2026-10-24: rev A before ordering

| directory | reviewer | verdict |
|---|---|---|
| `2026-10-24_Claude-Fable-5.1/` | the author (Claude Fable 5.1), written before reading any other | order after named fixes: COMPENSATION 2 alone is open circuit, not the bare 100 pF (rewire pole 2); "a short to a rail is survived" is false for the stocked SOT-23 (words); the 50 mA supply limit as the rule; ON marks on the switches; stale numbers. Patch in its `patch_round1.diff`, built clean in its copy; applied to the project on 2026-10-25 before the round opened, with the input terminals' ground symbols turned down as well |

| `2026-10-27_Gemini-4-Argon/` | Gemini 4 Argon | order after named fixes: follower oscillates with 100 pF of coax once the output leaves the dead band; PLACEMENT_CHECKS lookup bug; KF301 terminals 180 degrees round; the 50 mA limit does not save R8 from a ground clip; simulation at +/-15 V without the Schottkys; stale C2/C3 node names and an open-loop IN- trap; KiCad finder; "Q6 B" fix; wiper-open wording; short-circuit current inflated by input-clamp current |
| `2026-10-27_KimiK3/` | Kimi K3 (by Jason's account; it signed itself "Claude (Copilot SDK session)", so the directory was renamed) | order as it is, with documentation fixes: the 50 mA limit does not save R8; THT joint count 18 should be 27; no maximum supply voltage (25 V bypass caps); both TAIL sliders on leaves the null range; jack label 20 mA vs 15 mA; stale numbers; netlist carries an absolute path |

### What changed (applied 2026-10-27, before ordering rev A)

Checked by evidence before applying: the coax oscillation by transient simulation at
5 V (200 mV of 13 MHz ringing, also with transistors half as fast), the terminal
orientation against the KEFA drawing (the 3.60 dimension is the pin length; the pins
sit 4.0 mm from the back, so the wire face is EasyEDA's +y), the ground-clip powers by
arithmetic and simulation, the Schottky drop from its datasheet curve (0.18 V at 4 mA,
not 0.35).

- **R17**, 47 ohm from OUT to both jacks; the feedback is taken before it.  Clean from
  100 pF to 1 nF at any level; 4.5 % less into 1 k.  Q7 and Q8 spread 1.6 mm to make room.
- **R8 a 1 W 2512, R7 a 0.25 W 1206**: ground clips on Q3 E, Q2 C, Q6 E, Q6 B burn nothing.
  The 2512 is one more Extended code.
- **KF301 rotation +180** and the footprint's body flipped to match the drawing.
- **PLACEMENT_CHECKS**: every row that names a part, each with its own designators;
  the SOT-23 line says "lone pad (pin 3)", not "on the collector wire's side".
- **Simulation**: B5819W model in each rail, bypass caps, R14 and R17 in the core,
  rails and currents from the run, unwrapped phase, short-circuit current measured
  open loop at the jacks (16.9 mA, not 21.8).  Every quoted number regenerated.
- **Silkscreen**: R5 east so "Q6 B" is clear; RV1 50R; ground stubs drawn; "-15V"
  clear of D4; the OUT jack says 15 mA; the back says +/-16 V, 17 mA and R17.
- **Documents**: the ground-clip truth, +/-16 V, both-TAIL-on, open-loop IN-
  grounding, Q2 C / Q3 C names, wiper-open, Ib 2 uA, stage gains, margins, joint
  counts (27 THT), one parts total ($7.82).
- **Build**: duplicate pad numbers kept (joint count), netlist without absolute path
  or date, KICAD_APPIMAGE honoured over a KiCad 9 on PATH, dead USB check removed,
  stray scratch files removed.

Not changed: the Extended-fee question on through-hole codes (unverified); C2/C4 at
25 V (handbook says +/-16 V; 35 V parts are on the rev B list); Gemini's C1 = 220 pF
alternative (R17 cures the cable without leaving the book's value).
