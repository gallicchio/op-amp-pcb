# Handbook

For the student at the bench and for whoever brings up the first boards.  The
numbers come from the simulation in `sim/opamp_sim.py`, built with the same
values the board carries; the build checks that this file still quotes them.

## 1. What you are looking at

The silkscreen is the schematic.  Signal flows left to right: the inputs on the
left, the difference amplifier and its tail in the middle, the gain stage, the
push-pull output and the OUT jack on the right.  The +15 V rail runs along the
top and the -15 V rail along the bottom.  Every transistor sits inside a circle
with its emitter arrow drawn the way the book draws it: NPN arrows point out,
PNP arrows point in.  A dashed box names each stage.

| block | parts | what it does |
|---|---|---|
| INPUT PROTECTION | R1, R2, D1, D2 | 1 k in series with each input; two diodes between the bases hold the difference under 0.7 V |
| DIFFERENCE AMPLIFIER x11 | Q1, Q2, R3, RV1 | the book's diff pair; R3 is the 1.5 k collector load; the output is Q2's collector, the node Q2 C |
| TAIL | Q6, R5, R6, R7, R4, SW1 | the 1.4 mA current sink, or the 10 k resistor |
| GAIN x30 | Q3, R8, R9 | PNP common-emitter stage, 330 ohm emitter, 12 k collector; its output is Q3 C |
| COMPENSATION | C1, R14, SW2 | the 100 pF Miller capacitor from C3 back to C2, with 1 k in series |
| PUSH-PULL FOLLOWER | Q4, Q5, R15, R16 | the output followers, with 47 ohm in each emitter for the limit below |
| OUTPUT CURRENT LIMIT | Q7, Q8, D5, D6 | not in the book: a safety net, as in a real op-amp.  Q7 (Q8) turns on when more than about 0.65 V stands across R15 (R16) and steals the drive; the diodes keep the idle one out of the way.  It limits at about 22 mA into a dead short (15 mA through Q4 or Q5) and does nothing below that |
| FEEDBACK | R10, R11, SW3 | the book's 10 k / 1 k load and x11 divider; its tap is X, and the switch returns X or OUT to IN- |

## 2. Power

| | |
|---|---|
| supply | +15 V, GND, -15 V on the three-way terminal at the bottom right, marked POWER |
| current | about 4 mA a rail at rest, up to 20 mA driving a 1 k load to full swing |
| protection | a Schottky in each rail: reversed leads do nothing (no LED), they do not kill it |
| signs of life | both green LEDs on, one beside each rail |

Set the bench supply's current limit to 50 mA, always, not only for a new board:
the board never needs more than 30 mA a rail, and with the limit a shorted
output or a clip on a rail loop cannot burn anything.  One mistake the limit
does NOT catch: a scope's ground clip on Q2 C or Q3 E puts 0.6 W into the 0805
R8 (rated 0.125 W) while drawing under 50 mA, so the supply never limits and
R8 slowly cooks -- you will smell it; power off and move the clip.  The two
10 uF bypass capacitors hold the rails if the leads are long.  Stay within
+/-16 V at the terminal: the 10 uF bypass capacitors are 25 V parts and Q3
and Q6 are 40 V parts.

## 3. Inputs and output

| | jack | terminal | limits |
|---|---|---|---|
| IN- | J1, left, upper | J4 IN- / GND | +/-12 V |
| IN+ | J2, left, lower | J5 IN+ / GND | +/-12 V |
| OUT | J3, right | J7 OUT / GND | +/-12 V into 1 k, 15 mA |

The jack and the terminal of each input are the same node, so a generator can
come in on the BNC while a feedback network goes on the screws.  Each input has
1 k in series before the transistor base, so the 1N4148 clamp between the bases
limits the current a wrong input can push to about 7 mA (15 mA, 0.2 W in each
1 k, with the two inputs at opposite rails).  The output limits itself (about
15 mA through Q4 or Q5, 22 mA into a dead short with the sense transistor's
share), so a short to ground is survived for minutes, not an afternoon: 0.21 W
in a SOT-23 whose stocked part is rated 0.2 W.  A short to a rail puts 0.43 W
into Q4 or Q5, twice its rating: a slip, not a minute.  Loads of 1 k and up are
the design.

## 4. The switches

Each DIP switch has two sliders, numbered 1 and 2 on the board.  "On" is toward
the word ON beside the switch.

| switch | 1 on | 2 on | both off |
|---|---|---|---|
| **TAIL** SW1 | Q6 current sink (normal) | 10 k tail resistor, the book's first version | no tail: the diff pair is dead, nothing works |
| **COMPENSATION** SW2 | 100 pF + 1 k from C3 to C2 (normal) | the bare 100 pF, no 1 k: the book's version | no compensation |
| **FEEDBACK** SW3 | X to IN-: gain of 11, non-inverting | OUT to IN-: follower | open loop, or your own feedback on the terminals |

Both TAIL sliders on puts the resistor in parallel with the sink, which does no
damage but doubles the tail current to 2.8 mA; the offset then sits beyond
RV1's reach, so null again with slider 2 off.  Both COMPENSATION sliders on is
the same as 2 alone.  Both FEEDBACK sliders
on shorts R10, which makes a follower with a 1 k load to ground.

Usual, as the back of the board says: TAIL 1, COMPENSATION 1, FEEDBACK as needed.

## 5. The probe loops

18 probe loops, one per named node, take a scope probe's hook or a mini-grabber.
Four of them are ground, for the probe's clip, one per scope channel.  The voltages are what the
simulation gives as a follower (FEEDBACK 2 on) with IN+ grounded, TAIL 1,
COMPENSATION 1, +/-15 V in.  Expect a few hundred millivolts of spread from transistor
to transistor; a volt off is a fault.

| loop | node | where | expect |
|---|---|---|---|
| TP1 | IN- | after R1, at Q1's base | 0.0 V |
| TP2 | IN+ | after R2, at Q2's base | 0.0 V |
| TP13 | Q1 E | Q1's emitter | -0.6 V |
| TP14 | Q2 E | Q2's emitter | -0.6 V |
| TP3 | TAIL | the trimmer's wiper, Q6's collector | -0.7 V |
| TP5 | Q6 B | the 62 k / 10 k divider | -13.0 V |
| TP4 | Q6 E | across R7: 1.4 mA x 1 k | -13.6 V |
| TP6 | Q2 C | Q2's collector, the diff amp's output | +13.9 V |
| TP7 | Q3 E | Q3's emitter | +14.6 V |
| TP8 | Q3 C | Q3's collector, the push-pull's input | +0.5 V |
| TP9 | OUT | the output, beside the jack | 0.0 V |
| TP10 | X | the 10 k / 1 k tap, in the FEEDBACK box | 0.0 V |
| TP11 | +15V | the rail, after the Schottky | +14.6 V |
| TP12 | -15V | the rail, after the Schottky | -14.6 V |
| TP100 - TP103 | GND | for the clip, one per scope channel | 0 |

The 0.6 V steps are the story of the board: Q1 and Q2's emitters sit a diode
below their grounded bases; Q2 C sits where the 1.5 k drops half the tail
current; Q3's base-emitter junction takes 0.6 V off the +15 V rail; Q3 C rests half
a volt above the output because Q4 is just conducting.

## 6. Offset null

As a follower (FEEDBACK 2) with IN+ grounded, read OUT on a meter and turn RV1
until it is zero.  The trimmer moves the emitter resistors of the pair against
each other and has a null range of about +/-33 mV at the input; a board whose
offset is beyond that has a mismatched pair or a wrong resistor.  The null drifts
with temperature: hold a finger on Q1 and watch it.

## 7. Bringing up a new board

1. Look at it.  Eight transistors with their lone pad on the collector side (up
   for Q1, Q3, Q4, Q5, Q7, Q8; down for Q2 and Q6), the diode bands where the silkscreen bars
   are, the BNC barrels off the edges, the trimmer screw up.
2. Set TAIL 1, COMPENSATION 1, FEEDBACK 2.  Nothing on the inputs.
3. Power from a current-limited supply at 30 mA.  Both LEDs light; each rail
   draws about 4 mA.  A rail at more than 10 mA with nothing connected is a
   fault: power off and look for a transistor in backwards.
4. Read TP11 and TP12: +/-14.6 V.
5. Read the loops against the table above.  TAIL, Q2 C, Q3 E, Q3 C and Q6 E tell you
   which stage is wrong if one is.
6. Null the offset.
7. Put 1 V peak at 1 kHz into IN+ (BNC) and look at OUT: a clean copy.  Raise it to
   10 V peak: still a copy.  A square wave: clean edges, no ringing.
8. FEEDBACK 1: the same input at 0.5 V peak comes out 5 V peak.
9. COMPENSATION 2 as a follower: the square wave's edges ring, which is the book's point.
   Back to COMPENSATION 1.

## 8. Exercises, in the order of Lab 5L

Each one is a switch setting and a pair of loops.  "Open loop" means both
FEEDBACK sliders off.

1. **The operating point.**  Follower, IN+ grounded.  Measure every loop and
   account for every 0.6 V.  Work out the tail current from TP4 and R7, and check
   it against the drop across R3 (TP11 minus TP6).
2. **The difference amplifier.**  Open loop.  A few millivolts at 1 kHz into IN+,
   IN- grounded.  TP6 against the input: the gain is about 11 and inverted.  Now
   drive IN- instead: the same gain, not inverted.  Then tie IN+ and IN- together
   and drive both: the common-mode gain.
3. **The tail.**  Repeat the common-mode measurement with TAIL 2 (the 10 k
   resistor).  The current sink buys a hundred times less common-mode gain for
   the price of one transistor.
4. **The gain stage.**  Open loop, a millivolt or so in.  TP8 against TP6: about
   30, inverted again.  Note how quickly C3 hits a rail: the whole thing has a
   gain of a few hundred at rest.
5. **The push-pull and its crossover.**  Open loop, a 50 mV triangle in.  OUT
   against TP8: a dead band of about 1.2 V where neither Q4 nor Q5 conducts.  Now
   close the loop (FEEDBACK 2) with the same input: the dead band vanishes from OUT
   and reappears as a step at TP8.  That is what feedback does.
6. **The follower.**  FEEDBACK 2.  Gain, input and output swing into 1 k, slew rate
   on a 10 V square wave, and the bandwidth.
7. **The x11 amplifier.**  FEEDBACK 1.  Measure the gain to three figures: it is
   less than 11 by the finite open-loop gain.  Compare the bandwidth with the
   follower's.
8. **Compensation.**  COMPENSATION 2, then both off, as a follower and as x11.  Where it
   oscillates, read the frequency, then look at TP8 to see that the loop, not the
   output stage, is ringing.
9. **Offset.**  Null it, then warm Q1 with a finger and watch OUT walk.  Explain
   the sign.
10. **Your own circuit.**  FEEDBACK off.  Wire an inverting amplifier on the IN-,
    OUT and GND terminals (10 k in, 100 k back, IN+ grounded).  Then an
    integrator, a summing amplifier, a comparator with no feedback at all.

## 9. As an op-amp in your own circuit (Labs 6L to 9L)

Both FEEDBACK sliders off, and the IN-, IN+, OUT and GND terminals are a bare
op-amp: pins 2, 3 and 6 of the '411 the later labs use.  It is a real one, with
real limits, and the limits are the lesson.

| | this board | LF411 |
|---|---|---|
| input bias current | about 2 uA (a BJT pair at 0.7 mA a side) | 50 pA |
| input offset | millivolts, nullable with RV1 | 0.8 mV |
| open-loop gain | about 140 at rest, a few hundred once the output moves | 200,000 |
| output current | +/-12 V into 1 k; limits at about 15 mA (22 mA into a dead short); a short to ground is survived | 25 mA, limited |
| slew rate | several V/us | 15 V/us |
| inputs | anti-parallel diodes between the bases conduct above 0.7 V of difference, through the two 1 k | none |

| book circuit | works? | notes |
|---|---|---|
| 6L.2 open-loop test | yes | with a gain of hundreds you can find the window where OUT is not pinned |
| 6L.3 follower, Zout with the 1 k and feedback #2 | yes | the 1 M-in-series Zin test shows 2 V of bias-current drop instead: measure Ibias from it |
| 6L.4 non-inverting x11, 6L.5 inverting -10, 6L.6 summing | yes | FEEDBACK 1 is 6L.4 exactly; gains come out 2 to 8 % low, the finite-gain error |
| 6L.8 push-pull buffer | yes | keep the speaker amplitude modest; this board does the same demonstration inside its own box |
| 6L.9 photodiode with 10 M | no | 2 uA x 10 M = 20 V.  The phototransistor version with 100 k works, with 0.2 V of offset |
| 6L.10 current source, both versions | yes | an LED at 10 to 20 mA is the second one |
| 7L.1 integrator | yes, with a bigger C | drift is Ibias / C: 230 V/s with 10 nF, 2.3 V/s with 1 uF.  Leave the 10 M leak out or use 1 M; the reset button works; this is the bias-current measurement of 7L.1.1 made easy |
| 7L.2 differentiator, 7L.3 slew rate | yes | a third slew-rate data point between the 741 and the '411 |
| 7L.4 single-supply microphone amplifier | no | needs both rails |
| 8L.1 comparator, 8L.1.3 Schmitt trigger, 8L.2 relaxation oscillator | yes | keep the hysteresis under a volt or so, or the input clamp loads the divider |
| 8L.7 Wien bridge | yes at modest amplitude | 15 mA of output current is the ceiling |
| 9L.3 capacitive loads, 9L.4 buffer in the loop | yes | 51 degrees of phase margin to lose; a probe on Q3 C costs 12 of them |

Loads of 1 k and up are the design; a short is survived, not enjoyed.

## 10. If it does not work

| symptom | look at |
|---|---|
| no LED | supply reversed or absent; the Schottky is doing its job |
| one LED | that rail's lead; the two LEDs are independent |
| OUT stuck at a rail, open loop | normal: the open-loop gain is hundreds |
| OUT stuck at a rail as a follower | TAIL both off; a transistor in backwards; TP6 shows which stage |
| OUT clips at a few volts into a low load | the current limit at work: raise the load to 1 k |
| rings or oscillates as a follower | COMPENSATION 1 off; a long unterminated cable on OUT |
| hum | the scope's ground clip is not on a GND loop |
| a resistor smells hot | a ground clip on a signal loop: Q2 C or Q3 E to ground puts 0.6 W into R8, Q6 E or Q6 B to ground 0.2 W into R7.  That short draws under 50 mA, so the supply limit does not catch it: power off and move the clip |
