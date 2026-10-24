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
    "Q1": (33.4, 35.06, 90), "Q2": (46.0, 35.06, 270),
    "R3": (46.0, 24.0, 270),
    "RV1": (40.5, 46.0, 180),
    # the tail: the switch mirrored, so the 10k leaves to the left and the
    # sink sits under the switch
    "SW1": (40.5, 61.0, 180),
    "R4": (31.5, 70.0, 270),
    "Q6": (38.0, 68.5, 270), "R7": (38.4, 79.5, 270),
    "R5": (46.3, 71.0, 90), "R6": (43.5, 78.0, 270),
    # the gain stage and its compensation
    "Q3": (60.0, 30.0, 90), "R8": (65.0, 20.0, 270), "R9": (60.0, 72.0, 270),
    "SW2": (54.77, 44.5, 90), "R14": (53.5, 53.5, 270), "C1": (53.5, 58.5, 270),
    # the push-pull with its emitter sense resistors
    "Q4": (74.6, 36.0, 90), "Q5": (74.6, 60.5, 90),
    "R15": (74.2, 40.8, 270), "R16": (74.2, 46.0, 270),
    # the output current limit: Q7 / D5 above the OUT line, Q8 / D6 below
    "Q7": (82.3, 38.36, 90), "D5": (82.3, 32.3, 90),
    "Q8": (82.3, 56.0, 90), "D6": (82.3, 63.5, 90),
    # the output divider, hanging down from OUT, and the feedback selector
    "R10": (86.2, 47.5, 270), "R11": (86.2, 69.5, 270),
    "SW3": (81.5, 73.0, 270),
    # right edge: output and power
    "J3": (94.3, 44.0, 0),      # OUT BNC
    "J7": (95.5, 58.0, 270),    # OUT / GND screw terminal
    "J6": (95.5, 82.0, 270),    # +15 / GND / -15 screw terminal
    "D3": (88.5, 74.0, 270), "D4": (84.3, 87.0, 180),
    "C2": (24.0, 18.0, 270), "C3": (27.5, 18.0, 270),
    "C4": (24.0, 80.0, 270), "C5": (27.5, 80.0, 270),
    # the lamps hang from the rails toward ground, like the bypass capacitors
    "R12": (93.0, 18.0, 270), "LED1": (93.0, 22.5, 90),
    "R13": (70.0, 81.0, 270), "LED2": (70.0, 76.5, 90),
    # probe loops, each on its wire
    "TP1": (26.8, 36.0, 90),    # IN- (after the 1k)
    "TP2": (26.8, 58.0, 90),    # IN+ (after the 1k), the mirror of TP1
    "TP3": (40.5, 55.0, 90),    # TAIL
    "TP4": (38.4, 74.8, 90),    # Q6 E
    "TP5": (43.5, 74.0, 90),    # Q6 B
    "TP6": (51.75, 30.94, 90),  # Q2 C
    "TP7": (65.0, 24.0, 90),    # Q3 E
    "TP8": (64.0, 44.0, 0),     # Q3 C
    "TP9": (93.3, 50.9, 0),     # OUT, beside the jack
    "TP11": (66.0, VP_Y, 0),    # +15V
    "TP12": (66.0, VM_Y, 0),    # -15V
    "TP13": (33.0, 41.2, 90),   # Q1 E
    "TP14": (46.4, 41.4, 90),   # Q2 E
    "TP100": (27.5, 44.0, 90), "TP101": (12.0, 80.0, 0), "TP102": (92.0, 68.5, 90), "TP103": (64.0, 70.0, 0),
    "MH1": (4.0, 4.0, 0), "MH2": (96.0, 4.0, 0), "MH3": (4.0, 96.0, 0), "MH4": (96.0, 96.0, 0),
}

# ---------------------------------------------------------------- wires ----
W_SIG, W_RAIL = 0.35, 0.6
QC_X = 68.8           # the push-pull's base bus (Q3's collector), left of the two circles
FEED_X = 88.5         # the +15 feed from the power corner up to the rail
RET_X = 87.3          # the feedback return (IN-) up the right side
OR_X = 78.5           # OUT down to the feedback switch

WIRES = [
    # +15 V rail and everything that hangs from it
    ("+15V", [(24.0, VP_Y), (93.0, VP_Y)], W_RAIL),
    ("+15V", [("Q1", "3"), (33.4, VP_Y)], W_SIG),
    ("+15V", [("R3", "1"), (46.0, VP_Y)], W_SIG),
    ("+15V", [("R8", "1"), (65.0, VP_Y)], W_SIG),
    ("+15V", [("Q4", "3"), (74.6, VP_Y)], W_SIG),
    ("+15V", [("C2", "1"), (24.0, VP_Y)], W_SIG),
    ("+15V", [("C3", "1"), (27.5, VP_Y)], W_SIG),
    ("+15V", [("R12", "1"), (93.0, VP_Y)], W_SIG),
    ("+15V", [("D3", "1"), (FEED_X, 46.5), (FEED_X, 41.5), (FEED_X, VP_Y)], W_RAIL),
    # -15 V rail
    ("-15V", [(24.0, VM_Y), (82.65, VM_Y)], W_RAIL),
    ("-15V", [("R4", "2"), (31.5, VM_Y)], W_SIG),
    ("-15V", [("R6", "2"), (43.5, VM_Y)], W_SIG),
    ("-15V", [("R7", "2"), (38.4, VM_Y)], W_SIG),
    ("-15V", [("R9", "2"), (60.0, VM_Y)], W_SIG),
    ("-15V", [("Q5", "3"), (74.6, VM_Y)], W_SIG),
    ("-15V", [("C4", "2"), (24.0, VM_Y)], W_SIG),
    ("-15V", [("C5", "2"), (27.5, VM_Y)], W_SIG),
    ("-15V", [("R13", "2"), (70.0, VM_Y)], W_SIG),
    ("-15V", [("D4", "2"), (82.65, VM_Y)], W_RAIL),
    # power entry
    ("/+15V_IN", [("J6", "1"), (FEED_X, 77.0), ("D3", "2")], W_RAIL),
    ("/-15V_IN", [("J6", "3"), ("D4", "1")], W_RAIL),
    # inputs
    ("/IN-", [("J1", "1"), ("R1", "1")], W_SIG),
    ("/IN-", [("J4", "1"), (12.5, 24.5), (12.5, 36.0)], W_SIG),
    ("/IN-", [("SW3", "3"), ("SW3", "4"), (RET_X, 77.5), (RET_X, 47.5), (RET_X, 40.5), (RET_X, 17.5), (RET_X, 12.5),
              (RET_X, FB_Y), (14.5, FB_Y), (14.5, 36.0)], W_SIG),
    ("/Q1 B", [("R1", "2"), ("Q1", "1")], W_SIG),
    ("/Q1 B", [("D1", "2"), (21.5, 36.0)], W_SIG),
    ("/Q1 B", [("D2", "1"), (24.5, 36.0)], W_SIG),
    ("/IN+", [("J2", "1"), ("R2", "1")], W_SIG),
    ("/IN+", [("J5", "1"), (12.5, 74.5), (12.5, 58.0)], W_SIG),
    ("/Q2 B", [("R2", "2"), (28.5, 58.0), (28.5, 52.0), (38.5, 52.0), (42.5, 52.0), (49.5, 52.0),
             (49.5, 34.12), ("Q2", "1")], W_SIG),
    ("/Q2 B", [("D1", "1"), (21.5, 58.0)], W_SIG),
    ("/Q2 B", [("D2", "2"), (24.5, 58.0)], W_SIG),
    # the pair's emitters, the null trimmer, the tail
    ("Net-(Q1-E)", [("Q1", "2"), (34.35, 37.5), (33.0, 37.5), (33.0, 44.73), ("RV1", "3")], W_SIG),
    ("Net-(Q2-E)", [("Q2", "2"), (45.05, 37.5), (46.4, 37.5), (46.4, 42.5), (43.04, 42.5), ("RV1", "1")], W_SIG),
    ("/TAIL", [("RV1", "2"), (40.5, 58.0), (44.9, 58.0), ("SW1", "2"), ("SW1", "1")], W_SIG),
    ("Net-(R4-Pad1)", [("SW1", "3"), (31.5, 59.73), ("R4", "1")], W_SIG),
    ("Net-(Q6-C)", [("SW1", "4"), (36.1, 63.6), (38.0, 63.6), ("Q6", "3")], W_SIG),
    ("Net-(Q6-B)", [("Q6", "1"), (43.5, 67.56), ("R6", "1")], W_SIG),
    ("Net-(Q6-B)", [(43.5, 67.56), (46.3, 67.56), ("R5", "2")], W_SIG),
    ("Net-(Q6-E)", [("Q6", "2"), (37.05, 70.9), (38.4, 70.9), ("R7", "1")], W_SIG),
    # the gain stage
    ("/Q2 C", [("R3", "2"), ("Q2", "3")], W_SIG),
    ("/Q2 C", [(46.0, 30.94), ("Q3", "1")], W_SIG),
    ("/Q2 C", [(53.5, 30.94), ("SW2", "4")], W_SIG),
    ("Net-(Q3-E)", [("Q3", "2"), (60.95, 27.6), (59.6, 27.6), (59.6, 24.0), (65.0, 24.0), ("R8", "2")], W_SIG),
    ("/Q3 C", [("Q3", "3"), (60.0, 44.0), (60.0, 61.5), ("R9", "1")], W_SIG),
    ("/Q3 C", [(60.0, 44.0), (QC_X, 44.0), (QC_X, 36.94), ("Q4", "1")], W_SIG),
    ("/Q3 C", [(QC_X, 44.0), (QC_X, 61.44), ("Q5", "1")], W_SIG),
    ("/Q3 C", [("C1", "2"), (53.5, 61.5), (60.0, 61.5)], W_SIG),
    # compensation
    ("Net-(R14-Pad1)", [("SW2", "1"), ("R14", "1")], W_SIG),
    ("Net-(R14-Pad1)", [("SW2", "2"), (56.04, 51.0), (53.5, 51.0)], W_SIG),
    ("Net-(C1-Pad1)", [("R14", "2"), ("C1", "1")], W_SIG),
    ("Net-(C1-Pad1)", [("SW2", "3"), (58.3, 40.1), (58.3, 56.0), (53.5, 56.0)], W_SIG),
    # push-pull: emitters through the sense resistors to OUT
    ("Net-(Q4-E)", [("Q4", "2"), (75.55, 38.4), (74.2, 38.4), ("R15", "1")], W_SIG),
    ("/OUT", [("R15", "2"), (74.2, 44.0)], W_SIG),
    ("/OUT", [("R16", "1"), (74.2, 44.0)], W_SIG),
    ("Net-(Q5-E)", [("Q5", "2"), (75.55, 58.1), (74.2, 58.1), ("R16", "2")], W_SIG),
    ("/OUT", [(74.2, 44.0), ("J3", "1")], W_SIG),
    ("/OUT", [("J7", "1"), (94.3, 54.0), (94.3, 44.0)], W_SIG),
    # the current limit: Q7 senses R15, Q8 senses R16; D5 / D6 to the base bus
    ("Net-(Q4-E)", [(74.2, 38.4), (78.0, 38.4), (78.0, 39.3), ("Q7", "1")], W_SIG),
    ("/OUT", [("Q7", "2"), (83.25, 40.76), (81.9, 40.76), (81.9, 44.0)], W_SIG),
    ("Net-(D5-K)", [("Q7", "3"), ("D5", "1")], W_SIG),
    ("/Q3 C", [("D5", "2"), (82.3, 27.0), (75.6, 27.0), (73.6, 27.0), (67.2, 27.0), (67.2, 44.0)], W_SIG),
    ("Net-(Q5-E)", [(74.2, 56.94), ("Q8", "1")], W_SIG),
    ("/OUT", [("Q8", "2"), (83.25, 53.6), (81.9, 53.6), (81.9, 44.0)], W_SIG),
    ("Net-(D6-A)", [("Q8", "3"), ("D6", "2")], W_SIG),
    ("/Q3 C", [("D6", "1"), (82.3, 66.3), (79.5, 66.3), (77.5, 66.3), (75.6, 66.3), (73.6, 66.3), (QC_X, 66.3), (QC_X, 61.44)], W_SIG),
    # the divider hangs from OUT; X goes down to the switch
    ("/OUT", [(86.2, 44.0), ("R10", "1")], W_SIG),
    ("/X", [("R10", "2"), ("R11", "1")], W_SIG),
    ("/X", [(86.2, 64.0), (84.0, 64.0), (84.0, 67.0), (82.77, 67.0), ("SW3", "1")], W_SIG),
    ("/OUT", [(OR_X, 44.0), (OR_X, 55.9), (OR_X, 57.9), (OR_X, 70.0), (80.23, 70.0),
              ("SW3", "2")], W_SIG),
    # the lamps
    ("Net-(LED1-A)", [("R12", "2"), ("LED1", "2")], W_SIG),
    ("Net-(LED2-K)", [("R13", "1"), ("LED2", "1")], W_SIG),
]

# Segments that run on the back layer, between two vias: (net, start, end).
HOPS = [
    ("/Q2 B", (38.5, 52.0), (42.5, 52.0)),        # IN+ dives under the tail
    ("+15V", (FEED_X, 46.5), (FEED_X, 41.5)),     # the +15 feed dives under OUT
    ("/IN-", (RET_X, 47.5), (RET_X, 40.5)),       # the feedback return dives under OUT
    ("/IN-", (RET_X, 17.5), (RET_X, 12.5)),       # ...and under the +15 rail
    ("/Q3 C", (75.6, 27.0), (73.6, 27.0)),        # D5's bus dives under Q4's collector feed
    ("/Q3 C", (79.5, 66.3), (77.5, 66.3)),        # D6's bus dives under OUT's drop
    ("/Q3 C", (75.6, 66.3), (73.6, 66.3)),        # ...and under Q5's collector feed
    ("/OUT", (OR_X, 55.9), (OR_X, 57.9)),         # OUT's drop dives under Q8's sense lead
]

# Ground: a stub from the pad to a via (a point, or a path of points), the
# ground symbol drawn at the via pointing the way the last segment runs.
GND_STUBS = [
    (("J4", "2"), (9.8, 19.5)), (("J5", "2"), (9.8, 69.5)),
    (("J7", "2"), [(90.8, 60.5), (90.8, 63.0)]), (("J6", "2"), [(90.6, 82.0), (90.6, 84.0)]),
    (("C2", "2"), (24.0, 21.5)), (("C3", "2"), (27.5, 21.5)),
    (("C4", "1"), (24.0, 76.5)), (("C5", "1"), (27.5, 76.5)),
    (("LED1", "1"), (93.0, 26.5)), (("LED2", "2"), (70.0, 72.5)),
    (("R11", "2"), (86.2, 74.0)), (("R5", "1"), (46.3, 74.5)),
    (("TP100", "1"), (27.5, 47.5)), (("TP101", "1"), (12.0, 83.5)), (("TP102", "1"), (92.0, 71.6)),
    (("TP103", "1"), (64.0, 73.5)),
]
# Through-hole ground posts the plane reaches directly, with where to draw the symbol.
GND_MARKS = [(10.0, 40.0), (10.0, 62.0), (90.3, 48.0)]

# --------------------------------------------------------- silkscreen -----
# Transistors: ref -> (kind, base side).  The symbol is drawn round the SOT-23.
TRANSISTORS = {
    "Q1": ("NPN", "left"), "Q2": ("NPN", "right"), "Q6": ("NPN", "right"),
    "Q3": ("PNP", "left"), "Q4": ("NPN", "left"), "Q5": ("PNP", "left"),
    "Q7": ("NPN", "left"), "Q8": ("PNP", "left"),
}
Q_RADIUS = 3.0
# where each transistor's name and type go: (x, y, justify[, size[, angle]])
Q_CAPTION = {
    "Q1": (29.9, 30.2, "left"), "Q2": (44.6, 29.4, "right"), "Q3": (54.8, 33.6, "left"),
    "Q4": (72.9, 42.3, "right", 0.8), "Q5": (72.6, 54.6, "right", 0.8), "Q6": (41.6, 65.2, "left"),
    "Q7": (83.5, 42.6, "left", 0.8), "Q8": (79.4, 60.8, "left", 0.8),
}
# the types, once, in the band (the symbols say NPN or PNP); letters that need a home of their own
Q_LETTER = {"Q2": {"B": (49.0, 32.7), "C": (44.8, 31.0)}, "Q4": {"C": (75.9, 32.3)}, "Q5": {"E": (72.7, 55.9)},
            "Q6": {"B": (42.6, 66.5), "C": (39.4, 64.95)},
            "Q7": {"B": (79.8, 35.8), "C": (83.9, 35.1)}, "Q8": {"B": (79.6, 52.9)}}

# Free text: (x, y, text, size, thickness, justify, angle)
TEXTS = [
    # identity, in the band under the -15 V rail
    (48.0, 90.3, "DISCRETE TRANSISTOR OP-AMP", 2.4, 0.4, "center", 0),
    (48.0, 93.3, "the op-amp of Learning the Art of Electronics (Hayes & Horowitz), Lab 5L", 1.0, 0.15, "center", 0),
    (48.0, 95.3, "circuit: Hayes & Horowitz    board: Jason Gallicchio and Claude    rev " + parts.REV + "  " + parts.BOARD_DATE, 1.0, 0.15, "center", 0),
    (48.0, 97.3, parts.PROJECT_URL, 1.0, 0.15, "center", 0),
    # connectors
    (3.0, 28.9, "IN-", 1.6, 0.3, "left", 0),
    (3.0, 50.9, "IN+", 1.6, 0.3, "left", 0),
    (15.2, 26.0, "±12 V max", 0.9, 0.15, "left", 0),
    (15.2, 65.2, "±12 V max", 0.9, 0.15, "left", 0),
    (91.8, 34.0, "OUT", 1.6, 0.3, "left", 0),
    (98.8, 37.4, "±13 V 20 mA", 0.8, 0.15, "right", 0),
    (11.0, 22.8, "IN-", 0.9, 0.15, "left", 0),
    (12.0, 17.6, "GND", 0.9, 0.15, "right", 0),
    (13.0, 73.3, "IN+", 0.9, 0.15, "left", 0),
    (12.0, 67.6, "GND", 0.9, 0.15, "right", 0),
    (91.6, 54.3, "OUT", 0.9, 0.15, "right", 0),
    (91.9, 65.0, "GND", 0.9, 0.15, "left", 0),
    (91.4, 78.4, "+15V", 0.9, 0.15, "right", 0),
    (89.8, 84.6, "GND", 0.9, 0.15, "right", 0),
    (91.4, 88.7, "-15V", 0.9, 0.15, "right", 0),
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
    # the trimmer, the tail switch and its sink
    (36.5, 46.0, "OFFSET", 0.9, 0.15, "right", 0),
    (36.5, 47.4, "NULL", 0.9, 0.15, "right", 0),
    (36.5, 48.8, "RV1", 0.8, 0.15, "right", 0),
    (37.5, 56.6, "SW1", 0.8, 0.15, "center", 0),
    (46.6, 59.7, "2: 10k", 0.8, 0.15, "left", 0),
    (43.8, 64.6, "1: current", 0.8, 0.15, "left", 0),
    (43.8, 65.9, "source Q6", 0.8, 0.15, "left", 0),
    (33.15, 74.6, "CURRENT SOURCE", 0.9, 0.15, "center", 90),
    (48.4, 70.3, "R5", 0.8, 0.15, "left", 0),
    (48.4, 71.7, "62k", 0.8, 0.15, "left", 0),
    (32.9, 64.8, "R4", 0.8, 0.15, "left", 0),
    (32.9, 66.1, "10k", 0.8, 0.15, "left", 0),
    # the compensation switch
    (54.2, 37.7, "SW2", 0.8, 0.15, "left", 0),
    (65.9, 50.4, "COMPENSATION", 0.9, 0.15, "center", 90),
    (60.3, 56.2, "1: 100pF", 0.8, 0.15, "left", 0),
    (60.3, 57.65, "   + 1k", 0.8, 0.15, "left", 0),
    (60.3, 59.1, "2: no 1k", 0.8, 0.15, "left", 0),
    # the feedback switch, explained beside it
    (75.9, 72.5, "FEEDBACK", 0.9, 0.15, "center", 90),
    (75.4, 79.6, "1: X to IN- (gain 11)", 0.8, 0.15, "left", 0),
    (75.4, 80.9, "2: OUT to IN- (x1)", 0.8, 0.15, "left", 0),
    (75.4, 82.2, "off: bare op-amp", 0.8, 0.15, "left", 0),
    (48.0, 87.9, "Q1 Q2 Q4 Q6 Q7 = 2N3904 NPN       Q3 Q5 Q8 = 2N3906 PNP", 0.9, 0.15, "center", 0),
    (83.4, 30.8, "D5", 0.8, 0.15, "left", 0),
    (83.4, 62.3, "D6", 0.8, 0.15, "left", 0),
    (86.6, 72.4, "D3", 0.8, 0.15, "right", 0),
    # the clamp and the limiter's parts
    (20.2, 44.0, "D1 D2", 0.8, 0.15, "right", 0),
    (20.2, 45.4, "1N4148W", 0.8, 0.15, "right", 0),
    (79.5, 22.6, "OUTPUT", 0.8, 0.15, "left", 0),
    (79.5, 23.9, "CURRENT", 0.8, 0.15, "left", 0),
    (79.5, 25.2, "LIMIT", 0.8, 0.15, "left", 0),
]

LEGENDS = []

# Reference designators and values: (dx, dy) of each relative to the part.
FIELD_AT = {
    "R1": ((0, -2.2), (0, 2.1)), "R2": ((0, -2.2), (0, 2.1)),
    "R3": ((-2.6, -0.7), (-2.6, 0.7)),
    "R6": ((2.4, -0.7), (2.4, 0.7)), "R7": ((2.4, -0.7), (2.4, 0.7)),
    "R8": ((-2.6, -0.7), (-2.6, 0.7)), "R9": ((-2.6, -0.7), (-2.6, 0.7)),
    "R12": ((2.4, -0.7), (2.4, 0.7)), "R13": ((-2.4, -0.7), (-2.4, 0.7)),
    "R14": ((1.5, -0.7), (1.5, 0.7)), "C1": ((1.5, -0.7), (1.5, 0.7)),
    "D4": ((-2.6, -1.6), (-2.6, -0.2)),
    "LED1": ((2.4, -0.7), (2.4, 0.7)), "LED2": ((-2.4, -0.7), (-2.4, 0.7)),
}
# Parts whose reference or value is printed as free text instead, or not at all.
HIDE_REF = {"J1", "J2", "J3", "J4", "J5", "J6", "J7", "SW1", "SW2", "SW3", "D1", "D2", "D3", "D5", "D6",
            "RV1", "R4", "R5", "R10", "R11", "R15", "R16", "C2", "C3", "C4", "C5"}
HIDE_VALUE = {"SW1", "SW2", "SW3", "J1", "J2", "J3", "J4", "J5", "J6", "J7", "RV1", "D1", "D2", "D3", "D5", "D6",
              "R4", "R5", "R10", "R11", "R15", "R16", "C2", "C3", "C4", "C5",
              "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"}

# Where each probe loop's name goes, relative to the loop: (dx, dy, justify).
TP_LABEL = {
    "TP1": (0.4, -3.0, "center"), "TP2": (0.4, 3.0, "center"), "TP3": (2.0, 0.0, "left"),
    "TP4": (-1.0, -2.6, "right"), "TP5": (2.0, 0.0, "left"), "TP6": (0.6, -3.0, "center"),
    "TP7": (-2.0, -1.7, "right"), "TP8": (0, -2.2, "center"), "TP9": None,
    "TP11": None, "TP12": None,     # loops on the labelled rails, and by the OUT jack
    "TP13": (1.8, 0.0, "left"), "TP14": (-1.8, 0.0, "right"),
    "TP100": (-0.3, -3.0, "center"), "TP101": (0, -2.6, "center"), "TP102": (2.0, 0.0, "left"), "TP103": (2.6, 0.0, "left"),
}

# Dashed boxes round the stages, named as the book names them:
# (x0, y0, x1, y1, [(title line, x, y[, size]), ...]); titles are short lines that dodge the wires.
BOXES = [
    (13.5, 29.0, 25.5, 63.5, [("INPUT", 15.0, 30.4), ("PROTECTION", 15.0, 32.0)]),
    (28.9, 18.5, 50.4, 50.5, [("DIFFERENCE", 34.8, 20.1), ("AMPLIFIER", 34.8, 21.9), ("x11", 34.8, 23.7)]),
    (29.6, 57.5, 51.8, 82.5, [("TAIL", 30.1, 58.6)]),
    (54.3, 18.5, 66.7, 35.4, [("GAIN", 54.8, 20.1), ("STAGE", 54.8, 21.9), ("x30", 54.8, 23.7)]),
    (52.2, 36.6, 66.7, 63.0, []),
    (67.8, 28.3, 78.0, 66.8, [("PUSH-", 68.1, 29.6), ("PULL", 68.1, 31.0), ("FOLLOWER", 68.1, 32.3, 0.8), ("x1", 68.1, 33.6)]),
    (79.0, 27.5, 85.6, 66.8, []),
    (75.0, 67.6, 91.5, 83.4, []),
]

# Fiducials for the pick-and-place camera: 1 mm copper dots in a 2 mm mask
# opening, three corners, clear of the mounting holes and the title band.
FIDUCIALS = [(11.0, 7.0), (89.0, 7.0), (11.0, 92.0)]

# The QR code on the back: its centre and module size.
QR_AT, QR_MODULE = (55.0, 30.0), 0.6

# Printed on the back, where there are no parts: how to use the board.  Each
# line is short enough to stay between x = 30 and x = 85, clear of every
# through-hole pad (the silkscreen may cross tented vias).
BACK_Y, BACK_PITCH = 48.0, 1.9
BACK_TEXT = [
    "The op-amp of Learning the Art of Electronics",
    "(Hayes & Horowitz, 2016), built from eight",
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
    "   bias current (no 10 M feedback); its output limits",
    "   at 20 mA, like a real one (Q7, Q8: not in the book).",
    "OFFSET NULL: as a follower with IN+ grounded,",
    "   turn RV1 until OUT reads 0 V.",
    "INPUTS: ±12 V.  OUT: ±13 V into 1k or more; a short",
    "   to ground or a rail is survived, not enjoyed.",
    "PROBING: a loop on every named node for a scope",
    "   hook, and GND loops for the clip.",
]
