# Design notes

What was decided, what the simulation says, what could be wrong with a first
board, and what rev B should change.  The numbers quoted from the build are
checked against it by `scripts/gen_docs.py` on every build.

## 1. The book's circuit, kept

Lab 5L of *Learning the Art of Electronics* builds an op-amp in three stages and
the board keeps every value the book uses:

| stage | the book | the board |
|---|---|---|
| difference amplifier | 2N3904 pair, 1.5 k collector load on one side | Q1, Q2 (MMBT3904), R3 1.5 k |
| tail | 10 k to -15 V, then the "simple current sink" of Fig. 5L.10: 62 k / 10 k divider, 1 k emitter | R4 10 k; Q6, R5 62 k, R6 10 k, R7 1 k; chosen by SW1 |
| gain stage | 2N3906 common emitter, 330 ohm emitter, 12 k collector | Q3 (MMBT3906), R8 330 (a 1 W 2512), R9 12 k |
| compensation | 100 pF from collector to base of the gain stage | C1 100 pF C0G |
| output | 2N3904 / 2N3906 push-pull follower | Q4, Q5 |
| load and feedback | 10 k / 1 k divider, tap to IN- for a gain of 11 | R10, R11; SW3 pole 1 |

The transistors are the SOT-23 versions of the book's 2N3904 and 2N3906 so each
is a separate part on the silkscreen schematic, at the centre of its own symbol:
the base bar, the collector and emitter leads at 45 degrees with the arrow on the
emitter, B, C and E lettered inside the circle, and a hairline from each pad to
its lead (the copper follows the hairline) so the package is visibly the
symbol's transistor.

## 2. What the board adds, and why

| addition | parts | why |
|---|---|---|
| offset null | RV1, 50 ohm between the emitters, wiper to the tail | a discrete pair has millivolts of offset; a trimmer whose ends are the two emitter resistors (25 ohm each at centre) is the textbook null and costs one part.  Its wiper feeds the tail sink, a high-impedance collector, so wiper contact resistance only eats compliance and cannot unbalance the pair.  A wiper that lifts off entirely opens the tail and parks OUT at the negative rail: no damage, and the classic trimmer failure to look for |
| series 1 k with the Miller capacitor | R14 | the book's bare 100 pF puts a right-half-plane zero at 1 / (2 pi C / gm): the follower is unstable with it.  1 k in series moves the zero to the left half plane.  SW2 pole 2 shorts it so the book's version can be shown ringing |
| three 2-way DIP switches | SW1 TAIL, SW2 COMPENSATION, SW3 FEEDBACK | the book's variants (resistor tail or current sink; compensation or not; x11, follower or your own) without jumpers to lose |
| input protection | R1, R2 1 k 1206; D1, D2 1N4148W anti-parallel between the bases | a real op-amp's input clamps.  A 2N3904's base-emitter junction breaks down at 6 V reverse; a student with a 10 V generator on one input and the other grounded would otherwise degrade Q1 or Q2.  The 1206 resistors take 50 mW each with one input at a rail and the other grounded, 0.21 W each with the two inputs at opposite rails |
| output protection | R17, 330 ohm 2512, from the push-pull's joined emitters to OUT, inside the loop | students will short OUT in Lab 6; the '411 shrugs, and the book's bare push-pull would put more than 1 W into Q5.  One resistor does it: into a short at the jacks the current is about 46 mA and Q4 or Q5 dissipate at most 127 mW (rated 200 mW); R17 takes 0.7 W of its 1 W.  The feedback is taken at OUT, after R17, so the loop hides the drop: the gain, the offset and the output resistance are what the loop makes them, and the only cost is swing into heavy loads (+/-10 V into 1 k instead of +/-12 V).  330 ohm is the smallest value with margin: 270 puts 167 mW in Q4/Q5 at 25 C, 220 puts 220 mW.  It is also the isolation resistor between the push-pull and a cable: 100 pF to 2.2 nF on the jacks leaves the follower clean at any level.  It replaced, before rev A was ordered, a 741-style limiter (two sense transistors, two sense resistors, two diodes): the same protection for one part instead of six, and an output stage that is exactly the book's.  No probe loop sits between the push-pull and R17, so no ground clip can short it |
| reverse-supply protection | D3, D4 B5819W in series with each rail | a reversed bench supply forward-biases every junction on the board; the 0.17 V drop at 4 mA costs nothing here |
| resistors that survive a misplaced clip | R8 1 W 2512, R7 0.25 W 1206 | a scope's ground clip on Q3 E puts the whole rail across R8, 0.66 W at 45 mA, under any sensible supply limit; on Q2 C 0.5 W.  On Q6 E or Q6 B, 0.21 W in R7.  An 0805 would cook; these are inside their ratings.  The 2512 is the board's one Extended part added for safety, and a student who asks why that resistor is so big has asked the right question |
| rail LEDs | LED1, LED2 through 10 k | rails at a glance, 1.2 mA each |
| bypass | C2, C4 10 uF; C3, C5 100 nF | long bench leads |
| probe loops | TP1 - TP14, TP100 - TP103 | one per node the book asks you to look at, X included, plus four grounds for the clip, one per scope channel |
| BNCs and screw terminals | J1 - J7 | BNCs for the generator and the scope; terminals for the feedback network a student wires and for a bench supply |

## 3. What the simulation says

`sim/opamp_sim.py` runs ngspice on the netlist as built, with generic 2N3904 /
2N3906 models (Bf 300 / 200, VAF 100, Cjc 4 - 4.5 pF), 3 pF of stray at the
three high-impedance nodes, and the rails fed through D3 and D4 (a B5819W model
fitted to its datasheet curve) from a +/-15 V supply, bypassed as on the board.  The results in `sim/results.json` feed the schematic
notes, the handbook and this file.

**Operating point** (follower, IN+ grounded): rails at +/-14.8 V, tail current
of 1.36 mA through Q6, 1.28 mA in Q3, Q2 C at +13.8 V, Q3 C at +0.5 V, OUT at
-0.007 V.  The output current into a dead short is about 46 mA, set by R17,
with at most 127 mW in Q4 or Q5 (the worst case over every output level the loop
might be asking for).  Into 1 k OUT swings +/-10.1 V.  The follower's own offset with everything nominal is -6.7 mV, from
Q1's collector sitting at the rail while Q2's sits 1 V below it (Early effect);
the null range of about +/-33 mV covers it and the pair's real mismatch several
times over.

**Gain.** Stage 1 gives 11.4 at Q2 C, stage 2 gives 32 at Q3 C, and the
push-pull at rest is barely conducting (its small-signal gain at the quiescent
point is about a third, the dead band), so the small-signal open-loop gain at
the quiescent point of about 126 is what a student measuring tiny signals
around zero will see; it moves a lot with where in the dead band the output
rests.  Once the output moves and Q4 or Q5 is on, the follower's
gain goes to 1 and the loop gain is several hundred.  Consequently the x11
amplifier really has a gain of 10.1: the finite-gain error the book has
students compute.

**Stability.** With the 100 pF and the 1 k the follower has a phase margin of
about 55 degrees as a follower, no overshoot on a 0.5 V step, and the
follower settles in about 0.5 us; the x11 amplifier has 119 degrees.  Without
the 1 k the follower's phase margin is -38 degrees, that is, it oscillates, and
the x11 amplifier keeps about 107 degrees.  That is the book's lesson, kept on a
switch.  The simulated unity-gain crossing is 14 MHz, which is the models
talking: on the real board with SOT-23 parts and a probe on Q3 C, expect a few
MHz and a little less margin.  These small-signal margins are taken at 0 V, in
the dead band; with the output a few volts off zero the follower's margin is
nearer 40 degrees, which is why a cable on OUT needs R17 (section 2).  The
common-mode gain of the first stage goes from 0.076 with the resistor to 0.0004
with the sink.

**Swing.** As the x11 amplifier with 2 V peak in, OUT swings from -13.8 V to
+12.9 V into the 11 k divider: each side loses the Schottky, the positive side a
Vbe more.

## 4. The board

100 x 100 mm, two layers, every part on the front, a solid ground plane on the
back with 24 vias stitching the ground stubs and the hops into it.  100 SMT and 27
through-hole joints.  The silkscreen wires *are* the copper: `gen_pcb.py` routes
each track along the drawn wire, so the picture on the board is the netlist and
not a decoration.  Four crossings are hops: the crossing track dives to the
back layer between two vias and the silkscreen draws a small arc over it, as
the book draws a jump.

Choices worth knowing:

* **SOT-23 orientation.** The pads are 1.475 x 0.6 mm, so nothing passes under the
  body between the rows, but the collector pad sits between the two same-side
  pads 1.3 mm apart.  Every NPN and PNP is placed collector-up (rotation 90) with
  base at lower left and emitter at lower right, like the symbol, except Q2 and
  Q6, which are mirrored (rotation 270) because their bases come from the right.
* **No front copper pour.** The silkscreen schematic would be unreadable over fill,
  and there is nothing on this board that needs it.
* **Rails as lines.** +15 V along the top, -15 V along the bottom, 0.8 mm wide,
  exactly where the book draws them.
* **0805 passives, 1206 at the inputs and for R7, 2512 for R8 and R17**, big enough to
  probe and to replace; R7 and R8 sized for a misplaced ground clip, R17 for a
  shorted output.
* **Loops, not pins**: the RH-5019 surface-mount wire loop is one pad, costs a
  tenth of a dollar, and takes the hook every scope probe has.  A 2.54 mm pin
  header would take the hook too but is through-hole and lies down with it.
* **Identity**: the title, the authors, the revision and date and the repository
  URL in the band under the -15 V rail; the motto, "Op-Amps aren't magic; they're
  just transistors.", in the band above the +15 V rail between the fiducials; the
  user's instructions and a QR code to the repository on the back.

## 5. What could be wrong with a first board

In the order of how likely each is to make the board dead on arrival, and what
is there to catch it.

1. **The six SOT-23s fitted a half turn round.**  JLCPCB's drawing of the SOT-23
   has its pin 1 where KiCad has pin 3, so the upload CPL turns them by 180
   degrees.  This is predicted from their land pattern, not yet read in a preview
   of these two codes.  `PLACEMENT_CHECKS.txt` says what to look at; the lone pad
   (pin 3, the collector) must be up on Q1, Q3, Q4, Q5 and down on Q2, Q6.  Wrong, and every stage is dead: the bring-up
   step "each rail draws about 4 mA" catches it in a second.
2. **A DIP switch turned.**  Also predicted (from the 6-way of the same family,
   which was read).  Electrically symmetric: any orientation with the pads on the
   pads works, only the sliders' direction changes.
3. **The screw terminals' wire openings.**  JLCPCB's drawing of the KF301 has
   its openings on the side ours has the back, so the CPL turns it by 180 degrees
   (the pin row is symmetric, so only the body turns).  Predicted from their land
   pattern and the vendor drawing; wrong, and the wires go in from the middle of
   the board.  `PLACEMENT_CHECKS.txt` says which edge each one faces.
4. **Less phase margin than the models say.**  The 55 degrees as a follower is
   the simulation's at 0 V; the real board has less, and a 10x probe (15 pF) on
   Q3 C or Q2 C takes it down by 12 to 16 degrees, both probes by about 25.
   Cable capacitance on the OUT jacks is isolated from the push-pull by R17.
5. **A shorted output to a rail without a supply limit.**  To ground, R17 holds
   the current to 46 mA and Q4 or Q5 to 127 mW (C20526 is rated 200 mW at 625 K/W),
   indefinitely.  To a rail the current would be 90 mA and R17 would take 2.7 W;
   the handbook's 50 mA supply limit holds it to about 0.8 W.
6. **The BNC's rotation**, +90 degrees, was read on a built board of the same
   jack on the same footprint, so it is the least likely of the connectors to be
   wrong; the trimmer's is predicted, but its keyed hole pattern leaves the
   assembler no choice.
7. **Offset beyond the null range** on an unlucky pair.  +/-33 mV covers a 3:1
   beta mismatch; a 2N3904 pair from one reel is far better than that.

## 6. Rev B list

* A fourth switch position or a jumper to lift the 1 k input resistors for a
  bandwidth measurement without them.
* A place for a 1 nF to try as the compensation capacitor.
* Read every predicted rotation in the first preview and mark it "read".
* 35 V or 50 V parts for the 10 uF bypass capacitors, so a swapped GND lead (30 V)
  is inside their rating; today the handbook says +/-16 V.
