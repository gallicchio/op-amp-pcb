# Claude Code Chat Log — Discrete Op-Amp Educational PCB

Every prompt, verbatim (minor typos fixed), followed by the response as it was given, with the
renders as they were at the time (kept under `docs/history/`).  Model: Claude Fable 5.1.

## Prompt 1

> I want you to build a relatively inexpensive educational Op-Amp PCB out of discrete transistors that I'll order from JLCPCB using only components that they have available and in stock. The performance doesn't need to be great, but it should work as intended in basic op amp circuits. Record this prompt as Prompt 1 in CLAUDE_CODE_CHAT.md and record your response there and in the chat. Look at the other PCBs in ~/mudd/pcbs and ~/OpticsPCBs for recent examples. Follow the advice in ~/OpticsPCBs/CLAUDE_PCB.md and feel free to add to that document anything you learn while doing this. Feel free to use ~/.local/bin/kicad-10.0.7-x86_64.AppImage. The goal is an educational PCB. The silkscreen should look exactly like the schematic in that it the transistors should be arranged and rotated just like in a typical op-amp schematic, silkscreen should be drawn to clearly indicate what is what. Inputs and outputs and power should be screw terminals or BNCs where appropriate. I want you to make it out of the NPN and PNP transistors from Chapter 4 of Learning the Art of Electronics, which I've included as ~/mudd/pcbs/op-amp-pcb/datasheets_not_in_git/Tom_Hayes_Paul_Horowitz_Learning_the_Art_of_Electronics.pdf. Chapter 5 walks people through a design of an op amp with discrete transistors. I'd like you to follow that, though you should use individual discrete surface mount transistors to keep the silkscreen schematic looking like the schematic in the book. Another example of prior art on this is Evil Mad Scientist Laboratories, which has a discrete 741 design on a PCB, but their is more faithful to an existing chip, whereas ours is more for pedagogical purposes. I imagine that you'll select a 100mm x 100mm board for cost savings. The primary goal is clarity, simplicity, educational value, and ease of use for students in their first electronics lab class after having done most of chapter 4 in Learning the Art of Electronics.

Sent while the first response was being built:

> **1a.** Remember that the schematic should have an NPN or PNP symbol silkscreen right above (or around) the relevant NPN or PNP transistor. All of the wiring should be either blatantly obvious from the traces or silkscreened on. Intermediate surface-mount test loops for oscilloscope probes to clip onto should be liberally distributed on every trace worth probing.

> **1b.** As you make the schematics and board, show me screenshots and 3D renders here in the chat. Can you get away with a 2 layer board with all components on the top? 4 layer with all components on the top? Or do you need to do something more complicated and expensive? Make sure you include mounting holes in the corners for standoffs so that anything on the back side of the board does not get shorted or scratched.

> **1c.** Also, draw boxes with labels around things like "difference amplifier" and "push pull emitter follower" or however the book explains it.

> **1d.** On the silk screen, get rid of "Lab 5L" and add the github.com address where this checked out from. Maybe also a QR code to that address on the back, like you did for the ai-unleashes-chaos board in the same directory.

## Response 1

*2026-10-24, 09:51 to 12:13 PDT.*

**Two layers, all parts on top, is enough.**  Six transistors, three switches and
thirty passives on 100 x 100 mm leave most of the front empty; the back is one
unbroken ground plane with the text and the QR code on it, and M3 holes in the
four corners take standoffs.  Four layers would buy nothing.

### The circuit: Lab 5L's op-amp, kept, plus what a class needs

| stage | the book (Fig. 5L.15 and 5L.10) | on the board |
|---|---|---|
| difference amplifier | 2N3904 pair, 1.5 k collector load | Q1, Q2 MMBT3904, R3 1.5 k |
| tail | 10 k resistor, then the simple current sink 62 k / 10 k / 1 k | R4; Q6, R5, R6, R7; chosen by SW1 |
| gain stage | 2N3906 common emitter, 330 / 12 k | Q3 MMBT3906, R8, R9 |
| compensation | 100 pF collector to base of Q3 | C1 100 pF C0G, with R14 1 k in series (SW2 pole 2 shorts it) |
| output | 2N3904 / 2N3906 push-pull follower | Q4, Q5 |
| load / feedback | 10 k / 1 k divider, tap X to IN- for gain 11 | R10, R11; SW3 |

| addition | why |
|---|---|
| RV1 50 ohm trimmer between the emitters, wiper to the tail: OFFSET NULL | a discrete pair has millivolts of offset; null range +/-33 mV; a lifted wiper can only raise the resistance, never open the tail |
| R14 1 k in series with the Miller capacitor | the bare 100 pF leaves a right-half-plane zero: simulated follower phase margin -38 degrees (it oscillates); with the 1 k, +55 degrees.  The book's version stays on a switch |
| SW1 TAIL, SW2 COMPENSATION, SW3 FEEDBACK (2-way DIP switches) | the book's variants without loose jumpers: resistor or sink; with or without the 1 k; x11, follower or your own |
| R1, R2 1 k 1206 + D1, D2 1N4148W anti-parallel between the bases | a real op-amp's input clamps; a 2N3904's base-emitter breaks down at 6 V reverse |
| D3, D4 B5819W in series with the rails | a reversed bench supply does nothing |
| LED1, LED2 (green, 10 k) | rails at a glance |
| 17 RH-5019 SMT probe loops (3 of them ground) | a scope hook on every named node |
| BNC x3 (IN-, IN+, OUT) and KF301 screw terminals (IN-/GND, IN+/GND, OUT/GND, +15/GND/-15) | the generator and the scope on BNC; the student's own feedback network and the bench supply on screws |

Simulation (ngspice, `sim/opamp_sim.py`, results feed the sheet, the silkscreen and
the documents): tail 1.39 mA, Q3 1.30 mA; quiescent TAIL -0.66 V, Q2 C +13.9 V,
Q3 E +14.6 V, Q3 C +0.48 V, OUT 0.0 V; small-signal open-loop gain 139 at the
quiescent point (the class-B output is barely on), x11 amplifier really 10.2;
follower PM 55 degrees, settles in 0.5 us; swing -14.3 / +13.5 V; common-mode gain of
stage 1 0.073 (resistor tail) vs 0.0004 (sink).

### The board as the schematic

Copper follows the drawn wires: `scripts/layout.py` holds one list of wires and
`gen_pcb.py` draws each as track and as silkscreen.  Three crossings are hops
(the track dives to the back between two vias, the silkscreen arcs over).  Every
transistor sits in a circle with the base bar and the emitter arrow derived from
its real pads (NPN out, PNP in); SOT-23s are placed collector-up (rotation 90), or
mirrored where the base arrives from the right (Q2, Q6).  Dashed boxes name the
stages: INPUT PROTECTION, DIFFERENCE AMPLIFIER x11, TAIL, GAIN x30, COMP., PUSH-PULL
x1.  No front pour.  Rails are 0.8 mm lines along the top and bottom.  Title, authors,
rev, date and the repository URL in the band under the -15 V rail; the user's
instructions and a QR code to github.com/gallicchio/op-amp-pcb on the back.

![board, response 1](docs/history/2026-10-24-r1-top.png)
![render, response 1](docs/history/2026-10-24-r1-render-iso.png)
![schematic, response 1](docs/history/2026-10-24-r1-schematic.png)

### Checks and files

ERC 0; DRC 0 with schematic parity; 91 netlist assertions (`check_circuit.py`) that
re-derive the book's circuit from the exported netlist; no schematic text overlaps;
fab package checked (gerber layers, 59 placements against 39 BOM lines, every LCSC
code's JLCPCB description matching value and package, the QR decoded back out of the
board file, the trimmer's hole pattern keyed).  `./make.py` builds all of it in about a
minute.  Parts $7.62 a board; about $66 for the first assembled board and $8 for each
further one (JLCPCB's fixed fees dominate).  `docs/MANUFACTURING.md`, `out/opamp/`.

### What could be dead on arrival

1. The six SOT-23s turned a half turn: JLCPCB's drawing has pin 1 where KiCad has
   pin 3, so the upload CPL turns them +180, predicted from their land pattern and
   not yet read in a preview.  `PLACEMENT_CHECKS.txt`; the 4 mA per rail bring-up step
   catches it.
2. A DIP switch turned: electrically symmetric, harmless.
3. Ringing with a metre of coax on OUT; 55 degrees is the simulation's margin.
4. A shorted output kills Q4 or Q5: no current limit (rev B list).

## Prompt 2

> Can this be used as an opamp in an external circuit too? Like an integrator or photodiode current to voltage converter or an LED constant current source? (If both the 1x and 10x switches are off, for example?) Also, "tail" should indicate that the transistor is there to make a constant current source. Other labels like "comp" should be full words, even if they need to be rotated. This is for people who have never seen this material. It might even be used as a quick bridge between chapters 4 and 6 for a class with limited time -- I want to show students that opamps aren't magic (just made of transistors) but we don't have time to do all of lab 5. Could this be used for the first few circuits in lab 6 and 7 and maybe even 8? Are there small tweaks that don't add complexity that would allow this to function as an opamp in some of the circuits in the op amp chapters?

## Prompt 3

> (Keep recording all of these prompts in the CLAUDE_CODE_CHAT.md document along with your replies and screenshots and renders.)

## Prompt 4

> Being a "bad" integrator isn't the end of the world. Seeing and measuring drift current is part of lab 7 anyway. In fact, the 411 is almost "too good" to see these op amp non-idealities in some cases. As long as it doesn't run away in a tiny fraction of a second (and can't be fixed with a bigger capacitor), I'm perfectly happy with a "not very good op-amp" that is made of real discrete transistors that the students can see and poke at.

## Response 2

*2026-10-24, 12:25 to 12:55 PDT.*

**Yes: with both FEEDBACK sliders off it is a bare op-amp** on the IN-, IN+, OUT and
GND terminals, and I read the actual Lab 6L, 7L, 8L and 9L circuits out of the book's
PDF to judge each against its real numbers.  The numbers that matter: input bias
current about 2 uA (a BJT pair at 0.7 mA a side, beta 300; the '411 has 50 pA, the 741
80 nA); differential input impedance about 20 k plus the 1 k series resistors; open-loop
gain 140 at rest, a few hundred once the output moves; output +/-13 V into 1 k and up,
**no current limit** where the '411 has 25 mA; slew rate several V/us; the anti-parallel
clamp conducts when the inputs differ by more than 0.7 V (current limited by the 1 k's).

| book circuit | verdict | why |
|---|---|---|
| 6L.2 open-loop test | yes, better than with a '411 | gain of a few hundred: students can actually find the 50 mV window where OUT is not pinned |
| 6L.3 follower, Zout with the 1 k and feedback #2 | yes | FEEDBACK 2 is this circuit; the Zin test with a 1 M in series shows 2 V of bias-current drop instead, which is the lesson |
| 6L.4 non-inverting x11 | yes | FEEDBACK 1 is exactly Fig. 6L.7 (the book's own footnote points back to Lab 5L); gain 10.2, the finite-gain error |
| 6L.5 inverting -10, 6L.6 summing | yes | summing junction on the IN- terminal; the 1 k inside the loop costs 2 mV of offset |
| 6L.8 push-pull buffer with 3055/2955 | yes, modest amplitude | base drive of 10 mA is fine; the same crossover demonstration the board does inside itself |
| 6L.9 photodiode with 10 M | **no** | 2 uA x 10 M = 20 V; even 1 M gives 2 V of drifting offset.  The phototransistor version with 100 k: yes, 0.2 V offset |
| 6L.10 current source (floating 1 k load; 2N3906 + load to ground) | yes | the op-amp only supplies base current; an LED at 10-20 mA is the second circuit exactly |
| 7L.1 integrator (10 M leak, '411) | yes as a bias-current demonstration, with a bigger C | drift Ib/C: 230 V/s with 10 nF (rails in 60 ms), 23 V/s with 100 nF, 2.3 V/s with 1 uF (the 1 s/div sweep the book asks for); the 10 M leak pins the output, use 1 M or none; the reset button works |
| 7L.2 differentiator, 7L.3 slew rate | yes | slew rate lands between the 741's 0.5 and the '411's 15 V/us: a third data point |
| 7L.4 single-supply '358 at +5 V | no | needs both rails |
| 8L.1 comparator at 100 kHz | yes | slews as the book says it should |
| 8L.1.3 Schmitt trigger, 8L.2 RC relaxation oscillator | yes, small hysteresis | thresholds of +/-0.67 V sit at the clamp's knee; with volts of hysteresis the clamp loads a 10 k divider |
| 8L.7 Wien bridge with the lamp | yes at modest amplitude | 15 mA of output current at full swing is the ceiling |
| 9L.3 instability with capacitive loads, 9L.4 buffer in the loop | yes | it has 55 degrees of margin to lose |

Prompt 4 settles the integrator: it drifts at 2 uA / C, a bigger capacitor tames it to
volts per second, and the drift is the measurement.  Nothing on the board needs changing
for it.

**Tweaks.**  Done now, no parts added: TAIL box gains "CURRENT SOURCE" (standing up its
left side), "COMP." became "COMPENSATION" (standing), "GAIN STAGE x30", "PUSH-PULL
FOLLOWER x1", switch poles read "1: Q6 / 2: 10k" and "1: 100pF + 1k / 2: no 1k", the top
band spells the switches out in words, and the probe loops C2 / E3 / C3 are now Q2 C /
Q3 E / Q3 C (there is a capacitor called C2 on the board; the schematic labels, the
netlist, the circuit checker and the handbook all use the new names).  The back of the
board now says how to use it as a bare op-amp, with its two limits.  The one tweak worth
adding parts for is an **output current limit**: two more transistors and two 39 ohm
resistors in the push-pull, the 741's own scheme, limiting to about 15 mA so a shorted
OUT survives.  Students will short the output in Lab 6; the '411 shrugs, this board
loses Q4 or Q5.  It adds two circles to the PUSH-PULL box and a new lesson ("why your
op-amp has a current limit").  Not done; it is a change to the book's circuit, so it is
Jason's call.  Not worth doing: anything about the bias current (a Darlington input or a
lower tail current each costs more than it buys).

![board, response 2](docs/history/2026-10-24-r2-top.png)
![render, response 2](docs/history/2026-10-24-r2-render-iso.png)
![back silkscreen, response 2](docs/history/2026-10-24-r2-silk-bottom.png)
![schematic, response 2](docs/history/2026-10-24-r2-schematic.png)

Also in this response: three fiducials; `docs/HANDBOOK.md` (power, switches, the
voltage at every loop, bring-up, exercises in Lab 5L's order), `docs/DESIGN_NOTES.md`,
`docs/MANUFACTURING.md` with JLCPCB's order form field by field and
`out/opamp/PLACEMENT_CHECKS.txt`; `LICENSE` (CERN-OHL-P-2.0 hardware, MIT scripts);
lessons written into `~/OpticsPCBs/CLAUDE_PCB.md`.  Build: ERC 0, DRC 0, 91 circuit
checks, fab checks all pass, 25 of 25 document claims match the build.
