# Design review: Discrete Transistor Op-Amp, rev A

Reviewer: Claude Fable 5.1 (the model that generated the board), 2026-10-24/25, following
`design_reviews/DESIGN_REVIEW_PROMPT.md`, before reading any other review. Everything
here was run or re-derived in this directory: `sim_review.py` / `sim_review2.py` and
their logs, the land-pattern fetch `easyeda_landpatterns.log`, the 600 dpi silkscreen
crops `z_*.png` (as built) and `zp_*.png` (with the patch), `build.log` (the unmodified
copy) and `build_patched.log`, and the patch `patch_round1.diff` with `apply_patch.py`.
Nothing outside this directory was touched.

## 1. Verdict

**Order after named fixes.** The circuit is the book's and the copper is the
silkscreen: the netlist, the rebuild (byte-identical to the committed files except the
STEP and the raytrace), the land patterns and the rotations all check. But the board
would teach one thing wrong and promise one thing it cannot keep: the COMPENSATION
switch's position 2 on its own is *no* compensation, not the book's bare 100 pF that
the back of the board, the sheet and the handbook all say (finding 1); and "a short to
a rail is survived" is false for the transistor JLCPCB stocks (0.43 W in a part rated
0.2 W, finding 2). Both are cheap: one wire on the board and the sheet, and words. With
findings 1 to 3 applied (the patch in section 7 does all three and the smaller ones,
and builds clean: ERC 0, DRC 0, 102 circuit assertions, 28 of 28 claims), I would
order. Confidence: high on the findings, which rest on the netlist, the simulation and
the datasheets; moderate on the real board's stability margin, which no simulation
settles.

## 2. Findings

| # | severity | where | one line |
|---|---|---|---|
| 1 | **major** | SW2 wiring: `scripts/gen_sch.py`, `scripts/layout.py`; the back silk, the sheet note, `docs/HANDBOOK.md` sections 4, 7, 8 | COMPENSATION 2 alone is an open circuit, not the bare 100 pF; the bare capacitor needs both sliders on, which nothing says |
| 2 | **major** | `docs/HANDBOOK.md` section 3, the back silk, `docs/DESIGN_NOTES.md` section 5.4 | "A short to a rail is survived": 0.43 W in Q4 or Q5, whose stocked part (C20526) is rated 0.2 W at 625 K/W; to ground it is 0.21 W, the whole rating |
| 3 | **major** | `docs/HANDBOOK.md` sections 2 and 10, the back silk | A scope's ground clip on Q2 C or Q3 E puts 0.55 to 0.68 W into the 0805 R8; nothing tells the student to keep the supply current-limited after bring-up |
| 4 | minor | DIP switches: `docs/HANDBOOK.md` section 4, `scripts/gen_docs.py PREVIEW_CHECKS`, the silk | "On is toward the number" is not true as drawn (SW1's ON side is away from its legends) and cannot be checked in JLCPCB's preview; the silk has no ON mark |
| 5 | minor | `docs/DESIGN_NOTES.md` sections 5.3 and 6 | Cable capacitance on OUT does not destabilise the follower in the model (100 pF raises the margin to 90 degrees); the rev B "47 ohm in series" item is moot, and probe loading is the real margin eater |
| 6 | minor | the documents, the sheet, `scripts/parts.py`, `scripts/check_circuit.py` | Numbers and counts that disagree with each other or the board: six vs eight transistors (four places), 55 vs 51 degrees, null range 33 / 37 / 19 mV, input-resistor power 0.14 / 0.2 W, stage-2 gain 12.5 vs 34, "no fiducials" vs three, "2.54 mm pins" vs loops |
| 7 | minor | `docs/HANDBOOK.md` sections 1, 3, 9; the back silk | The output figures: "22 mA" is the dead-short total, Q4 carries 14.5 mA; "+/-13 V into 1 k, 20 mA" is +/-12 V and 15 mA |
| 8 | nit | silk near TP5 | The "Q6 B" label sits on R5's ground symbol and reads as "Q6 B is grounded" |
| 9 | nit | silk at J4 and J5 | The ground symbols beside the input terminals' GND pins point sideways; the rule is down (except the -15 V side) |
| 10 | nit | `docs/MANUFACTURING.md` order form | "Remove Mark" may carry a fee; "Order Number (Specify Position)" with `JLCJLCJLCJLC` on the back silk is free and keeps the front clean |
| 11 | nit | `scripts/gen_docs.py` fees | The THT per-joint rate (0.03) is about twice JLCPCB's help page (0.0157); the Extended feeder fee may have dropped from $3 to $1.50; totals move by a few dollars either way |

### Finding 1: COMPENSATION 2 alone is no compensation (major)

**Where.** `out/opamp.net`: `Net-(R14-Pad1) = R14.1 SW2.1 SW2.2`, `Net-(C1-Pad1) = C1.1
R14.2 SW2.3`, `/Q2 C` has `SW2.4`. Pole 1 (pins 1-4) connects Q2 C to R14; pole 2
(pins 2-3) shorts R14. The chain Q2 C -> pole 1 -> R14 -> C1 -> Q3 C is open whenever
pole 1 is off, whatever pole 2 does.

**What is wrong.** The back of the board says "COMPENSATION 2 shorts the 1k: the book's
bare 100 pF; the x11 amp still works, a follower rings". The sheet note says "2 ON:
shorts the 1k, leaving the bare 100 pF". `HANDBOOK.md` section 4's table has "2 on:
shorts the 1 k: the book's bare 100 pF", section 7 step 9 says "COMPENSATION 2 as a
follower: the square wave's edges ring, which is the book's point", and exercise 8 says
"COMPENSATION 2, then both off", as if they differed. With 2 alone there is no
capacitor in the loop at all: the student sees the uncompensated amplifier twice and
never sees the book's bare-Miller case, which is the point of the exercise. The
assertion in `check_circuit.py`, "SW2 pole 2 shorts R14", is true and still let this
through: it checks the wiring, not what a position does on its own.

**Evidence.** `sim_review.log` section 5: with no compensation the follower's phase
margin is -39 degrees and the x11 amplifier's is +18 degrees, with a 54 % overshoot and
1.65 V peak-to-peak still ringing 60 us after a 0.1 V step (the x11 amplifier with the
bare 100 pF has 106 degrees and is fine). `HANDBOOK.md` section 4 also says "Both
COMPENSATION sliders on is the same as 2 alone", which is false as wired (both on is
the bare capacitor; 2 alone is nothing).

**Fix** (in the patch, F1). Move pole 2's input from the R14 node to Q2 C: on the
sheet, SW2 pin 3 goes up to the Q2 C line and pin 2 down to the R14 / C1 junction; on
the board, the Q2 C drop forks at (53.5, 37.5) into both top pads and the lower
right-hand pad runs down the switch's right side to the junction below R14. Then 1 =
100 pF + 1 k, 2 = the bare 100 pF, both = the bare 100 pF, as every legend already
says. `check_circuit.py` now asserts "SW2 pole 2 takes Q2 C straight to C1, bypassing
R14". The patched build is clean (`build_patched.log`), and `zp_sw2.png` and
`zp_sch_sw2.png` show the result. The alternative, keeping the wiring and rewriting the
legends to "2 alone does nothing; 1 and 2 together is the bare 100 pF", is worse for
the student.

**Confidence.** Certain: it is in the netlist.

### Finding 2: a short to a rail is not survived (major)

**Where.** `HANDBOOK.md` section 3: "The output limits itself at about 22 mA, so a
short to ground or to a rail is survived (the transistor runs hot: do not leave it)";
the back silk: "a short to ground or a rail is survived, not enjoyed"; the sheet's
OUTPUT note; `DESIGN_NOTES.md` section 5.4: "22 mA with 15 V across it, 0.3 W".

**Evidence.** `sim_review.log` section 7. The limit holds the sense resistor's current
at 0.65 V / 47 ohm: Q4 carries 14.5 mA into a short to ground (Q5 14.0 mA the other
way); the 21.8 mA the project quotes is the total reaching the short, the rest coming
through the sense transistor Q7 from the drive node. Powers: short to ground, 208 mW in
Q4 (201 mW in Q5); short to the far rail (OUT held at -15 V while the loop asks for
more, or at +15 V), 431 mW in Q4 or 423 mW in Q5 with 29 V across it. The transistor
JLCPCB stocks for C20526 (its datasheet, `datasheets/MMBT3904_RANGE_100-300__C20526.pdf`)
is rated 200 mW collector dissipation and 625 K/W junction to ambient; onsemi's
MMBT3904 is 350 mW and 357 K/W. So a short to ground runs the stocked part at its full
rating (a 130 K rise: survivable for minutes, not an afternoon), and a short to either
rail is twice the rating and a 270 K rise: seconds. The limiter does its job for the
case students produce most (OUT to ground, or an 8 ohm speaker), not for a rail.

**Fix** (in the patch, F4): say so. Handbook section 3 and the back silk now read "a
short to ground is survived, to a rail only for seconds"; `DESIGN_NOTES.md` 5.4 carries
the numbers. If rail-short survival is wanted, 100 ohm sense resistors give 6.5 mA
(190 mW into a rail, under the rating) at the price of +/-6.5 V into 1 k; or specify
onsemi's part. I would not: the book's loads are 11 k and up, and the words are enough.

**Confidence.** High: operating-point simulation and the two datasheets.

### Finding 3: a ground clip on the wrong loop burns R8; the supply limit is not a rule (major)

**Where.** `HANDBOOK.md` section 2 ("A current-limited bench supply at 30 mA is the
right thing for a new board") and section 7 step 3 are the only mentions; nothing on
the board.

**Evidence.** `sim_review2.log` section B: a scope's ground clip shorts the node it is
on to ground. On TP6 (Q2 C): Q3's base goes to ground, Q3 saturates, R8 (330 ohm, 0805,
rated 0.125 W) takes 545 mW and R3 150 mW; the +15 V rail draws 52 mA. On TP7 (Q3 E):
R8 takes 682 mW and Q3 678 mW; 47 mA. On TP4 or TP5: R7 takes 200 to 225 mW from the
-15 V rail. Students put the ground clip on the wrong thing; these loops are 4 mm from
the ground loops. A 50 mA limit on the bench supply ends the two R8 cases (the rail
sags before R8 cooks) and costs nothing; the R7 cases (15 mA) it does not catch, and R7
at twice its rating for a minute discolours rather than opens.

**Fix** (in the patch, F3): make the limit the rule, not a bring-up step: handbook
section 2 ("Set the bench supply's current limit to 50 mA, always"), a new row in
section 10 ("a resistor smells hot"), and the back silk's POWER line ("set the supply's
limit to 50 mA"). Bring-up keeps 30 mA, which is a better fault detector.

**Confidence.** High on the numbers; the teaching-lab judgment is the author's.

### Finding 4: the DIP switches' ON side is unmarked and mis-described (minor)

**Where.** `HANDBOOK.md` section 4: "'On' is toward the number". `gen_docs.py
PREVIEW_CHECKS` and the assembler notes: "sliders move toward the '1 / 2' legends".

**Evidence.** The footprint `SW_DIP_SPSTx02_KingTek_DSIC02_P2.54mm` puts ON toward +x
(pads 3 / 4), the usual convention and the one the DSIC02 drawing's top view supports
(ON at the pad row opposite the numbers). SW1 is placed at 180 degrees, so its ON side
is the left, and its legends "1: current source Q6 / 2: 10k" are on the right
(`z_sw1.png`); SW2 at 90 degrees has ON upward with its legend to the right; SW3 at 0
has ON to the right with its legends below. No digit sits on an ON side. The physical
ON direction of the placed part is set by the CPL angle (+270 predicted from the
Lorenz board's DSIC06), so only the preview can confirm it, and the preview check as
written has nothing to compare against.

**Fix** (in the patch, F2): a silkscreen "ON" at each switch's ON side (left of SW1,
above SW2, and "ON>" above SW3's right-hand pads where the box edge leaves no room
beside them), the handbook's sentence changed to "toward the word ON", and the preview
check changed to "the part's own ON marking on the side of the silkscreen ON". If the
preview shows the part's ON the other way, turn the CPL angle by 180 for C54949; it is
electrically indifferent.

**Confidence.** High that the documents are wrong as written; the footprint's ON
convention is the usual one but is unverified for this part until the preview.

### Finding 5: the cable-capacitance story is the wrong way round (minor)

**Where.** `DESIGN_NOTES.md` 5.3 ("Oscillation at a few MHz when a long unterminated
cable hangs on OUT ... Rev B puts 47 ohm in series with the OUT jack") and 6.

**Evidence.** `sim_review.log` section 3: with the 47 ohm sense resistors already
between the emitters and OUT, 100 pF on OUT moves the unity-gain crossing from 15 MHz
to 2 MHz and the phase margin from 51 to 90 degrees (6 % overshoot on a step); 1 nF
gives 51 degrees, 10 nF 30 degrees and 18 % overshoot. Without the 47 ohm it is nearly
the same (89 degrees at 100 pF). The rev B item was written before the limiter put the
47 ohm in, and the model never supported it. What does eat margin is a 10x probe on the
high-impedance nodes (section 2): 15 pF on TP8 (Q3 C) gives 39 degrees, on TP6 (Q2 C)
35, both at once 25. All still stable, with no overshoot on a 0.5 V step, but the real
board starts below the model.

**Fix** (in the patch, F5): 5.3 rewritten around probe loading; the 47 ohm item struck.

**Confidence.** High within the model; the model's 15 MHz crossing is optimistic, as
the notes say.

### Finding 6: numbers and counts that disagree (minor)

| what | where | says | should say |
|---|---|---|---|
| transistor count | `DESIGN_NOTES.md` 5.1, `HANDBOOK.md` 7.1, `parts.py` D3 note (so `MANUFACTURING.md`), the sheet's header note | six | eight (Q7, Q8 added with the limiter) |
| follower phase margin | `DESIGN_NOTES.md` 5.3, `HANDBOOK.md` 9L.3 row | 55 degrees | 51 (the checked sentence in 3 already says 51) |
| null range | `parts.py` RV1 note, `check_circuit.py` message | +/-37 mV, +/-19 mV | +/-33 mV (simulated: -37.5 to +28.8 mV about -5.6) |
| input-resistor power | `DESIGN_NOTES.md` 2, `parts.py`, `check_circuit.py` | 0.14 W, 0.2 W "when an input is held at a rail" | 51 mW each with one input at a rail and the other grounded (7.2 mA through both 1 k and the clamp); 214 mW each only with the two inputs at opposite rails |
| stage-2 gain | `DESIGN_NOTES.md` 3 | "stage 2 gives 12.5 at Q3 C loaded as it is" | 34 at Q3 C (`sim_review2.log` A: 375 / 11.1); the 12.4 is stage 2 times the push-pull's 0.37 small-signal gain at rest (the dead band). `HANDBOOK.md` exercise 4's "about 30" is right |
| fiducials | `MANUFACTURING.md` order form | "the board carries no fiducials" | three 1 mm copper dots in 2 mm mask openings at (11, 7), (89, 7), (11, 92) are in the board file |
| probe loops | the sheet's PROBING note | "A 2.54 mm pin on every node ... Three pairs of ground pins" | wire loops; four ground loops |
| box name | `HANDBOOK.md` section 1 table | PUSH-PULL FOLLOWER x1 | PUSH-PULL FOLLOWER (the "x1" was dropped from the silk) |

None of these is covered by the 28 document claims, which check voltages, gains and
joint counts. **Fix** (in the patch, F6): the texts; and I would add claims for the
transistor count and the phase margin wherever they are quoted.

### Finding 7: the output figures (minor)

"It limits at about 22 mA" (`HANDBOOK.md` 1) is the dead-short total; "+/-13 V into 1 k
or more, 20 mA" (section 3's table, section 9's table, the back silk) overstates:
`sim_review.log` section 11 has +/-10.6 V into 1 k for 1 V peak in and +12.6 / -11.7 V
when 1.3 V is asked, the limiter clipping before the rails; into 330 ohm, +5.3 / -4.6 V
(16 / 14 mA). **Fix** (patch F4): "+/-12 V into 1 k, 15 mA (22 mA into a dead short)".

### Finding 8: "Q6 B" over a ground symbol (nit)

`docs/history/2026-10-24-r4-q6.png`, `z_tail.png`: TP5's label "Q6 B" sits directly
above the ground symbol that R5's lower end runs to, and 2 mm from R6's label. A
first-year reader can take Q6 B as grounded. Move the label to the left of the loop or
move R5's ground stub. Not patched.

### Finding 9: sideways ground symbols at the input terminals (nit)

`z_inputs.png`: the GND symbol beside J4's upper pin is drawn pointing to the right (a
horizontal stem, bars decreasing rightwards); J5's is the same. The author's own rule,
quoted in the brief, is that grounds point down except on the -15 V side. The
terminals' other ground symbols (J6, J7) point down. Check `layout.py GND_MARKS` /
the terminal ground symbol rotation. Not patched.

### Findings 10 and 11: order-form details (nits)

JLCPCB's help pages (fetched 2026-10-24) say the order number can be placed where a
`JLCJLCJLCJLC` silk text sits, at no charge, with "Order Number (Specify Position)";
removing it altogether is described as costing extra, amount not stated. The back has
room under the text block. The assembly-fee page lists Economic setup $8.00, stencil
$1.50, SMT $0.0016 to $0.0017 a joint, feeder loading $3.00 per Extended part, and
hand-soldering $3.50 an order plus $0.0157 a joint; `gen_docs.py` uses 0.0017, $3.58 and
0.03. A third-party page claims the Extended fee fell to about $1.50 on 2025-12-19; I
could not confirm it on JLCPCB's own pages. The quote tool is the arbiter; the
estimates here are within a few dollars and on the safe side.

## 3. The brief's questions, by number

1. **The circuit against the book.** Every net printed from `out/opamp.net`
   (`sim_review` was built from the same netlist) matches `DESIGN_NOTES.md` section 1
   and my memory of Figs. 5L.10 and 5L.15: Q1's collector straight to +15 V, R3 1.5 k on
   Q2's collector, Q3 (PNP) with its emitter through 330 ohm to +15 V and collector
   through 12 k to -15 V, base from Q2 C; the Miller capacitor from Q3 C back to Q2 C;
   Q4 / Q5 bases on Q3 C, collectors to the rails, emitters to OUT through the 47 ohm;
   R10 / R11 from OUT to X to ground; Q6 with 62 k to ground and 10 k to -15 V at its
   base and 1 k in its emitter; R4 10 k as the alternative tail. The sense is right: IN+
   rising turns Q2 on, Q2 C falls, Q3 conducts more, Q3 C rises, OUT rises. Q3 is
   drawn the right way up for a PNP (emitter up to the 330 ohm, arrow into the bar,
   collector down). What `check_circuit.py` did not assert: Q7 and Q8's types (the
   patch adds them: 102 assertions), and what each switch position does *on its own*
   (finding 1). It asserts no polarity for D1 / D2 beyond "back to back", which the
   netlist shows is right.
2. **The additions.** Null: +/-33 mV (pot 0: -37.5 mV, pot 1: +28.8 mV, centre
   -5.6 mV); open-loop gain changes from 138 to 246 across the travel because the
   degeneration moves to one side; a lifted wiper opens the tail and the pair stops,
   harmlessly; shorted ends make 0 ohm per emitter and a gain of 20, harmlessly.
   Input protection: one input at +/-15 V with the other grounded gives 7.2 mA through
   both 1 k and the clamp, 51 mW each, the off transistor's base-emitter reverse
   voltage 0.02 V; +15 V and -15 V on the two inputs gives 14.6 mA and 214 mW each (the
   1206's rating is 250 mW); +/-20 V with the other grounded 9.7 mA, 93 mW. The clamp
   conducts above 0.7 V of difference, which is only in open loop (exercises 2 to 5,
   the comparator of Lab 8L): by design, and the handbook says so. R14: with the 330 ohm
   degeneration Q3's effective transconductance is about 1 / 351 S, so the bare
   capacitor's right-half-plane zero is at 4.5 MHz, below the 15 MHz crossing; with
   1 k (more than 1 / gm) it moves to the left half plane at 2.45 MHz, which is the
   checker's figure; the model goes from -43 to +51 degrees. The limiter: see finding 2
   for the currents and powers; it costs 4 degrees of margin (55 to 51) and nothing in
   gain; D5 / D6 polarity is right in the netlist (D5 anode on Q3 C, cathode on Q7's
   collector; D6 cathode on Q3 C, anode on Q8's collector). D3 / D4: anode of D3 on the
   terminal, cathode on the rail; D4 anode on the -15 V rail, cathode on the terminal:
   right, 0.4 V drop at 4 mA (the 14.6 V rails). Both supplies reversed: both diodes
   block, the board floats, nothing lit, nothing hurt. One rail missing: the other
   rail's circuits sit against ground, no damage. GND swapped with a rail: 30 V across
   C2 or C4 (25 V X5R parts), outside their rating though not a failure in minutes;
   the transistors see 30 V, under their 40 V. LEDs 1.2 mA each.
3. **Stability.** Models against onsemi: Cjc 4 / 4.5 pF matches Cob 4 pF max; TF 350 ps
   is fT about 450 MHz against 300 MHz minimum; Bf 300 against a stocked part binned
   100 to 300, so the input bias current is 2 to 7 uA, not the handbook's "about 2 uA".
   Probes: 15 pF on TP8 39 degrees, on TP6 35, both 25, on TP9 (OUT) 63, on TP7 77;
   with the bare capacitor every case is negative (the book's point survives probing).
   Follower steps with a probe on TP8 or TP6: no overshoot at 0.5 V. Cable on OUT:
   finding 5. Both FEEDBACK on: a follower into 1 k, OUT -3 mV, 97 degrees. The x11
   amplifier with 2 V peak in: the project's -14.3 / +13.4 V into 11 k; with 1 V peak
   into 1 k, +/-10.6 V. Slew rate 4.4 V/us both ways (the handbook's "several V/us").
   The dead band shows at TP8 as the handbook says.
4. **The silkscreen as a schematic.** Read in the r4 close-ups and my 600 dpi crops:
   every three-way node has a dot, every crossing an arc with its two vias; the
   transistor symbols put B, C and E on the pads the netlist says, the arrow on the
   emitter, out for NPN and in for PNP; the hairlines run where the copper runs. Box
   names, switch legends and loop names match the handbook except the COMPENSATION
   semantics (finding 1). Found: the ON marks (finding 4), "Q6 B" (8), the sideways
   grounds (9). SW2's lower pads' wires are hidden by the courtyard clipping and
   emerge below the switch; the patch's fork above the switch makes both top pads'
   connection visible.
5. **Copper and board.** Parity DRC 0 means every pad is on its net and every net
   complete. The rebuild in `project/` is byte-identical to the committed board,
   schematic, gerbers, CSVs and documents (only the STEP, which carries a timestamp,
   and the raytraced render differ). SOT-23: KiCad's footprint has pads 1 and 2 on one
   side, 3 alone; the stocked part's datasheet has 1 = base, 2 = emitter, 3 = collector;
   at rotation 90 the lone pad is up with base lower-left and emitter lower-right, at
   270 the mirror, which is what the symbols draw and `PLACEMENT_CHECKS.txt` says.
   The three fiducials are in the board file (1 mm copper, 2 mm mask). Hops: eight,
   32 vias. The custom footprints against JLCPCB's own land patterns
   (`easyeda_landpatterns.log`): BNC centre pin and four posts on 8 x 8 mm (theirs
   1.4 mm drills, ours 1.4; centre 1.2 vs our 1.3), KF301 2P / 3P pads at +/-2.5 and
   -5 / 0 / +5 with 1.4 mm drills, RH-5019 one 4.0 x 2.2 pad, 3362P pins at (+/-2.5,
   1.25) and (0, -1.25), DSIC02 four 1.1 x 2.2 pads 9.0 mm across (ours 2.4 x 1.5 at
   8.8), SOD-123 and SOD-123F pads at +/-1.7 (ours +/-1.65): all compatible.
6. **The JLCPCB package.** The upload CPL's angles are the KiCad angles plus the table
   (Q1 90 -> 270, Q2 -90 -> 90, SW1 180 -> 90, SW2 90 -> 0, SW3 0 -> 270, BNCs +90) and
   its Y is mirrored to JLCPCB's convention. The corrections agree with the land
   patterns: JLCPCB's SOT-23 is KiCad's turned 180 (pad 1 at (+1.0, +0.95) against
   (-0.94, -0.95)); their DSIC02 has its rows along y, 9 mm apart, so KiCad's must turn
   by -90 (+270) to land pad 1 on pad 1, which is the table's value; their 0805 LED has
   pad 2 on the left where KiCad's cathode pad 1 is, which with JLCPCB's "pin 2 =
   cathode" convention (read on the GPiBridge preview) is 0, as the table says. The
   DSIC02 drawing's schematic shows each pole across the body, as the footprint
   assumes (pads 1-4 one row, 2-3 the other). JLCPCB's capabilities page lists
   Economic PCBA as single-sided SMT, through-hole and mixed, 2 to 50 pieces, so the
   eight through-hole parts are fine on Economic. Fees: finding 11. Polarised parts:
   D1 / D2 anti-parallel, D3 / D4, D5 / D6 and the LEDs are right in the netlist and the
   assembler notes say which end is the cathode.
7. **The documents as a handout.** Every voltage in the loop table matches
   `sim/results.json` to the rounding shown. Exercise 4's "about 30" is right (finding
   6 corrects the design notes, not the handbook). Exercise 8 and bring-up step 9 are
   wrong as wired (finding 1). The DOA list misses: the switch semantics (not dead, but
   a wrong lesson), the ground-clip hazard (finding 3), and the stocked transistor's
   lower rating (finding 2). The 28 claims do not cover the items in finding 6.
8. **What a student will do to it.**
   - supply reversed, or +15 / -15 swapped: the Schottkys block, nothing lights,
     nothing hurt;
   - one rail only: works badly, no damage;
   - GND swapped with a rail: 30 V across a 25 V bypass capacitor; no transistor over
     its 40 V; rare, accept;
   - 20 V peak generator into an input: 9.7 mA, 93 mW in the 1 k, no junction reversed;
   - a ground clip on a signal loop: finding 3 (R8 at 0.55 to 0.68 W on TP6 / TP7,
     R7 at 0.2 W on TP4 / TP5, nothing elsewhere; TP11 shorts the +15 V rail, which
     the supply limit must handle: D3 is a 1 A part);
   - OUT tied to an input: 7 mA through the input resistor, the clamp holds the pair;
   - OUT to ground: 0.21 W in Q4 or Q5, at the stocked part's rating (finding 2);
   - OUT to a rail: 0.43 W, twice it (finding 2);
   - a 100 ohm load: +/-2 V, 177 mW in Q4 or Q5, fine;
   - the trimmer at an end: +/-33 mV of offset, gain 20 on one side, harmless;
   - a DIP slider half way: open; the switch is a make contact.
   The one no-cost protection is the 50 mA supply limit written on the board.

## 4. Checked and found right

- The netlist is the book's circuit with the stated additions; `check_circuit.py`'s 98
  assertions pass and the four added ones do too.
- The build is reproducible and deterministic from a clean copy in 21 s.
- ERC 0, DRC 0 at every severity with parity, including the silkscreen rules.
- SOT-23 pin order against the stocked part's datasheet; footprint pad geometry and
  the package rotations against the symbols and the preview notes.
- The JLCPCB corrections for every code against JLCPCB's own land patterns; the LED
  convention against the earlier read.
- All custom footprints against JLCPCB's land patterns (pad positions and drills).
- Polarity of every diode and LED in the netlist.
- The loop voltages in the handbook against the simulation; the stage gains (11.1,
  34, 0.37 at rest, 355 with the output in conduction); the x11 gain of 10.2 at small
  signals; the common-mode gains.
- The null range (33 mV), the input-protection currents and powers, the limiter's
  currents, the slew rate, the swing into 1 k.
- Probe loading and cable loading leave the follower stable in the model.
- Economic PCBA assembles through-hole parts; the BOM has 40 lines with codes, the CPL
  matches it, the gerbers have every layer, the QR decodes.
- No absolute paths, e-mail addresses or keys in tracked files (`git grep`).

## 5. Could not check

- The physical ON direction of the DSIC02 as JLCPCB places it, and whether JLCPCB's
  drawing of C54949 has ON toward its pads 3 / 4: only the preview shows it. The silk
  ON marks in the patch make that preview check possible.
- The BNC, terminal and trimmer footprints against parts in hand; only against JLCPCB's
  land patterns and the Lorenz board's read of the BNC.
- The real transistors' beta and fT, so the real phase margin; the model says 51
  degrees and I believe less.
- JLCPCB's fees as of today, beyond their help pages.
- The repository URL and QR code resolve only once the repository is pushed.
- The book's figures directly: the book is not provided; I checked the circuit against
  `DESIGN_NOTES.md` section 1 and what I remember of Lab 5L.

## 6. Publishing

Tracked files carry no absolute paths, e-mail addresses or keys (`git grep -n
"/home/\|jason@\|hmc.edu"` over the tree outside `design_reviews/` is empty, and the
chat log has no absolute paths). This directory holds no datasheet excerpts: the renders
I made of the DSIC02 drawing while checking its ON side were deleted before this report
was finished. The project copy in `project/` is gitignored.

## 7. Patches

- `patch_round1.diff`: `diff -u` of the nine source files against the originals,
  produced from `project/` after `./make.py` there passed (ERC 0, 102 circuit checks,
  no sheet overlaps, DRC 0, fab checks, 28 of 28 claims; `build_patched.log`). It
  contains F1 (SW2 pole 2 to Q2 C, on the sheet and the board, the checker, the back
  silk, the sheet note, the handbook), F2 (silk ON marks, handbook sentence, preview
  check, assembler note), F3 (the 50 mA rule in the handbook and on the back), F4 (the
  limiter's numbers and the rail-short wording), F5 (the cable-capacitance story and the
  rev B item), F6 (the stale counts and numbers, the fiducial row, the sheet notes,
  Q7 / Q8 in the checker, README's assertion count).
- `apply_patch.py`: the same edits as exact replacements, the form I applied them in.
- Not patched: findings 8, 9, 10, 11, and the optional 100 ohm sense resistors.
- Regenerated by the build in the copy and therefore not in the diff: the board and
  sheet files, the gerbers, the assembly notes, `PLACEMENT_CHECKS.txt`,
  `docs/MANUFACTURING.md`, `docs/images/`.
- Renders of the patched board: `zp_sw1.png`, `zp_sw2.png`, `zp_sw3.png`,
  `zp_sch_sw2.png`; of the board as built: `z_inputs.png`, `z_tail.png`, `z_sw1.png`,
  `z_sw2.png`, `crop_*.png`.
