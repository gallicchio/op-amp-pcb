# Design review: Discrete Transistor Op-Amp, rev A — 2026-10-27_Claude

Reviewer: Claude (Copilot SDK session), 2026-10-27. Reviewed the committed rev A
(board date 2026-10-24) plus a full rebuild of a private copy
(`project/`, KiCad 10.0.7 AppImage, libngspice present). All simulations and
renders mentioned below are kept in this directory.

## 1. Verdict

**Order as it is**, with `PLACEMENT_CHECKS.txt` in hand at the preview, and apply
the documentation fixes in `review-fixes.patch` when convenient (none of them
touches copper). I rebuilt the project from scratch and got byte-identical
gerbers; ERC 0, DRC 0 (re-run by me at all severities with schematic parity), 102
circuit assertions, fab checks green, 28/28 document claims. Every circuit claim I
re-derived or re-simulated held. The worst thing I found is a wrong sentence about
the 50 mA supply limit "saving" R8 (it does not — see Finding 1); everything else
is a wrong count, a missing rating line, or a label that could teach a slightly
wrong number. The residual risks are the ones the author already lists: predicted
rotations (I verified each geometrically against EasyEDA's current drawings and
agree with every angle) and real-silicon phase margin (the docs already expect
less than the models say, and the models say the margin survives that).

Confidence: high on the circuit, the fab package and the documents; moderate on
the "assembled correctly first time" claim only because no preview has been seen,
which the author already says.

## 2. Findings

| # | Severity | Where | Finding |
|---|----------|-------|---------|
| 1 | major | docs/HANDBOOK.md:36-40 and :215 | "The 50 mA supply limit is what saves R8" / "cannot burn anything" is wrong: a ground clip on Q2 C or Q3 E draws ~44 mA — under the limit — while R8 (0805, 0.125 W) dissipates 0.6 W, ~5x rating, indefinitely |
| 2 | minor | scripts/gen_pcb.py `place()`/`export_geometry()` | THT joint count is 18, should be 27: the BNC's four ground posts share pad number "2" and collapse to one entry in `self.pads`; every THT joint count and cost line in MANUFACTURING.md is low by 9 joints/board (~$0.54 on a 2-board order) |
| 3 | minor | docs/HANDBOOK.md section 2, layout.py TEXTS | No maximum supply voltage anywhere; +30 V on one terminal puts 29.6 V on the 25 V-rated C2 (10 uF), and ±30 V can put ~59 V across Q3 (40 V part). Suggest a "+/-16 V max" line |
| 4 | minor | docs/HANDBOOK.md:73 | "Both TAIL sliders on ... harmless": tail current doubles to 2.8 mA and the follower offset becomes +65 mV — beyond RV1's +/-33 mV null range. No damage, but the offset exercise fails silently |
| 5 | minor | layout.py TEXTS (98.8, 36.4) vs docs/HANDBOOK.md:50 and back text | The OUT jack's silk says "±13 V 20 mA"; the handbook and the back of the board say "±12 V into 1 k, 15 mA". 20 mA is the short-circuit current, 15 mA the design limit; the jack label reads like a rating |
| 6 | nit | scripts/gen_sch.py title block vs layout.py BOXES vs docs | Stage-2 gain is printed as x30 (silk box), "about 30" (HANDBOOK ex. 4), 34 (DESIGN_NOTES), and x12 (schematic title block, because results.json's `g2` = a0/gdiff1 includes the push-pull dead zone). A student measures ~34 at TP8/TP6 |
| 7 | nit | scripts/gen_sch.py notes band vs docs/HANDBOOK.md section 9 | Input bias current is "about 5 uA" on the sheet and "about 2 uA" in the handbook and on the back of the board (sim: 2.3 uA at Bf=300; up to ~10 uA at the Bf=70 floor) |
| 8 | nit | scripts/gen_outputs.py:382 vs scripts/gen_docs.py | Parts cost is printed $7.77/board by the BOM stage (unrounded total) but $7.78 in the documents (sum of 3-decimal-rounded line items). Each is checked against itself, so the build never notices |
| 9 | nit | docs/DESIGN_NOTES.md:71 | "unity-gain crossing is 14 MHz"; sim says 14.96 MHz (and the round's own prompt says 15). Not among the 28 checked numbers |
| 10 | nit | scripts/check_circuit.py:147 | Stale comment: "33 ohm in each emitter" where the asserted value is 47 ohm |
| 11 | nit | out/opamp.net:4 | The committed netlist embeds the author's absolute build path (`/home/jason/mnt/.../hardware/opamp.kicad_sch`) — against the "relative paths only" rule and the only absolute path in the tree |
| 12 | nit | hardware/opamp.kicad_pcb, layout.py TP_LABEL | Confirmed still present (already known, per the prompt): the "Q6 B" label overlaps R5's ground symbol — verified on the current 600 dpi render (`z_tail.png`) |

### Finding 1 — the 50 mA limit does not save R8 (major)

docs/HANDBOOK.md section 2 says the 50 mA supply limit means a scope ground clip
on the wrong loop "cannot burn anything", and the symptom table (section 10) says
"The 50 mA supply limit is what saves R8".

The arithmetic: a clip on TP7 (Q3 E) shorts the bottom of R8 to ground, so R8
sees the full +14.6 V rail: P = 14.6^2 / 330 = **0.65 W**, at I = 44 mA. The
board's other +15 V loads add ~4 mA, so the rail draws ~48 mA — *under* the 50 mA
limit; the supply never limits and R8 sits at 5x its 0.125 W rating until someone
smells it. The clip-on-TP6 (Q2 C) case is the same: Q3's base-emitter is then
forward-biased through R8 to the rail, I = (14.6-0.7)/330 = 42 mA, P(R8) = 0.59 W
(R3 also takes 0.14 W, 1.1x rating). Total ~56 mA: the limit may just engage, and
R8 still gets ~0.5 W. Either way the limit is not what saves R8; the smell is.
The transistors do survive (that's the good half of the claim), and the symptom
table's "a resistor smells hot" is the honest version.

Expected: the docs should not teach that the 50 mA limit covers this case.

Fix (in `review-fixes.patch`): reword both places; the 50 mA rule stays (it does
bound output shorts, rail clips and transistor faults).

How sure: high — arithmetic from the documented rail voltage and resistor values;
the current is below the limit by construction.

### Finding 2 — THT joint count is 18, the true count is 27 (minor)

In `gen_pcb.py`, `place()` records pads in `self.pads[(ref, pad.GetNumber())]`.
The custom BNC footprint has four ground posts all numbered "2" (verified in
`hardware/lib/opamp.pretty/BNC_KYWE_RightAngle.kicad_mod`: pads "1","2","2","2","2"),
so the dict keeps only the last post. `export_geometry()` writes
`out/pcb_geom.json` from that dict, and `gen_docs.py joint_counts()` counts THT
joints from it: 18. Counting the board file directly (my `count_joints.py`, run
under KiCad 10's pcbnew): **27** (J1/J2/J3: 5 each; J4/J5/J7: 2; J6: 3; RV1: 3).

Everything quoting joints is therefore low by 9 per board: "112 SMT and 18
through-hole joints" (DESIGN_NOTES section 4, MANUFACTURING), the cost table lines
"224 SMT and 36 THT joints" (should be 54), etc. At $0.03/THT joint the assembly
lines are underquoted by $0.54 (qty 2) to $2.70 (qty 10) — JLCPCB counts joints
from the real files, so the order page will simply show a slightly higher number
than the document. Nothing stops the line; the numbers are wrong, and they are
among the "checked" numbers — checked against a buggy source.

Fix (in patch): keep all pads by disambiguating duplicate pad numbers in
`place()` (`"2#2"`, `"2#3"`, ...). Wire resolution by ("ref","2") still finds the
first post, which is all the router needs. Py-compiles; I did not rerun the whole
build with it.

How sure: high — reproduced from the committed board file.

### Finding 3 — no maximum supply voltage; the 25 V bypass caps go first (minor)

The silk and docs say "+15 V, GND, -15 V" and the inputs carry "±12 V max", but no
rail limit is stated, and the reverse-protection Schottkys invite confidence.
With +30 V on the +15 terminal (other rail normal): the rail sits at ~29.6 V and
C2 (10 uF, **25 V** rated, C15850) is over voltage; all transistors stay within
their 40 V Vceo (worst is Q1/Q4 at ~30 V). With ±30 V on both, Q3's Vec can reach
~59 V when open-loop drives its base up. Neither is a likely bench accident, but
"30 V between one rail and ground" is exactly the kind of thing a student does
with a dual supply, and the fix is one line of text.

Fix (in patch): HANDBOOK section 2 gains "Stay within +/-16 V at the terminal:
the 10 uF bypass capacitors are 25 V parts and Q3 and Q6 are 40 V parts."

How sure: high on the capacitor (its rating is on the BOM), moderate on how much
it matters — X5R MLCCs tolerate some overvoltage; it is out of spec, not
necessarily fatal.

### Finding 4 — both TAIL sliders on: works, but the offset leaves the null range (minor)

HANDBOOK section 4: "Both TAIL sliders on puts the resistor in parallel with the
sink, which is harmless." Simulation (`sim_extra.py`): the tail becomes
1.39 mA (sink) + 1.43 mA (R4) = **2.82 mA**; the loop still holds OUT at zero but
the follower offset moves from -5.6 mV to **+64.6 mV** — beyond the +/-33 mV the
trimmer can null. No damage; but a student who nulls with both sliders on cannot,
and the loop table's voltages no longer match. The current wording invites the
combination.

Fix (in patch): say what happens and to null with slider 2 off.

How sure: high (simulation, reproduced twice).

### Finding 5 — the OUT jack's silk label disagrees with the handbook (minor)

Front silk beside J3: "±13 V 20 mA" (layout.py TEXTS, (98.8, 36.4)). HANDBOOK
section 3 and the back of the board: "±12 V into 1 k, 15 mA". The swing is
-14.3/+13.4 V into the 11 k divider and the short-circuit current is ~22 mA
(15 mA through Q4/Q5) — so each number exists somewhere, but the jack's "20 mA"
reads as a rating while the design rating is 15 mA. Suggest "±13 V, 15 mA" (or
"limits at ~20 mA") so the jack, the handbook and the back agree.

How sure: high that the texts disagree; the choice of wording is the author's.

### Finding 6 — stage-2 gain quoted four ways (nit)

Silk box: "GAIN STAGE x30". HANDBOOK exercise 4: "about 30". DESIGN_NOTES: "stage
2 gives 34" (matches 12k/(330+re) = 34.2 and the sim: a0 = 11.11 x 33.6 x 0.37).
Schematic title block: "gain x12", because results.json's `g2` = a0/gdiff1 folds
in the push-pull's 0.37 quiescent gain. The story note on the sheet explains it
("... = 30; the push-pull's dead zone takes a third of it x12") but the title
block's bare "gain x12" next to "difference x11" reads as the stage's gain.
Fix (in patch): title block now says "gain x30 ... (the push-pull's dead zone
takes stage 2 down to x12)". Note the "x30" then duplicates layout.py's
hardcoded box title rather than deriving from a checked number — a `g2_stage`
key in results.json would be the cleaner fix.

### Finding 7 — input bias current quoted as both 5 uA and 2 uA (nit)

Schematic INPUTS note: "Ib (about 5 uA) drops 5 mV across it." HANDBOOK section 9
and the back of the board: "about 2 uA". Sim at the shipped models: 2.3 uA; at
the Bf=70/80 datasheet floor ~9 uA. Both are defensible; they should be the same
sentence. No patch (one judgement call for the author).

### Finding 8 — $7.77 vs $7.78 (nit)

`gen_outputs.py` prints the parts total unrounded ($7.7729 -> "$7.77/board");
`gen_docs.py` sums the BOM's 3-decimal-rounded `Ext $` column ($7.7790 -> $7.78,
which is what README.md and MANUFACTURING.md quote, and the claims check passes
because it checks gen_docs' own sum). One cent; exactly the kind of split-brain
the one-source-of-truth rule exists for.

### Finding 9 — "14 MHz" vs 14.96 MHz (nit)

DESIGN_NOTES section 3 says the simulated unity-gain crossing "is 14 MHz";
sim/results.json says 14.96. Not among the 28 checked claims. Patch: "15 MHz".

### Finding 10 — stale comment (nit)

check_circuit.py:147: "33 ohm in each emitter" above an assertion that checks 47
ohm. Patch: comment now says 47.

### Finding 11 — absolute path in out/opamp.net (nit, publishing)

The committed netlist's header carries
`/home/jason/mnt/local4TB/2TBext4/frank/stuff/mudd/pcbs/op-amp-pcb/hardware/opamp.kicad_sch`
(KiCad's exporter writes it; the build's timestamp-normaliser doesn't touch it).
The only absolute path in the tree. Not sensitive, but against the project's own
"relative paths only" rule.

### Finding 12 — "Q6 B" over R5's ground symbol (nit, known)

Verified on the current board (my 600 dpi render `z_tail.png`): the ground
symbol's bars strike through the "Q6" of the "Q6 B" label. Listed as already
known in the review brief; confirming it survived to this revision.

## 3. Section-3 questions, answered

### 3.1 The circuit against the book

Read `gen_sch.py`, the exported netlist, and `check_circuit.py`; ran the 102
assertions on the committed netlist (pass). Every value and connection of the
Fig. 5L.15 list is present and asserted: 1.5 k collector load on the IN+ side
(Q1's collector straight to the rail), tail = 10 k or the Fig. 5L.10 sink
(62 k / 10 k divider, 1 k emitter; divider puts the base at -12.9 V, sink
1.4-1.5 mA — the book's "about 1.5 mA"), PNP common-emitter 330/12k, 100 pF
Miller, push-pull, 10k/1k divider with tap X to IN-. Global polarity checked by
hand: Q2 C is inverting w.r.t. IN+, Q3 inverts again, so IN+ is non-inverting
and feedback lands on IN- — right. Q3 is drawn and wired the right way up for a
PNP (emitter through R8 to +15, collector through R9 to -15, emitter arrow in).

`check_circuit.py` asserts everything topological that matters, including switch
pole-to-pin mapping, diode directions by pin number, the probe loops' nets, and
no one-pin nets. What it does NOT assert: the values of the six diodes and the
LEDs (a value/LCSC swap between the 1N4148W and B5819W lines would not be caught
here — though both travel together through `parts.py`, so the generator cannot
produce it; only a hand edit could), TP1/TP2's "0.0 V" expectations (b1/b2 are
not in results.json's op dict), and the trimmer's physical pin-2-is-wiper fact
(true for the 3362P — verified against the vendor drawing — but only the netlist
side is asserted).

Caveat: the book itself was not available to me (not in the repo, by design), so
the quotation check is from my knowledge of Lab 5L plus internal consistency
(the quoted values reproduce the book's quoted ~1.5 mA tail). The values match
what I know of Figs. 5L.10/5L.15.

### 3.2 What the board adds

- **Offset null** (`sim_extra.py`): range is -37.5/+28.8 mV at the output as a
  follower, i.e. a 66 mV span, "+/-33 mV" as documented, comfortably over the
  nominal -5.6 mV offset and the simulated 2:1 beta-mismatch offset (-3.8 mV).
  Stage-1 gain with the wiper at an end is unchanged (~12): the two emitter
  resistances always sum to 50 ohm. Wiper fully open: the tail dies and OUT parks
  at the negative rail (simulated: OUT = -13.5 V) — no damage, but the
  DESIGN_NOTES claim "grit under the wiper cannot open the tail" is only true of
  *resistive* wiper degradation (the wiper is in series with a current-sink
  collector, so added resistance is invisible); an open wiper is the classic
  trimmer failure and does kill the pair. Patch rewords it. Ends shorted:
  emitters tied together — degeneration gone, gain rises toward the book's ~20,
  nulling lost, no damage.
- **Input protection**: worst case (inputs at opposite rails): I =
  (30-0.7)/2k = 14.65 mA, P = 0.215 W in each 1206 — inside the 0.25 W rating, as
  documented. The off transistor's base-emitter sees ~0 V reverse, not 6 V: the
  clamp holds the bases 0.7 V apart and the live transistor's emitter follows its
  own base (worked through, then confirmed by the topology). One input at +20 V,
  other grounded: 9.7 mA, 0.09 W — fine. The clamp never conducts in normal use
  (needs |Vdiff| > 0.7 V; open-loop exercises use millivolts; the 8L comparator
  guidance about keeping hysteresis under a volt is in HANDBOOK section 9).
- **R14**: the zero arithmetic in `check_circuit.py` checks out: with 330 ohm
  degeneration the feedforward transconductance is ~1/350 S, so the bare cap's
  RHP zero sits at 1/(100 pF x 350) = 4.5 MHz and the 1 k moves it to the LHP at
  1/(100 pF x (1000-350)) = 2.4 MHz. Sim: follower PM 50.8 deg with, -42.6 deg
  without. Switch positions do what the HANDBOOK says (pole 1 = 100 pF + 1 k,
  pole 2 = bare 100 pF; both on = pole 2; verified in the netlist and the pad
  dump). The post-patch wiring is confirmed correct: SW2 pole 2 bypasses R14.
- **Output current limit**: 0.65/47 = 13.8 mA design; simulated 14-15 mA through
  Q4/Q5, 17-22 mA total into a dead short depending on drive (results.json quotes
  21.8 mA; my harder-driven variant got 17.2 mA — the difference is how hard the
  loop pushes, both are "about 20 mA"). Both polarities limit symmetrically
  (14.5/14.0 mA). OUT to ground: 208 mW in Q4 — "minutes" at 625 K/W is fair
  (Tj ~ +130 C over ambient, right at the edge, as the docs say). OUT to a rail:
  423-431 mW — twice the 0.2 W rating, "a slip, not a minute" is accurate.
  Limiter invisible in normal use: x11 2 V-peak swing is bit-identical with the
  limiter deleted (my sim): -14.29/+13.41 V both ways. The HANDBOOK's current
  wording ("a short to ground is survived ... a short to a rail, only for
  seconds") is true.
- **D3/D4**: polarity verified three ways (netlist assertions; pad-level dump of
  the built board — D3 cathode on the +15 V rail, D4 cathode on the terminal;
  600 dpi render). Drop 0.35-0.4 V at 4 mA -> rails at +/-14.6 V, as quoted.
  Reversed supply: both block, no LED, nothing forward-biased. Single rail: the
  other rail floats up through the loads; nothing exceeds ratings; it just
  doesn't work. +30 V on one terminal: see Finding 3 (the 25 V bypass cap is the
  first casualty).
- **LEDs and bypass**: 1.2 mA per rail through 10 k (checked in the assertions);
  LED1/LED2 cathodes verified on the board file against the MANUFACTURING preview
  instructions. C2/C4 10 uF + C3/C5 100 nF per rail, placed at the rail ends.
  C2/C4's 25 V rating is the board's voltage ceiling (Finding 3).

### 3.3 Stability and the simulation

Models vs onsemi MMBT3904/MMBT3906 datasheets: CJC 4/4.5 pF = Cobo max 4/4.5 pF
(ok); CJE 8/10 pF = Cibo max 8/10 pF (ok); TF 350 ps gives fT ~300 MHz with the
caps at the operating point (datasheet min 300/250 MHz); Bf 300/200 is the
datasheet *maximum* at 10 mA (typical is lower). So the shipped models are at
the fast/happy end — which is exactly why I re-ran the margins at the slow end
(`sim_models.py`): Bf=100/100 -> PM 55.7 deg; Bf=70/80 (datasheet floor at 1 mA)
-> PM 60 deg (A0 rises to ~195); fT halved and caps +50% -> PM 47 deg; strays
3 pF -> 10 pF -> PM 43 deg. The 51 deg claim survives every datasheet-plausible
model I threw at it.

The new questions:

- **10x probe (15 pF || 10 Meg) on TP8**: follower PM 50.8 -> **39.2 deg** (with
  the 1 k); on TP6: **35.1 deg**; both probes: **25.0 deg**. Without the 1 k it
  oscillates regardless (-45 deg). Matches the author's r4 numbers (39/35/25).
  Stable but visibly ringier; x11 barely moves (117-119 deg).
- **A metre of coax (~100 pF) on OUT, FEEDBACK 2**: step overshoot 6.4 %, no
  ringing; 1 nF -> 12.9 %; even 10 nF -> 18.1 % and no sustained ringing. The 47
  ohm sense resistors already isolate the emitters from the load: the rev B item
  "47 ohm in series with OUT" is **not needed** (and is in fact no longer in the
  rev B list — confirmed resolved).
- **Both FEEDBACK sliders on** (R10 shorted): a follower with a 1 k load to
  ground, PM 104.7 deg, offset -3 mV. The HANDBOOK sentence is exactly right.
- **x11 with 2 V peak in**: swing -14.29/+13.41 V (results.json: -14.28/+13.41);
  max |dV/dt| 0.36 V/us at 1 kHz — no slew limiting at exercise amplitudes.
  Follower slew on a 10 V step: **4.7 V/us up, 5.3 V/us down** (20-80 %), under
  the tail-current ceiling of 14 V/us at the Miller node; "several V/us" in the
  HANDBOOK's LF411 table is fair.
- **Crossover dead band at TP8** (exercise 5): open-loop rest has Q3 C at -1.61 V
  and OUT at -1.02 V; pushing +/-50 uA into Q3 C moves OUT only after the ~1.2 V
  band — consistent with the documented "dead band of about 1.2 V".
- Also ran: **TAIL 2 (10 k)** follower PM 47.8 deg (both tail variants are
  stable); **COMPENSATION both off**: follower PM -39 deg (oscillates), x11 PM
  +17.8 deg (rings hard) — the sheet's note "Both OFF: no compensation, and the
  x11 amplifier rings" is accurate.

### 3.4 The silkscreen as a schematic

Read the committed renders, the r4 close-ups, and my own 600 dpi render of the
current board (`board600.png`, crops `z_*.png`).

- Junction dots appear wherever three wire-ends of a net meet and at
  end-on-wire T's (the logic in `silk_wires()` is generic, not hardcoded; I
  verified dots at Q2 C, the emitters/trimmer T's, the OUT node, the X tap, the
  Q6 B three-way, and every rail drop). Hops draw as semicircle jumps with the
  two vias visible beside them (verified the Q2 B hop over TAIL, both D6-bus
  hops, the OUT-drop hop). All 8 hops present.
- Every transistor: correct B/C/E letters, emitter arrow out for NPN and in for
  PNP (checked all eight at 600 dpi), hairlines from pads to leads. The PNP
  collector hairline runs down between the B and E pads as designed; DRC says
  the ~0.48 mm side clearances hold.
- Labels: switch legends, box names and loop names all match HANDBOOK.md.
  "ON" marks sit where PLACEMENT_CHECKS says (left of SW1, above SW2, "ON>"
  above SW3's right pads). Known overlap "Q6 B"/R5's ground symbol confirmed
  (Finding 12). TP9/TP11/TP12 are deliberately unlabeled (on the labelled OUT
  jack/rails) — reads fine.
- Grounds point down, except the -15 V-side bypass caps whose stubs run up and
  whose symbols point up — consistent with the schematic's language.
- One departure from "the silkscreen is the schematic": the six diodes are drawn
  as the SOD-123 body cup with the closed end marking the cathode — no triangle.
  Polarity marks are correct and consistent with every document (verified pad by
  pad), so this is an assembly-safe choice, but D1/D2 are the one place a student
  reading the board as a schematic meets a non-schematic symbol (the INPUT
  PROTECTION box title and the "1N4148W" label carry the meaning). Observation,
  not a finding.
- The push-pull box's missing "x1" is listed in the brief; the FEEDBACK legend
  carries it. Fine.

### 3.5 Copper and board

- Copper follows the silk wires by construction (`gen_pcb.py` lays tracks along
  the drawn wires; DRC schematic-parity re-run by me: 0 violations, 0 unconnected
  pads at all severities). 226 tracks, 32 vias, 8 hops as claimed.
- Hops: each is a back-layer segment between two 0.8/0.3 mm vias under a silk
  arc — verified in the B.Cu render (`z_bcu.png`): the plane stays continuous
  everywhere; no islands or narrow necks; 32 vias = 16 ground stubs + 16 hop
  ends.
- 0.35 mm signal tracks are ~1 A territory at 1 oz — 20 mA is nothing. Rails
  0.6 mm. Min clearance rule 0.20 mm, hole clearance 0.30 mm; DRC clean, so the
  M3 holes (nearest copper: the fiducials, 7.6 mm away) and BNC flanges are
  clear.
- Three fiducials at (11,7), (89,7), (11,92) — three corners, asymmetric, clear
  of the mounting holes and the title band; the order form's "Added by JLCPCB"
  for rails is consistent.
- Custom footprints vs their drawings: BNC (drills 1.3/1.4 mm vs JLC's 1.2/1.4 —
  fine; posts on a 8x8 mm square as the part's drawing), 3362P (pads match the
  vendor drawing to 0.04 mm; keyed by the L of three holes — the build re-proves
  it fits one way), KF301-2P/3P (5.0 mm pitch, pins along x, pin 1 at the -x end,
  matching JLC's land), DSIC02 (columns 8.8 mm: from the vendor's 6.60 mm inner +
  2.2 mm pads; 2.54 mm pitch; pads 1,2 left / 4,3 right as KiCad's SW_DIP_x02
  assumes), RH-5019 (single 4.0 x 2.2 mm pad, exactly JLC's).
- SOT-23 pad assignment: KiCad SOT-23 pads 1=B, 2=E, 3=C; onsemi MMBT3904/
  MMBT3906 pin 1 = base, 2 = emitter, 3 = collector. Match.

### 3.6 The JLCPCB package

- Rotations: I fetched every code's current EasyEDA land pattern
  (`scripts/easyeda.py` in the copy) and fitted it to ours by pin number.
  SOT-23: their pad 1 at (+1.0,+0.95) vs KiCad's (-0.94,-0.95) -> **+180
  correct** (pad 3 lands on pad 3 too; checked both codes). DSIC02: their pads
  stand along y, ours lie along x; mapping pin 1 to pin 1 needs **+270 —
  correct**. SOD-123 (both codes): pad 1 at -1.7 in both -> **0 correct**.
  KF301-2P/3P, 3362P, RH-5019: geometries identical, pin 1 on the same side ->
  **0 correct**. LED C2297: subtle and worth a note — JLC numbers the LED's
  *anode* as pin 1 (their symbol says so), so a naive pin-number fit suggests
  180; but their cathode physically sits at -x, same side as KiCad's pad 1, so
  the "read: 0" from the GPiBridge preview is **corroborated by geometry**. The
  BNC's +90 could not be re-derived (their drawing numbers the signal pin 5 vs
  our 1, and the barrel side lives in their silk, not the pads) — it rests on
  the built Lorenz board, which the brief already rates as the best evidence.
- DSIC02 pairing: the vendor drawing's recommended land and construction views
  confirm the poles bridge the two columns (1-4, 2-3), as the footprint and
  `Switch:SW_DIP_x02` assume. Electrically symmetric anyway.
- Economic PCBA + THT: JLCPCB's FAQ says Economic PCBA takes through-hole parts
  (wave or hand soldering, per-part library marking); nothing in the BOM is a
  known Standard-only part type. The cost model's constants ($8.00 setup, $1.50
  stencil, $3.58 THT setup, $3.00/Extended code, $0.0017 SMT and $0.03 THT per
  joint) match JLCPCB's long-standing published Economic rates; I verified the
  arithmetic of all four cost tables (all internally consistent — with the THT
  joint count off by 9/board, Finding 2). "Remove Mark" and the fee constants
  remain the known open items.
- Nothing else stops the line: 14 gerber/drill files, outline exactly
  100 x 100, vias 0.3/0.8 within the free spec, BOM/CPL column layouts as JLCPCB
  expects, QR decodes from the board file, RV1 keyed, the two CPLs differ only in
  the rotation angles (checked by the build).

### 3.7 The documents as a lab handout

- Every loop voltage in the HANDBOOK table matches the simulated operating point
  (TAIL -0.66 -> "-0.7 V", Q6 B -12.95 -> "-13.0 V", Q6 E -13.61 -> "-13.6 V",
  Q2 C 13.91, Q3 E 14.57, Q3 C 0.48 -> "+0.5 V", OUT -0.006 -> "0.0 V",
  rails +/-14.6). The checked ones (8 loops) pass; the unchecked ones (TP1, TP2,
  TP9, TP10 "0.0 V", TP13/TP14 "-0.6 V") also follow from the op point.
- Exercises 1-8 walk through the simulation numbers correctly: stage gains
  11.1 / ~34 (the "about 11"/"about 30" a student measures), CM gain 0.073 ->
  0.0004 ("a hundred times"), dead band ~1.2 V, x11 gain 10.23 ("5 V peak" from
  0.5 V in), compensation demo oscillates exactly where claimed (follower, both
  COMP settings that remove the 1 k; x11 rings but works), offset null and drift
  exercise sound. Exercise 8's "look at TP8 to see that the loop, not the output
  stage, is ringing" is right: the phase margin dies at the loop crossing, not in
  the follower.
- The three documents agree with each other and the board, except the findings
  above (R8 claim, TAIL-both-on, OUT jack label, 14 vs 15 MHz, 5 vs 2 uA, x12 vs
  x30, $7.77 vs $7.78, 18 vs 27 THT joints).
- The 28 checked numbers: listed in `gen_docs.py` (they cover the loop table
  partly, the limit, swing, null range, PMs, costs, counts). Not checked: stage
  gains, the x11's 120 deg PM, the unity crossing, "several V/us" slew, Ibias,
  TP1/2/9/10/13/14 voltages, the switch-truth-table statements. All verified by
  hand/sim above; candidates for new claims rows.
- DESIGN_NOTES section 5 (dead-on-arrival list) gaps: the R8-on-a-ground-clip
  case (Finding 1 — the board is not dead but the doc's catch is wrong),
  supply-overvoltage guidance (Finding 3), the wiper-open failure mode
  (Finding re: null; patch), and the joint-count bug (Finding 2). Its items 1-6
  are otherwise the right list.

### 3.8 What a student will do to it

| mistake | outcome | evidence |
|---|---|---|
| supply reversed / +15 and -15 swapped | nothing happens, no LEDs; D3/D4 block | netlist + pad-verified diode directions |
| one rail only | no damage; just dead | topology |
| 30 V between one rail and ground | C2 or C4 (25 V) overvolted; transistors stay within 40 V for one-sided | Finding 3 |
| 20 V peak generator into one input | clamp at 9.7 mA, 0.09 W per 1206; within the +/-12 V printed limit it's 0.14 W | calculation |
| inputs at opposite rails (worst) | 14.7 mA, 0.215 W per 1206 (rated 0.25 W); off transistor's Veb ~0 V | calculation |
| scope ground clip on TP11/TP12 (rails) | rail collapses through D3/D4; the 50 mA limit does protect here (1 A Schottky anyway) | topology |
| scope clip on Q2 C / Q3 E | **R8 cooks at 0.6 W, 5x rating, under the 50 mA limit** | Finding 1 |
| scope clip on Q6 E / Q6 B | 0.2 W in R7 (0805, 1.7x rating) — warm, survives a while | as documented |
| OUT tied to IN- | the follower — normal use | — |
| OUT tied to IN+ (open loop) | OUT pins at a rail; the limiter caps any resulting short at ~22 mA | sim |
| OUT to ground | 208 mW in Q4/Q5: minutes | sim |
| OUT to a rail | 0.43 W in Q4/Q5: seconds | sim |
| 100 ohm load | limiter clips the swing to ~1.5 V; no damage | limit arithmetic |
| trimmer to an end | offset at most +/-33 mV; gain unchanged | sim + arithmetic |
| trimmer wiper open | OUT parks at -13.5 V, no damage | sim |
| DIP slider half way | switch open: that function is off; nothing damaged | topology |
| both TAIL sliders on | works, tail 2.8 mA, offset beyond null range | Finding 4 |

Nothing on that list is unsafe for the student; the only part-damaging cases are
R8/R7 cooking under a misplaced ground clip (smell first) and a long output
short to a rail (Q4/Q5, seconds). For a first-year lab that is a good record.
What would prevent the R8 case at no cost to clarity: nothing component-free —
the honest fix is the sentence (patched). A 1206 R8 would raise the margin from
5x to 2.6x rating at the cost of one odd footprint.

## 4. Checked and found right

- The full build from a clean copy: one command, under two minutes, byte-identical
  gerbers and silkscreen images, identical results.json (date excepted); ERC 0;
  my own DRC re-run (`--severity-all --schematic-parity`): 0 violations, 0
  unconnected pads; 102/102 circuit assertions; 0 text overlaps on the sheet; all
  fab checks pass (the 37 "missing 3D model" FAILs on this machine are
  environmental — no `3dmodels` directory here; with the AppImage's own libs the
  same check prints "66 3D model(s) resolve on disk").
- The circuit is the book's, value by value, connection by connection (3.1), with
  the four documented additions each verified as circuits (3.2).
- Every number in results.json reproduced by re-running the simulation.
- Phase margins robust to datasheet-floor betas, halved fT, +50% caps, 10 pF
  strays (PM 43-60 deg; 3.3).
- Every CPL rotation re-derived from EasyEDA's current land patterns; the two
  "read" ones consistent (LED explicitly corroborated); the polarised parts'
  cathodes verified pad-by-pad on the built board against the preview
  instructions.
- Silkscreen: dots, hops, transistor symbols, hairlines, legends, ground-symbol
  directions — all read correctly at 600 dpi as a student would (3.4).
- Custom footprints match vendor drawings; DSIC02 pad pairing; 3362P keying;
  SOT-23 pinout vs onsemi.
- Cost-table arithmetic (given the stated fee constants) correct on all four
  quantity tiers, apart from the 9-joint undercount of Finding 2.
- The post-patch items from the previous round verified rather than re-found:
  COMPENSATION pole 2 really is the bare 100 pF alone; the short-to-ground /
  short-to-rail wording is on the board and in the handbook; the ON marks are on
  the board; the input terminals' ground symbols point down.

## 5. Could not check

- **The book itself** (not provided, by design). The values match my knowledge of
  Lab 5L and are internally consistent with the book's quoted currents; I could
  not diff the quotation in DESIGN_NOTES section 1 against the page.
- **A real JLCPCB "Confirm Parts Placement" preview** — the predicted rotations
  are verified geometrically instead; the preview is still the last word (as
  PLACEMENT_CHECKS.txt says).
- **JLCPCB's fee schedule as of today** — the constants match their published
  Economic PCBA rates as of my knowledge, and the arithmetic is right; the order
  page is the authority. (Known open item.)
- **The BNC's +90 geometrically** (their drawing's pin numbering differs from the
  footprint's); rests on the built Lorenz board.
- **Real-silicon phase margin** — simulation only; the docs already expect less
  than the models, and the models say there is margin to spare (3.3).
- **Whether any of the 8 THT parts is flagged non-Economic** in JLCPCB's parts
  library today — the BOM upload will say.

## 6. Publishing

- `out/opamp.net` line 4 embeds the author's absolute home path (Finding 11) —
  the only absolute path in the tree. Harmless but should be scrubbed or the
  file gitignored/regenerated at build time (it is a build product).
- The QR code and silk URL point to a repository that does not resolve yet
  (known); nothing private in them.
- No datasheets, no book text beyond fact-level values, no personal information
  beyond the author's name (intended), no keys.

## 7. Patches

- `review-fixes.patch` — one combined `diff -u` (paths as `a/...`, `b/...`,
  applies with `patch -p1` or `git apply` from the repository root):
  - `scripts/check_circuit.py` — Finding 10 (comment says 47 ohm).
  - `scripts/gen_pcb.py` — Finding 2 (keep duplicate-numbered pads so the THT
    joint count is 27). Py-compiles; regenerate to see MANUFACTURING's counts and
    costs move by the stated amounts.
  - `scripts/gen_sch.py` — Finding 6 (title block: "gain x30 ... (the push-pull's
    dead zone takes stage 2 down to x12)").
  - `docs/HANDBOOK.md` — Findings 1, 3, 4 (the 50 mA rewording, the +/-16 V line,
    the both-TAIL-on sentence, the symptom-table row).
  - `docs/DESIGN_NOTES.md` — Finding 9 (15 MHz) and the wiper-open caveat (3.2).
- `patched/` holds the full patched files the diff was made from.
- Supporting evidence in this directory: `sim_baseline.txt`, `sim_extra.py` /
  `sim_extra.txt`, `sim_models.py` / `sim_models.txt`, `count_joints.py`,
  `dump_diodes.py` (pad-level orientation dump), `drc-full.rpt`,
  `board600.png` + `z_*.png` (my 600 dpi render and crops of the current board),
  `dsic02*.png` (the vendor drawing), `project/` (the built copy).
