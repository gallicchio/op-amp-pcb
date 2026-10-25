#!/usr/bin/env python3
"""Apply the review's proposed changes to the review copy (project/), exactly.

Each edit is an exact-string replacement that must occur once; the script stops
on the first miss so nothing is half-applied.  Run from this directory; then
`cd project && ./make.py`, and `diff -ru` the originals against the copy.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "project")

EDITS = [
    # ---------------------------------------------------------------- F1: SW2 pole 2 ----
    # board: pole 2 (pads 2-3) takes Q2 C straight to C1, bypassing R14
    ("scripts/layout.py",
     '    ("/Q2 C", [(53.5, 30.0), ("SW2", "4")], W_SIG),\n',
     '    ("/Q2 C", [(53.5, 30.0), (53.5, 37.5), ("SW2", "4")], W_SIG),\n'
     '    ("/Q2 C", [(53.5, 37.5), (56.04, 37.5), ("SW2", "3")], W_SIG),\n'),
    ("scripts/layout.py",
     '    ("Net-(R14-Pad1)", [("SW2", "2"), (56.04, 51.0), (53.5, 51.0)], W_SIG),\n',
     ''),
    ("scripts/layout.py",
     '    ("Net-(C1-Pad1)", [("SW2", "3"), (58.3, 40.1), (58.3, 56.0), (53.5, 56.0)], W_SIG),\n',
     '    ("Net-(C1-Pad1)", [("SW2", "2"), (56.04, 50.5), (58.3, 50.5), (58.3, 56.0), (53.5, 56.0)], W_SIG),\n'),
    ("scripts/layout.py",
     '    (54.2, 37.7, "SW2", 0.8, 0.15, "left", 0),\n',
     '    (58.2, 37.6, "SW2", 0.8, 0.15, "center", 0),\n'),
    # schematic: the same
    ("scripts/gen_sch.py",
     '    # pole 2 shorts the 1k: its lower pin to the node above R14, its upper pin\n'
     '    # round the outside to the node below it\n'
     '    s.wire(c2_, (c2_[0], g(52)), (CX, g(52)))\n'
     '    s.wire(c3_, (g(98), c3_[1]), (g(98), g(57)), (CX, g(57)))\n',
     '    # pole 2 bypasses the 1k: its upper pin up to Q2 C, its lower pin to the\n'
     '    # node between R14 and C1, so "2" alone is the book\'s bare 100 pF\n'
     '    s.wire(c3_, (g(98), c3_[1]), (g(98), C2_Y))\n'
     '    s.junction(g(98), C2_Y)\n'
     '    s.wire(c2_, (c2_[0], g(57)), (CX, g(57)))\n'),
    ("scripts/gen_sch.py",
     '    s.junction(CX, g(52))\n',
     ''),
    ("scripts/gen_sch.py",
     '          "2 ON: shorts the 1k, leaving the bare 100 pF.",\n',
     '          "2 ON: the bare 100 pF, no 1k: the book\'s version.",\n'
     '          "1 and 2 ON: the same as 2.",\n'),
    ("scripts/check_circuit.py",
     '    check(N.net("SW2", 2) == n1 and N.net("SW2", 3) == N.net("C1", 1), "SW2 pole 2 shorts R14")\n',
     '    check(N.net("SW2", 3) == "Q2 C" and N.net("SW2", 2) == N.net("C1", 1),\n'
     '          "SW2 pole 2 takes Q2 C straight to C1, bypassing R14: the book\'s bare 100 pF on its own")\n'),
    ("scripts/layout.py",
     '    "   COMPENSATION 2 shorts the 1k: the book\'s bare",\n'
     '    "   100 pF; the x11 amp still works, a follower rings.",\n',
     '    "   COMPENSATION 2 = the bare 100 pF, no 1k (the book\'s):",\n'
     '    "   the x11 amp still works, a follower rings.",\n'),
    ("docs/HANDBOOK.md",
     '| **COMPENSATION** SW2 | 100 pF + 1 k from C3 to C2 (normal) | shorts the 1 k: the book\'s bare 100 pF | no compensation |\n',
     '| **COMPENSATION** SW2 | 100 pF + 1 k from C3 to C2 (normal) | the bare 100 pF, no 1 k: the book\'s version | no compensation |\n'),
    # ------------------------------------------------------- F2: ON marks on the switches ----
    ("scripts/layout.py",
     '    (37.5, 56.6, "SW1", 0.8, 0.15, "center", 0),\n',
     '    (37.5, 56.6, "SW1", 0.8, 0.15, "center", 0),\n'
     '    (33.8, 61.6, "ON", 0.8, 0.15, "center", 0),\n'),
    ("scripts/layout.py",
     '    (64.0, 54.0, "COMPENSATION", 0.9, 0.15, "center", 90),\n',
     '    (64.0, 54.0, "COMPENSATION", 0.9, 0.15, "center", 90),\n'
     '    (58.2, 39.4, "ON", 0.8, 0.15, "center", 0),\n'),
    ("scripts/layout.py",
     '    (86.2, 60.3, "FEEDBACK", 0.9, 0.18, "right", 0),\n',
     '    (86.2, 60.3, "FEEDBACK", 0.9, 0.18, "right", 0),\n'
     '    (85.0, 72.4, "ON>", 0.8, 0.15, "center", 0),\n'),
    ("docs/HANDBOOK.md",
     'Each DIP switch has two sliders, numbered 1 and 2 on the board.  "On" is toward\nthe number.\n',
     'Each DIP switch has two sliders, numbered 1 and 2 on the board.  "On" is toward\nthe word ON beside the switch.\n'),
    ("scripts/gen_docs.py",
     '    ("SW1, SW2, SW3", "2-way DIP switch: pads on pads; sliders move toward the \'1 / 2\' legends",\n'
     '     "SW1 and SW2 sliders moving toward the labelled side; electrically it cannot go in wrong"),\n',
     '    ("SW1, SW2, SW3", "2-way DIP switch: pads on pads; the part\'s own ON marking",\n'
     '     "on the side of the silkscreen word ON (left of SW1, above SW2; the \'ON>\' above SW3\'s right-hand pads points at it); electrically it cannot go in wrong"),\n'),
    # --------------------------------------------------- F3: the supply limit as the rule ----
    ("docs/HANDBOOK.md",
     'A current-limited bench supply at 30 mA is the right thing for a new board.  The\n'
     'two 10 uF bypass capacitors hold the rails if the leads are long.\n',
     'Set the bench supply\'s current limit to 50 mA, always, not only for a new board:\n'
     'the board never needs more than 30 mA a rail, and with the limit a scope\'s\n'
     'ground clip on the wrong loop (Q2 C or Q3 E to ground would otherwise put\n'
     '0.6 W into the 0805 R8) or a shorted output cannot burn anything.  The two\n'
     '10 uF bypass capacitors hold the rails if the leads are long.\n'),
    ("docs/HANDBOOK.md",
     '| hum | the scope\'s ground clip is not on a GND loop |\n',
     '| hum | the scope\'s ground clip is not on a GND loop |\n'
     '| a resistor smells hot | a ground clip on a signal loop: Q2 C or Q3 E to ground puts 0.6 W into R8, Q6 E or Q6 B to ground 0.2 W into R7.  The 50 mA supply limit is what saves R8; power off and move the clip |\n'),
    ("scripts/layout.py",
     '    "POWER: +15 V, GND, -15 V into the terminal, 20 mA.",\n'
     '    "   Both green LEDs light when it is right way round.",\n',
     '    "POWER: +15 V, GND, -15 V into the terminal, 20 mA; set",\n'
     '    "   the supply\'s limit to 50 mA.  Both LEDs light if right.",\n'),
    # ------------------------------------------- F4: the output limit and the rail short ----
    ("docs/HANDBOOK.md",
     'limits the current a wrong input can push to about 6 mA.  The output limits\n'
     'itself at about 22 mA, so a short to ground or to a rail is survived (the\n'
     'transistor runs hot: do not leave it).  Loads of 1 k and up are the design.\n',
     'limits the current a wrong input can push to about 7 mA (15 mA, 0.2 W in each\n'
     '1 k, with the two inputs at opposite rails).  The output limits itself (about\n'
     '15 mA through Q4 or Q5, 22 mA into a dead short with the sense transistor\'s\n'
     'share), so a short to ground is survived for minutes, not an afternoon: 0.21 W\n'
     'in a SOT-23 whose stocked part is rated 0.2 W.  A short to a rail puts 0.43 W\n'
     'into Q4 or Q5, twice its rating: a slip, not a minute.  Loads of 1 k and up are\n'
     'the design.\n'),
    ("docs/HANDBOOK.md",
     '| OUT | J3, right | J7 OUT / GND | +/-13 V into 1 k or more, 20 mA |\n',
     '| OUT | J3, right | J7 OUT / GND | +/-12 V into 1 k, 15 mA |\n'),
    ("docs/HANDBOOK.md",
     'It limits at about 22 mA and does nothing below that |\n',
     'It limits at about 22 mA into a dead short (15 mA through Q4 or Q5) and does nothing below that |\n'),
    ("docs/HANDBOOK.md",
     '| output current | +/-13 V into 1 k and up; limits at about 22 mA, a short is survived | 25 mA, limited |\n',
     '| output current | +/-12 V into 1 k; limits at about 15 mA (22 mA into a dead short); a short to ground is survived | 25 mA, limited |\n'),
    ("scripts/layout.py",
     '    "INPUTS: ±12 V.  OUT: ±13 V into 1k or more; a short",\n'
     '    "   to ground or a rail is survived, not enjoyed.",\n',
     '    "INPUTS: ±12 V.  OUT: ±12 V into 1k, 15 mA; a short to",\n'
     '    "   ground is survived, to a rail only for seconds.",\n'),
    ("scripts/gen_sch.py",
     '          "op-amp does, so a short to a rail or ground is survived."],\n',
     '          "op-amp does: a short to ground is survived, to a rail for seconds."],\n'),
    ("docs/DESIGN_NOTES.md",
     '4. **A shorted output held for minutes.**  The limit holds Q4 or Q5 at about\n'
     '   22 mA with 15 V across it, 0.3 W in a SOT-23: it survives a student\'s slip,\n'
     '   not an afternoon.\n',
     '4. **A shorted output held for minutes.**  The limit holds Q4 or Q5 at about\n'
     '   14.5 mA (22 mA reaches the short, the rest through the sense transistor): to\n'
     '   ground that is 0.21 W in a SOT-23 whose stocked part (C20526) is rated 0.2 W\n'
     '   at 625 K/W, so minutes; to either rail it is 0.43 W, twice the rating: it\n'
     '   survives a student\'s slip, not a minute.\n'),
    # ------------------------------------------------- F5: the cable-capacitance story ----
    ("docs/DESIGN_NOTES.md",
     '3. **Oscillation at a few MHz** when a long unterminated cable hangs on OUT (a\n'
     '   metre of coax is 100 pF on the follower\'s output).  The 55 degrees of margin is\n'
     '   the simulation\'s; the real board has less.  Rev B puts 47 ohm in series with\n'
     '   the OUT jack.\n',
     '3. **Less phase margin than the models say.**  The 51 degrees as a follower is\n'
     '   the simulation\'s; the real board has less, and a 10x probe (15 pF) on Q3 C\n'
     '   or Q2 C takes the model to 39 or 35 degrees, both probes to 25.  Cable\n'
     '   capacitance on OUT is not the problem: with the 47 ohm sense resistors\n'
     '   between the emitters and OUT, 100 pF of coax raises the margin to 90\n'
     '   degrees and 10 nF still leaves 30.\n'),
    ("docs/DESIGN_NOTES.md",
     '* 47 ohm in series with OUT at the jack (cable capacitance).\n',
     ''),
    ("docs/HANDBOOK.md",
     '| 9L.3 capacitive loads, 9L.4 buffer in the loop | yes | 55 degrees of phase margin to lose |\n',
     '| 9L.3 capacitive loads, 9L.4 buffer in the loop | yes | 51 degrees of phase margin to lose; a probe on Q3 C costs 12 of them |\n'),
    # ------------------------------------------------------------- F6: stale text ----
    ("docs/DESIGN_NOTES.md",
     '1. **The six SOT-23s fitted a half turn round.**',
     '1. **The eight SOT-23s fitted a half turn round.**'),
    ("docs/HANDBOOK.md",
     '1. Look at it.  Six transistors with their lone pad on the collector side (up for\n'
     '   Q1, Q3, Q4, Q5; down for Q2 and Q6), the diode bands where the silkscreen bars\n',
     '1. Look at it.  Eight transistors with their lone pad on the collector side (up\n'
     '   for Q1, Q3, Q4, Q5, Q7, Q8; down for Q2 and Q6), the diode bands where the silkscreen bars\n'),
    ("docs/HANDBOOK.md",
     '| PUSH-PULL FOLLOWER x1 | Q4, Q5, R15, R16 |',
     '| PUSH-PULL FOLLOWER | Q4, Q5, R15, R16 |'),
    ("scripts/parts.py",
     '"does nothing instead of forward-biasing six transistors. "',
     '"does nothing instead of forward-biasing eight transistors. "'),
    ("scripts/parts.py",
     '"+/-37 mV referred to the input"',
     '"+/-33 mV referred to the input"'),
    ("scripts/check_circuit.py",
     '"RV1 is 50 ohm: 25 ohm per emitter at centre, +/-19 mV of null"',
     '"RV1 is 50 ohm: 25 ohm per emitter at centre, +/-33 mV of null"'),
    ("scripts/check_circuit.py",
     '          "R1 and R2 are 1206: a rail on an input puts 0.2 W in them")\n',
     '          "R1 and R2 are 1206: the two inputs at opposite rails put 0.21 W in each")\n'),
    ("scripts/check_circuit.py",
     '    for q, kind in (("Q1", "2N3904"), ("Q2", "2N3904"), ("Q3", "2N3906"),\n'
     '                    ("Q4", "2N3904"), ("Q5", "2N3906"), ("Q6", "2N3904")):\n',
     '    for q, kind in (("Q1", "2N3904"), ("Q2", "2N3904"), ("Q3", "2N3906"), ("Q4", "2N3904"),\n'
     '                    ("Q5", "2N3906"), ("Q6", "2N3904"), ("Q7", "2N3904"), ("Q8", "2N3906")):\n'),
    ("README.md", "the 98 circuit assertions", "the 102 circuit assertions"),
    ("scripts/gen_sch.py",
     '          "PNP of Chapter 4 as six SOT-23 transistors, on a board whose silkscreen is this drawing.",\n',
     '          "PNP of Chapter 4 as eight SOT-23 transistors, on a board whose silkscreen is this drawing.",\n'),
    ("scripts/gen_sch.py",
     '          "A 2.54 mm pin on every node named on the sheet;",\n'
     '          "a scope hook grabs it.  Three pairs of ground",\n'
     '          "pins for the clip."],\n',
     '          "A wire loop on every node named on the sheet;",\n'
     '          "a scope hook grabs it.  Four ground loops for",\n'
     '          "the clip."],\n'),
    ("docs/DESIGN_NOTES.md",
     '**Gain.** Stage 1 gives 11.1 at Q2 C, stage 2 gives 12.5 at Q3 C loaded as it is\n'
     '(12 k against Q3\'s Early resistance and the push-pull\'s input), and the\n'
     'push-pull at rest is barely conducting, so the small-signal open-loop gain at\n',
     '**Gain.** Stage 1 gives 11.1 at Q2 C, stage 2 gives 34 at Q3 C, and the\n'
     'push-pull at rest is barely conducting (its small-signal gain at the quiescent\n'
     'point is 0.37, the dead band), so the small-signal open-loop gain at\n'),
    ("docs/DESIGN_NOTES.md",
     'The 1206 resistors take 0.14 W when an input is held at a rail |',
     'The 1206 resistors take 50 mW each with one input at a rail and the other grounded, 0.21 W each with the two inputs at opposite rails |'),
    ("scripts/gen_docs.py",
     '        ("Edge Rails/Fiducials", "Added by JLCPCB", "the board carries no fiducials; let them add rails with fiducials, removed before delivery"),\n',
     '        ("Edge Rails/Fiducials", "Added by JLCPCB", "the board has three 1 mm fiducials in its corners; let them add rails anyway, removed before delivery"),\n'),
    ("scripts/gen_outputs.py",
     '  pads is electrically right; the sliders should move toward the side the\n  silkscreen "1"/"2" legends sit on.',
     "  pads is electrically right; the part's own ON marking goes on the side of\n  the silkscreen word ON beside each switch (left of SW1, above SW2; the 'ON>' above SW3's right-hand pads points at it)."),
]

for rel, old, new in EDITS:
    path = os.path.join(P, rel)
    s = open(path, encoding="utf-8").read()
    n = s.count(old)
    if n != 1:
        sys.exit(f"{rel}: expected 1 occurrence, found {n}:\n{old}")
    open(path, "w", encoding="utf-8").write(s.replace(old, new))
    print(f"  edited {rel}: {old.strip().splitlines()[0][:60]!r}")
print(f"{len(EDITS)} edits applied")
