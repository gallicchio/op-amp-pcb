"""The board, as a drawing: where every part sits and where every wire runs.

The board is the schematic.  Signal flows left to right: the two inputs on the
left edge, the differential pair, the gain stage, the push-pull, the output on
the right edge; +15 V along the top, -15 V along the bottom, power in at the
bottom-right corner.  Every transistor stands where the book's Fig. 5L.15
draws it and every wire here is laid as copper AND drawn on the silkscreen, so
what the student sees is the circuit.

Coordinates are millimetres from the board's top-left corner, y down.
Rotations are KiCad's, degrees counter-clockwise.

  SOT-23 at rot 90:  C on top, B bottom-left, E bottom-right: every
                     transistor whose base comes from the left (Q1, Q3-Q6).
                     A PNP's emitter then leaves to the right and goes up,
                     its collector goes down between the two bottom pads.
  SOT-23 at rot 270: B top-right, E top-left, C bottom: Q2, whose base
                     comes from the right; its collector goes up between
                     the two top pads, its emitter left and down.
  0805/1206 at rot 270: pad 1 on top; at rot 90: pad 1 at the bottom;
  at rot 0 pad 1 on the left.
  SOD-123 at rot 270: cathode (pad 1) on top; rot 90: cathode at the bottom.
  DIP switch at rot 0: pads 1, 2 on the left, 4, 3 on the right (pole 1 =
  1-4 top, pole 2 = 2-3 bottom); rot 180 swaps left and right; rot 90 turns
  it so pole 1 is the left column (4 top, 1 bottom) and pole 2 the right.

A wire is (net, [point, ...], width); a point is (x, y) or ("REF", "pad"),
which the board generator resolves to that pad's centre after placement and
checks is on the named net.  Three segments cross other wires and dive under
them on the back layer between two vias (HOPS); the silkscreen draws hops.
"""
import parts

BOARD_W, BOARD_H = 100.0, 100.0
VP_Y, VM_Y = 15.0, 84.0          # the rails
FB_Y = 9.0                       # the feedback return along the top

# ------------------------------------------------------------ placement ----
PLACE = {
    # left edge: inputs
    "J4": (4.5, 22.0, 90),      # IN- / GND screw terminal, wires leave to the left
    "J1": (6.0, 36.0, 180),     # IN- BNC
    "J2": (6.0, 58.0, 180),     # IN+ BNC
    "J5": (4.5, 72.0, 90),      # IN+ / GND screw terminal
    "R1": (18.0, 36.0, 0), "R2": (18.0, 58.0, 0),
    "D1": (21.5, 47.0, 90), "D2": (24.5, 47.0, 270),
    # the differential pair
    "Q1": (33.0, 35.06, 90), "Q2": (47.0, 35.06, 270),
    "R3": (47.0, 24.0, 270),
    "RV1": (40.5, 46.0, 180),
    # the tail: the switch mirrored, so the 10k leaves to the left and the
    # sink sits under the switch
    "SW1": (40.5, 61.0, 180),
    "R4": (31.5, 70.0, 270),
    "Q6": (38.0, 68.5, 270), "R7": (35.6, 77.5, 270),
    "R5": (46.3, 71.0, 90), "R6": (43.5, 78.0, 270),
    # the gain stage and its compensation
    "Q3": (60.0, 30.0, 90), "R8": (65.0, 20.0, 270), "R9": (60.0, 72.0, 270),
    "SW2": (54.77, 44.5, 90), "R14": (53.5, 53.5, 270), "C1": (53.5, 58.5, 270),
    # the push-pull, the output divider and the feedback selector
    "Q4": (74.6, 37.0, 90), "Q5": (74.6, 51.0, 90),
    "R10": (80.0, 38.5, 90), "R11": (80.0, 29.8, 90),
    "SW3": (84.5, 31.0, 90),
    # right edge: output and power
    "J3": (94.0, 44.0, 0),      # OUT BNC
    "J7": (95.5, 58.0, 270),    # OUT / GND screw terminal
    "J6": (95.5, 84.0, 270),    # +15 / GND / -15 screw terminal
    "D3": (87.5, 74.0, 270), "D4": (89.0, 87.0, 90),
    "C2": (24.0, 18.0, 270), "C3": (27.5, 18.0, 270),
    "C4": (24.0, 80.0, 270), "C5": (27.5, 80.0, 270),
    "R12": (76.9, 18.0, 0), "LED1": (80.5, 18.0, 180),
    "R13": (79.0, 88.0, 180), "LED2": (83.0, 88.0, 0),
    # probe loops, each on its wire
    "TP1": (27.5, 36.0, 90),    # IN- (after the 1k)
    "TP2": (35.0, 52.0, 0),     # IN+ (after the 1k)
    "TP3": (40.5, 55.0, 90),    # TAIL
    "TP4": (35.6, 73.5, 90),    # Q6 E
    "TP5": (43.5, 74.0, 90),    # Q6 B
    "TP6": (51.8, 30.94, 90),   # C2
    "TP7": (65.0, 24.0, 90),    # E3
    "TP8": (64.0, 44.0, 0),     # C3
    "TP9": (80.5, 44.0, 0),     # OUT
    "TP10": (79.6, 34.3, 90),   # X
    "TP11": (66.0, VP_Y, 0),    # +15V
    "TP12": (66.0, VM_Y, 0),    # -15V
    "TP13": (33.95, 41.2, 90),  # Q1 E
    "TP14": (44.5, 40.0, 0),    # Q2 E
    "TP100": (27.5, 44.0, 90), "TP101": (36.0, 87.5, 0), "TP102": (92.0, 70.0, 90),
    "MH1": (4.0, 4.0, 0), "MH2": (96.0, 4.0, 0), "MH3": (4.0, 96.0, 0), "MH4": (96.0, 96.0, 0),
}

# ---------------------------------------------------------------- wires ----
W_SIG, W_RAIL = 0.35, 0.6

WIRES = [
    # +15 V rail and everything that hangs from it
    ("+15V", [(24.0, VP_Y), (87.5, VP_Y)], W_RAIL),
    ("+15V", [("Q1", "3"), (33.0, VP_Y)], W_SIG),
    ("+15V", [("R3", "1"), (47.0, VP_Y)], W_SIG),
    ("+15V", [("R8", "1"), (65.0, VP_Y)], W_SIG),
    ("+15V", [("Q4", "3"), (74.6, VP_Y)], W_SIG),
    ("+15V", [("C2", "1"), (24.0, VP_Y)], W_SIG),
    ("+15V", [("C3", "1"), (27.5, VP_Y)], W_SIG),
    ("+15V", [("R12", "1"), (75.95, VP_Y)], W_SIG),
    ("+15V", [("D3", "1"), (87.5, 46.5), (87.5, 41.5), (87.5, VP_Y)], W_RAIL),
    # -15 V rail
    ("-15V", [(24.0, VM_Y), (89.0, VM_Y)], W_RAIL),
    ("-15V", [("R4", "2"), (31.5, VM_Y)], W_SIG),
    ("-15V", [("R6", "2"), (43.5, VM_Y)], W_SIG),
    ("-15V", [("R7", "2"), (35.6, VM_Y)], W_SIG),
    ("-15V", [("R9", "2"), (60.0, VM_Y)], W_SIG),
    ("-15V", [("Q5", "3"), (74.6, VM_Y)], W_SIG),
    ("-15V", [("C4", "2"), (24.0, VM_Y)], W_SIG),
    ("-15V", [("C5", "2"), (27.5, VM_Y)], W_SIG),
    ("-15V", [("R13", "2"), (78.09, VM_Y)], W_SIG),
    ("-15V", [("D4", "2"), (89.0, VM_Y)], W_RAIL),
    # power entry
    ("/+15V_IN", [("J6", "1"), (87.5, 79.0), ("D3", "2")], W_RAIL),
    ("/-15V_IN", [("J6", "3"), (89.0, 89.0), ("D4", "1")], W_RAIL),
    # inputs
    ("/IN-", [("J1", "1"), ("R1", "1")], W_SIG),
    ("/IN-", [("J4", "1"), (12.5, 24.5), (12.5, 36.0)], W_SIG),
    ("/IN-", [("SW3", "3"), (85.77, 25.0), (84.5, 25.0), (84.5, 17.5), (84.5, 12.5), (84.5, FB_Y),
              (14.5, FB_Y), (14.5, 36.0)], W_SIG),
    ("/IN-", [("SW3", "4"), (83.23, 25.0), (84.5, 25.0)], W_SIG),
    ("/Q1 B", [("R1", "2"), ("Q1", "1")], W_SIG),
    ("/Q1 B", [("D1", "2"), (21.5, 36.0)], W_SIG),
    ("/Q1 B", [("D2", "1"), (24.5, 36.0)], W_SIG),
    ("/IN+", [("J2", "1"), ("R2", "1")], W_SIG),
    ("/IN+", [("J5", "1"), (12.5, 74.5), (12.5, 58.0)], W_SIG),
    ("/Q2 B", [("R2", "2"), (28.0, 58.0), (28.0, 52.0), (38.5, 52.0), (42.5, 52.0), (50.0, 52.0),
             (50.0, 34.12), ("Q2", "1")], W_SIG),
    ("/Q2 B", [("D1", "1"), (21.5, 58.0)], W_SIG),
    ("/Q2 B", [("D2", "2"), (24.5, 58.0)], W_SIG),
    # the pair's emitters, the null trimmer, the tail
    ("Net-(Q1-E)", [("Q1", "2"), (33.95, 44.73), ("RV1", "3")], W_SIG),
    ("Net-(Q2-E)", [("Q2", "2"), (44.5, 34.12), (44.5, 44.73), ("RV1", "1")], W_SIG),
    ("/TAIL", [("RV1", "2"), (40.5, 58.0), (44.9, 58.0), ("SW1", "2"), ("SW1", "1")], W_SIG),
    ("Net-(R4-Pad1)", [("SW1", "3"), (31.5, 59.73), ("R4", "1")], W_SIG),
    ("Net-(Q6-C)", [("SW1", "4"), (36.1, 63.6), (38.0, 63.6), ("Q6", "3")], W_SIG),
    ("Net-(Q6-B)", [("Q6", "1"), (43.5, 67.56), ("R6", "1")], W_SIG),
    ("Net-(Q6-B)", [(43.5, 67.56), (46.3, 67.56), ("R5", "2")], W_SIG),
    ("Net-(Q6-E)", [("Q6", "2"), (35.6, 67.56), ("R7", "1")], W_SIG),
    # the gain stage
    ("/Q2 C", [("R3", "2"), ("Q2", "3")], W_SIG),
    ("/Q2 C", [(47.0, 30.94), ("Q3", "1")], W_SIG),
    ("/Q2 C", [(53.5, 30.94), ("SW2", "4")], W_SIG),
    ("Net-(Q3-E)", [("Q3", "2"), (65.0, 30.94), ("R8", "2")], W_SIG),
    ("/Q3 C", [("Q3", "3"), (60.0, 44.0), (60.0, 61.5), ("R9", "1")], W_SIG),
    ("/Q3 C", [(60.0, 44.0), (70.0, 44.0), (70.0, 37.94), ("Q4", "1")], W_SIG),
    ("/Q3 C", [(70.0, 44.0), (70.0, 51.94), ("Q5", "1")], W_SIG),
    ("/Q3 C", [("C1", "2"), (53.5, 61.5), (60.0, 61.5)], W_SIG),
    # compensation
    ("Net-(R14-Pad1)", [("SW2", "1"), ("R14", "1")], W_SIG),
    ("Net-(R14-Pad1)", [("SW2", "2"), (56.04, 51.0), (53.5, 51.0)], W_SIG),
    ("Net-(C1-Pad1)", [("R14", "2"), ("C1", "1")], W_SIG),
    ("Net-(C1-Pad1)", [("SW2", "3"), (58.3, 40.1), (58.3, 56.0), (53.5, 56.0)], W_SIG),
    # push-pull output, divider, feedback selector
    ("/OUT", [("Q4", "2"), (75.55, 44.0)], W_SIG),
    ("/OUT", [("Q5", "2"), (75.55, 44.0)], W_SIG),
    ("/OUT", [(75.55, 44.0), ("J3", "1")], W_SIG),
    ("/OUT", [(80.0, 44.0), ("R10", "1")], W_SIG),
    ("/OUT", [(85.77, 44.0), ("SW3", "2")], W_SIG),
    ("/OUT", [("J7", "1"), (94.0, 54.0), (94.0, 44.0)], W_SIG),
    ("/X", [("R10", "2"), (80.0, 35.4), ("SW3", "1")], W_SIG),
    ("/X", [("R11", "1"), (80.0, 35.4)], W_SIG),
    # the lamps
    ("Net-(LED1-A)", [("R12", "2"), ("LED1", "2")], W_SIG),
    ("Net-(LED2-K)", [("R13", "1"), ("LED2", "1")], W_SIG),
]

# Segments that run on the back layer, between two vias: (net, start, end).
HOPS = [
    ("/Q2 B", (38.5, 52.0), (42.5, 52.0)),      # IN+ dives under the tail
    ("+15V", (87.5, 46.5), (87.5, 41.5)),     # the +15 feed dives under OUT
    ("/IN-", (84.5, 17.5), (84.5, 12.5)),     # the feedback return dives under the +15 rail
]

# Ground: a short stub from the pad to a via, drawn with a ground symbol.
GND_STUBS = [
    (("J4", "2"), (9.8, 19.5)), (("J5", "2"), (9.8, 69.5)),
    (("J7", "2"), (91.0, 60.5)), (("J6", "2"), (91.2, 84.0)),
    (("C2", "2"), (24.0, 21.5)), (("C3", "2"), (27.5, 21.5)),
    (("C4", "1"), (24.0, 76.5)), (("C5", "1"), (27.5, 76.5)),
    (("LED1", "1"), (83.5, 18.0)), (("LED2", "2"), (85.6, 88.0)),
    (("R11", "2"), (80.0, 26.8)), (("R5", "1"), (46.3, 74.5)),
    (("TP100", "1"), (27.5, 47.5)), (("TP101", "1"), (33.0, 87.5)), (("TP102", "1"), (92.0, 73.5)),
]
# Through-hole ground posts the plane reaches directly, with where to draw the symbol.
GND_MARKS = [(10.0, 40.0), (10.0, 62.0), (90.0, 48.0)]

# --------------------------------------------------------- silkscreen -----
# Transistors: ref -> (kind, base side).  The symbol is drawn round the SOT-23.
TRANSISTORS = {
    "Q1": ("NPN", "left"), "Q2": ("NPN", "right"), "Q6": ("NPN", "right"),
    "Q3": ("PNP", "left"), "Q4": ("NPN", "left"), "Q5": ("PNP", "left"),
}
Q_RADIUS = 2.9
# where each transistor's name and type go: (x, y, justify)
Q_CAPTION = {
    "Q1": (34.0, 30.0, "left"), "Q2": (45.6, 29.4, "right"), "Q3": (54.3, 33.0, "left"),
    "Q4": (70.5, 40.6, "left", 0.8), "Q5": (73.4, 55.3, "right"), "Q6": (40.9, 65.0, "left"),
}

# Free text: (x, y, text, size, thickness, justify, angle)
TEXTS = [
    # identity, in the band under the -15 V rail
    (48.0, 90.3, "LAoE  DISCRETE OP-AMP", 2.4, 0.4, "center", 0),
    (48.0, 93.3, "a 3-stage op-amp from six discrete transistors, after Learning the Art of Electronics", 1.0, 0.15, "center", 0),
    (48.0, 95.3, "circuit: Hayes & Horowitz    board: Jason Gallicchio and Claude    rev " + parts.REV + "  " + parts.BOARD_DATE, 1.0, 0.15, "center", 0),
    (48.0, 97.3, parts.PROJECT_URL, 1.0, 0.15, "center", 0),
    # the switches, in the band above the +15 V rail
    (30.0, 10.0, "FEEDBACK SW3:  1 on = X to IN- (gain of 11)    2 on = OUT to IN- (follower)", 0.8, 0.15, "left", 0),
    (30.0, 11.5, "both off = bare op-amp: wire your own feedback to the OUT, IN- and GND terminals", 0.8, 0.15, "left", 0),
    (32.0, 13.0, "usual settings: TAIL 1 on (Q6 current source), COMPENSATION 1 on (100 pF + 1k)", 0.8, 0.15, "left", 0),
    # connectors
    (3.0, 28.9, "IN-", 1.6, 0.3, "left", 0),
    (3.0, 50.9, "IN+", 1.6, 0.3, "left", 0),
    (15.2, 26.0, "+/-12 V max", 0.9, 0.15, "left", 0),
    (15.2, 65.2, "+/-12 V max", 0.9, 0.15, "left", 0),
    (91.5, 36.8, "OUT", 1.6, 0.3, "left", 0),
    (82.5, 48.0, "+/-13 V", 0.9, 0.15, "center", 0),
    (82.5, 49.5, "10 mA", 0.9, 0.15, "center", 0),
    (11.0, 22.8, "IN-", 0.9, 0.15, "left", 0),
    (12.0, 17.6, "GND", 0.9, 0.15, "right", 0),
    (13.0, 73.3, "IN+", 0.9, 0.15, "left", 0),
    (12.0, 67.6, "GND", 0.9, 0.15, "right", 0),
    (91.0, 54.3, "OUT", 0.9, 0.15, "right", 0),
    (91.0, 59.0, "GND", 0.9, 0.15, "right", 0),
    (91.4, 77.3, "+15V", 0.9, 0.15, "right", 0),
    (91.4, 82.3, "GND", 0.9, 0.15, "right", 0),
    (91.4, 90.3, "-15V", 0.9, 0.15, "right", 0),
    (93.5, 93.2, "POWER", 1.0, 0.2, "center", 0),
    # rails
    (24.0, 13.1, "+15 V", 1.2, 0.2, "left", 0),
    (24.0, 86.3, "-15 V", 1.2, 0.2, "left", 0),
    (74.0, 86.3, "-15 V", 1.2, 0.2, "right", 0),
    # bypass capacitors, named in pairs beside the pair
    (21.4, 17.3, "C2 10uF", 0.8, 0.15, "right", 0),
    (21.4, 18.7, "C3 100nF", 0.8, 0.15, "right", 0),
    (21.4, 79.3, "C4 10uF", 0.8, 0.15, "right", 0),
    (21.4, 80.7, "C5 100nF", 0.8, 0.15, "right", 0),
    # the switches' poles, the knob, the sink
    (36.5, 46.0, "OFFSET", 0.9, 0.15, "right", 0),
    (36.5, 47.4, "NULL", 0.9, 0.15, "right", 0),
    (36.5, 48.8, "RV1", 0.8, 0.15, "right", 0),
    (37.5, 56.6, "SW1", 0.8, 0.15, "center", 0),
    (46.6, 59.7, "2: 10k", 0.8, 0.15, "left", 0),
    (46.6, 62.3, "1: Q6", 0.8, 0.15, "left", 0),
    (33.6, 74.6, "CURRENT SOURCE", 0.9, 0.15, "center", 90),
    (48.4, 70.3, "R5", 0.8, 0.15, "left", 0),
    (48.4, 71.7, "62k", 0.8, 0.15, "left", 0),
    (32.9, 64.8, "R4", 0.8, 0.15, "left", 0),
    (32.9, 66.1, "10k", 0.8, 0.15, "left", 0),
    (54.2, 37.7, "SW2", 0.8, 0.15, "left", 0),
    (65.9, 50.4, "COMPENSATION", 0.9, 0.15, "center", 90),
    (60.5, 56.2, "1: 100pF", 0.8, 0.15, "left", 0),
    (60.5, 57.65, "   + 1k", 0.8, 0.15, "left", 0),
    (60.5, 59.1, "2: no 1k", 0.8, 0.15, "left", 0),
    # the clamp and the power diodes
    (20.2, 44.0, "D1 D2", 0.8, 0.15, "right", 0),
    (20.2, 45.4, "1N4148W", 0.8, 0.15, "right", 0),
    (87.3, 92.5, "D4 B5819W", 0.8, 0.15, "center", 0),
]

LEGENDS = []

# Reference designators and values: (dx, dy) of each relative to the part.
FIELD_AT = {
    "R1": ((0, -2.2), (0, 2.1)), "R2": ((0, -2.2), (0, 2.1)),
    "R3": ((-2.6, -0.7), (-2.6, 0.7)),
    "R6": ((2.4, -0.7), (2.4, 0.7)), "R7": ((2.4, -0.7), (2.4, 0.7)),
    "R8": ((-2.6, -0.7), (-2.6, 0.7)), "R9": ((-2.6, -0.7), (-2.6, 0.7)),
    "R10": ((2.4, 0.8), (2.4, 2.2)), "R11": ((-2.4, -3.8), (-2.4, -2.4)),
    "R12": ((0, 1.9), (0, 3.3)), "R13": ((0, 1.9), (0, 3.3)),
    "R14": ((1.5, -0.7), (1.5, 0.7)), "C1": ((1.5, -0.7), (1.5, 0.7)),
    "D3": ((-2.6, -0.7), (-2.6, 0.7)),
    "LED1": ((0, 1.9), (0, 3.3)), "LED2": ((0, 1.9), (0, 3.3)),
}
# Parts whose reference or value is printed as free text instead, or not at all.
HIDE_REF = {"J1", "J2", "J3", "J4", "J5", "J6", "J7", "SW1", "SW2", "SW3", "D1", "D2", "D4",
            "RV1", "R4", "R5", "C2", "C3", "C4", "C5"}
HIDE_VALUE = {"SW1", "SW2", "SW3", "J1", "J2", "J3", "J4", "J5", "J6", "J7", "RV1", "D1", "D2", "D4",
              "R4", "R5", "C2", "C3", "C4", "C5"}

# Where each probe loop's name goes, relative to the loop: (dx, dy, justify).
TP_LABEL = {
    "TP1": (0, -3.0, "center"), "TP2": (0, 2.6, "center"), "TP3": (2.0, 0.0, "left"),
    "TP4": (2.1, 0.0, "left"), "TP5": (2.0, 0.0, "left"), "TP6": (-0.3, -3.0, "center"),
    "TP7": (-2.0, -1.7, "right"), "TP8": (0, -2.2, "center"), "TP9": (0, 2.6, "center"),
    "TP10": (-2.0, 0.0, "right"), "TP11": None, "TP12": None,     # loops on the labelled rails
    "TP13": (2.0, 0.0, "left"), "TP14": (-2.2, 0.0, "right"),
    "TP100": (0, -3.0, "center"), "TP101": (2.6, 0.0, "left"), "TP102": (2.0, 0.0, "left"),
}

# Dashed boxes round the stages, named as the book names them:
# (x0, y0, x1, y1, [(title line, x, y[, size]), ...]); titles are short lines that dodge the wires.
BOXES = [
    (13.5, 29.0, 25.5, 63.5, [("INPUT", 15.0, 30.4), ("PROTECTION", 15.0, 32.0)]),
    (29.6, 18.5, 49.6, 50.5, [("DIFFERENCE", 34.8, 20.1), ("AMPLIFIER", 34.8, 21.9), ("x11", 34.8, 23.7)]),
    (29.6, 57.5, 51.8, 82.5, [("TAIL", 30.1, 58.6)]),
    (54.0, 18.5, 67.6, 35.4, [("GAIN", 54.5, 20.1), ("STAGE", 54.5, 21.9), ("x30", 54.5, 23.7)]),
    (52.2, 36.6, 67.0, 63.0, []),
    (67.5, 28.3, 78.0, 58.0, [("PUSH-", 68.0, 29.6), ("PULL", 68.0, 31.0), ("FOLLOWER", 68.0, 32.3, 0.8), ("x1", 68.0, 33.6)]),
]

# Fiducials for the pick-and-place camera: 1 mm copper dots in a 2 mm mask
# opening, three corners, clear of the mounting holes and the title band.
FIDUCIALS = [(11.0, 7.0), (89.0, 7.0), (11.0, 92.0)]

# The QR code on the back: its centre and module size.
QR_AT, QR_MODULE = (68.0, 30.0), 0.6

# Printed on the back, where there are no parts: how to use the board.  Each
# line is short enough to stay between x = 30 and x = 85, clear of every
# through-hole pad (the silkscreen may cross tented vias).
BACK_Y, BACK_PITCH = 48.0, 1.9
BACK_TEXT = [
    "The op-amp of Learning the Art of Electronics",
    "(Hayes & Horowitz, 2016), built from six",
    "2N3904 / 2N3906 so you can probe every node.",
    "",
    "POWER: +15 V, GND, -15 V into the terminal, 20 mA.",
    "   Both green LEDs light when it is right way round.",
    "SWITCHES, usual: TAIL 1 on (Q6 current source),",
    "   COMPENSATION 1 on (100 pF + 1k), FEEDBACK as needed.",
    "   TAIL 2 = 10k tail resistor instead.",
    "   COMPENSATION 2 shorts the 1k: the book's bare",
    "   100 pF; the x11 amp still works, a follower rings.",
    "FEEDBACK 1 = X to IN-: gain 11.  2 = OUT to IN-:",
    "   follower.  Both off: it is a bare op-amp.",
    "AS AN OP-AMP IN YOUR OWN CIRCUIT (Labs 6-9): FEEDBACK",
    "   both off; IN-, IN+, OUT and GND on the terminals",
    "   are pins 2, 3, 6 of a '411.  Mind its 2 uA of input",
    "   bias current (no 10 M feedback) and its unprotected",
    "   output (loads of 1k and up).",
    "OFFSET NULL: as a follower with IN+ grounded,",
    "   turn RV1 until OUT reads 0 V.",
    "INPUTS: +/-12 V.  OUT: +/-13 V into 1k or more;",
    "   never short OUT to a rail.",
    "PROBING: a loop on every named node for a scope",
    "   hook, and GND loops for the clip.",
]
