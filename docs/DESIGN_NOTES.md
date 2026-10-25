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
| gain stage | 2N3906 common emitter, 330 ohm emitter, 12 k collector | Q3 (MMBT3906), R8 330, R9 12 k |
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
| offset null | RV1, 50 ohm between the emitters, wiper to the tail | a discrete pair has millivolts of offset; a trimmer whose ends are the two emitter resistors (25 ohm each at centre) is the textbook null and costs one part.  Its wiper is the tail, so grit under the wiper cannot open the tail: the resistance only rises |
| series 1 k with the Miller capacitor | R14 | the book's bare 100 pF puts a right-half-plane zero at 1 / (2 pi C / gm): the follower is unstable with it.  1 k in series moves the zero to the left half plane.  SW2 pole 2 shorts it so the book's version can be shown ringing |
| three 2-way DIP switches | SW1 TAIL, SW2 COMPENSATION, SW3 FEEDBACK | the book's variants (resistor tail or current sink; compensation or not; x11, follower or your own) without jumpers to lose |
| input protection | R1, R2 1 k 1206; D1, D2 1N4148W anti-parallel between the bases | a real op-amp's input clamps.  A 2N3904's base-emitter junction breaks down at 6 V reverse; a student with a 10 V generator on one input and the other grounded would otherwise degrade Q1 or Q2.  The 1206 resistors take 50 mW each with one input at a rail and the other grounded, 0.21 W each with the two inputs at opposite rails |
| output current limit | R15, R16 47 ohm in the emitters; Q7, Q8 sensing them; D5, D6 | a 741's scheme: when 0.65 V stands across a sense resistor the sense transistor steals the push-pull's drive.  Students will short OUT in Lab 6; the '411 shrugs, a bare Q4 would die.  The diodes are not in the 741: with the book's class-B pair the idle sense transistor's base-collector junction is forward-biased by the other half's Vbe and, without a diode, injects current into the drive node and halves the negative swing (found in simulation).  Drawn in its own box, labelled as the safety net it is |
| reverse-supply protection | D3, D4 B5819W in series with each rail | a reversed bench supply forward-biases every junction on the board; a 0.35 V drop at 4 mA costs nothing here |
| rail LEDs | LED1, LED2 through 10 k | rails at a glance, 1.2 mA each |
| bypass | C2, C4 10 uF; C3, C5 100 nF | long bench leads |
| probe loops | TP1 - TP14, TP100 - TP103 | one per node the book asks you to look at, X included, plus four grounds for the clip, one per scope channel |
| BNCs and screw terminals | J1 - J7 | BNCs for the generator and the scope; terminals for the feedback network a student wires and for a bench supply |

## 3. What the simulation says

`sim/opamp_sim.py` runs ngspice on the netlist as built, with generic 2N3904 /
2N3906 models (Bf 300 / 200, VAF 100, Cjc 4 - 4.5 pF) and 3 pF of stray at the
three high-impedance nodes.  The results in `sim/results.json` feed the schematic
notes, the handbook and this file.

**Operating point** (follower, IN+ grounded): tail current of 1.39 mA through Q6,
1.30 mA in Q3, Q2 C at +13.9 V, Q3 C at +0.5 V, OUT at -0.006 V.  The output
current into a dead short is about 22 mA; into the 11 k divider it never limits.  The follower's own
offset with everything nominal is -5.6 mV, from Q1's collector sitting at the
rail while Q2's sits 1 V below it (Early effect); the null range of about
+/-33 mV covers it and the pair's real mismatch several times over.

**Gain.** Stage 1 gives 11.1 at Q2 C, stage 2 gives 34 at Q3 C, and the
push-pull at rest is barely conducting (its small-signal gain at the quiescent
point is 0.37, the dead band), so the small-signal open-loop gain at
the quiescent point of about 138 is what a student measuring tiny signals
around zero will see.  Once the output moves and Q4 or Q5 is on, the follower's
gain goes to 1 and the loop gain is several hundred.  Consequently the x11
amplifier really has a gain of 10.2: the finite-gain error the book has
students compute.

**Stability.** With the 100 pF and the 1 k the follower has a phase margin of
about 51 degrees as a follower, no overshoot on a 0.5 V step, and the
follower settles in about 0.6 us; the x11 amplifier has 120 degrees.  Without
the 1 k the follower's phase margin is -43 degrees, that is, it oscillates, and
the x11 amplifier keeps about 100 degrees.  That is the book's lesson, kept on a
switch.  The simulated unity-gain crossing is 14 MHz, which is the models
talking: on the real board with SOT-23 parts and a probe on Q3 C, expect a few
MHz and a little less margin.  The common-mode gain of the first stage goes
from 0.073 with the resistor to 0.0004 with the sink.

**Swing.** As the x11 amplifier with 2 V peak in, OUT swings from -14.3 V to
+13.4 V into the 11 k divider: the positive side loses a Vbe plus the Schottky.

## 4. The board

100 x 100 mm, two layers, every part on the front, a solid ground plane on the
back with 32 vias stitching the ground stubs and the hops into it.  112 SMT and 18
through-hole joints.  The silkscreen wires *are* the copper: `gen_pcb.py` routes
each track along the drawn wire, so the picture on the board is the netlist and
not a decoration.  Eight crossings are hops: the crossing track dives to the
back layer between two vias and the silkscreen draws a small arc over it, as
the book draws a jump.  Four of the eight came with the current limit, whose
diode returns and sense leads have to cross the output's own wires.

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
* **0805 passives, 1206 at the inputs**, big enough to probe and to replace.
* **Loops, not pins**: the RH-5019 surface-mount wire loop is one pad, costs a
  tenth of a dollar, and takes the hook every scope probe has.  A 2.54 mm pin
  header would take the hook too but is through-hole and lies down with it.
* **Identity**: the title, the authors, the revision and date and the repository
  URL in the band under the -15 V rail; the user's instructions and a QR code to
  the repository on the back.

## 5. What could be wrong with a first board

In the order of how likely each is to make the board dead on arrival, and what
is there to catch it.

1. **The eight SOT-23s fitted a half turn round.**  JLCPCB's drawing of the SOT-23
   has its pin 1 where KiCad has pin 3, so the upload CPL turns them by 180
   degrees.  This is predicted from their land pattern, not yet read in a preview
   of these two codes.  `PLACEMENT_CHECKS.txt` says what to look at; the lone pad
   must be on the collector side.  Wrong, and every stage is dead: the bring-up
   step "each rail draws about 4 mA" catches it in a second.
2. **A DIP switch turned.**  Also predicted (from the 6-way of the same family,
   which was read).  Electrically symmetric: any orientation with the pads on the
   pads works, only the sliders' direction changes.
3. **Less phase margin than the models say.**  The 51 degrees as a follower is
   the simulation's; the real board has less, and a 10x probe (15 pF) on Q3 C
   or Q2 C takes the model to 39 or 35 degrees, both probes to 25.  Cable
   capacitance on OUT is not the problem: with the 47 ohm sense resistors
   between the emitters and OUT, 100 pF of coax raises the margin to 90
   degrees and 10 nF still leaves 30.
4. **A shorted output held for minutes.**  The limit holds Q4 or Q5 at about
   14.5 mA (22 mA reaches the short, the rest through the sense transistor): to
   ground that is 0.21 W in a SOT-23 whose stocked part (C20526) is rated 0.2 W
   at 625 K/W, so minutes; to either rail it is 0.43 W, twice the rating: it
   survives a student's slip, not a minute.
5. **The BNC's rotation**, +90 degrees, was read on a built board of the same
   jack on the same footprint, so it is the least likely of the connectors to be
   wrong; the terminal blocks' and the trimmer's are predicted, but their hole
   patterns (the trimmer's is keyed) leave the assembler little choice.
6. **Offset beyond the null range** on an unlucky pair.  +/-33 mV covers a 3:1
   beta mismatch; a 2N3904 pair from one reel is far better than that.

## 6. Rev B list

* A fourth switch position or a jumper to lift the 1 k input resistors for a
  bandwidth measurement without them.
* A place for a 1 nF to try as the compensation capacitor.
* Read every predicted rotation in the first preview and mark it "read".
