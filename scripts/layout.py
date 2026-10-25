"""The board, as a drawing: where every part sits and where every wire runs.

The board is the schematic.  Signal flows left to right: the two inputs on the
left edge, the differential pair, the gain stage, the push-pull, the output on
the right edge; +15 V along the top, -15 V along the bottom, power in at the
bottom-right corner.  Every transistor stands where the book's Fig. 5L.15
draws it and every wire here is laid as copper AND drawn on the silkscreen, so
what the student sees is the circuit.

Coordinates are millimetres from the board's top-left corner, y down.
Rotations are KiCad's, degrees counter-clockwise.

  Each transistor sits at the centre of a drawn symbol (gen_pcb.q_geometry):
  a circle of Q_RADIUS whose base lead leaves on the base's side and whose
  collector and emitter leads leave at the top and bottom, straight above and
  below the package.  Wires therefore reach a transistor at (cx -/+ R, cy),
  (cx, cy - R) and (cx, cy + R); the copper inside follows the symbol.
  SOT-23 at rot 90:  C on top, B bottom-left, E bottom-right: every
                     transistor whose base comes from the left (Q1, Q3-Q5,
                     Q7, Q8).  For an NPN each pad is under its own lead; for
                     a PNP the collector pad is under the emitter leg and its
                     hairline runs down between the other two pads.
  SOT-23 at rot 270: B top-right, E top-left, C bottom: Q2 and Q6, whose
                     bases come from the right.
  0805/1206 at rot 270: pad 1 on top; at rot 90: pad 1 at the bottom;
  at rot 0 pad 1 on the left.
  SOD-123 at rot 270: cathode (pad 1) on top; rot 90: cathode at the bottom.
  DIP switch at rot 0: pads 1, 2 on the left, 4, 3 on the right (pole 1 =
  1-4 top, pole 2 = 2-3 bottom); rot 180 swaps left and right; rot 90 turns
  it so pole 1 is the left column (4 top, 1 bottom) and pole 2 the right.

A wire is (net, [point, ...], width); a point is (x, y) or ("REF", "pad"),
which the board generator resolves to that pad's centre (or, for a
transistor, to the end of the symbol's lead) after placement and checks is on
the named net.  A few segments cross other wires and dive under them on the
back layer between two vias (HOPS); the silkscreen draws hops as jumps.
"""
import parts

BOARD_W, BOARD_H = 100.0, 100.0
VP_Y, VM_Y = 15.0, 84.0          # the rails
FB_Y = 9.0                       # the feedback return along the top
OUT_Y = 43.0                     # the output node, level with the OUT jack's pin

# ------------------------------------------------------------ placement ----
PLACE = {
    # left edge: inputs
    "J4": (4.5, 22.0, 90),      # IN- / GND screw terminal, wires leave to the left
    "J1": (6.0, 36.0, 180),     # IN- BNC
    "J2": (6.0, 58.0, 180),     # IN+ BNC
    "J5": (4.5, 72.0, 90),      # IN+ / GND screw terminal
    "R1": (18.0, 36.0, 0), "R2": (18.0, 58.0, 0),
    "D1": (21.1, 47.0, 90), "D2": (24.1, 47.0, 270),
    # the differential pair
    "Q1": (33.0, 36.0, 90), "Q2": (45.6, 36.0, 270),
    "R3": (45.6, 22.5, 270),
    "RV1": (40.5, 46.0, 180),
    # the tail: the switch mirrored, so the 10k leaves to the left and the
    # sink sits under the switch
    "SW1": (40.5, 61.0, 180),
    "R4": (30.8, 70.0, 270),
    "Q6": (38.0, 69.0, 270), "R7": (38.0, 80.0, 270),
    "R5": (46.3, 71.0, 90), "R6": (43.5, 78.0, 270),
    # the gain stage, its load straight above it as the book draws it, and
    # its compensation
    "Q3": (60.0, 30.0, 90), "R8": (60.0, 21.0, 270), "R9": (60.0, 72.0, 270),
    "SW2": (54.77, 44.5, 90), "R14": (53.5, 53.5, 270), "C1": (53.5, 58.5, 270),
    # the push-pull with its emitter sense resistors
    "Q4": (70.9, 33.0, 90), "Q5": (70.9, 53.0, 90),
    "R15": (70.9, 40.5, 270), "R16": (70.9, 45.5, 270),
    # the output current limit: Q7 / D5 above the OUT line, Q8 / D6 below
    "Q7": (82.1, 38.0, 90), "D5": (82.1, 31.0, 90),
    "Q8": (82.1, 48.0, 90), "D6": (82.1, 55.0, 90),
    # the feedback box: the divider hanging from OUT, its tap X, and the
    # selector with its inputs on the left and IN- leaving on the right
    "R10": (76.5, 62.8, 270), "R11": (83.5, 67.1, 270),
    "SW3": (80.4, 75.4, 0),
    # right edge: output and power
    "J3": (94.3, OUT_Y, 0),     # OUT BNC
    "J7": (95.5, 58.0, 270),    # OUT / GND screw terminal
    "J6": (95.5, 82.0, 270),    # +15 / GND / -15 screw terminal
    "D3": (88.5, 74.0, 270), "D4": (84.3, 87.0, 180),
    "C2": (24.0, 18.0, 270), "C3": (27.5, 18.0, 270),
    "C4": (24.0, 80.0, 270), "C5": (27.5, 80.0, 270),
    # the lamps hang from the rails toward ground, like the bypass capacitors
    "R12": (93.0, 18.0, 270), "LED1": (93.0, 22.5, 90),
    "R13": (68.0, 81.0, 270), "LED2": (68.0, 76.5, 90),
    # probe loops, each on its wire
    "TP1": (26.8, 36.0, 90),    # IN- (after the 1k)
    "TP2": (26.8, 58.0, 90),    # IN+ (after the 1k), the mirror of TP1
    "TP3": (40.5, 55.0, 90),    # TAIL
    "TP4": (38.0, 76.0, 90),    # Q6 E
    "TP5": (43.5, 74.0, 90),    # Q6 B
    "TP6": (45.6, 26.8, 90),    # Q2 C, between the 1.5k and Q2
    "TP7": (61.0, 24.3, 0),     # Q3 E, between Q3 and the 330, the wire off its centre
    "TP8": (62.5, OUT_Y, 0),    # Q3 C
    "TP9": (93.3, 50.9, 0),     # OUT, beside the jack
    "TP10": (80.0, 65.1, 0),    # X, the divider's tap
    "TP11": (62.6, VP_Y, 0),    # +15V
    "TP12": (62.6, VM_Y, 0),    # -15V
    "TP13": (33.0, 42.0, 0),    # Q1 E
    "TP14": (46.8, 42.0, 0),    # Q2 E, the wire off its centre to clear the trimmer
    "TP100": (24.0, 68.5, 90), "TP101": (12.0, 80.0, 0), "TP102": (92.0, 68.5, 90), "TP103": (54.3, 68.0, 0),
    "MH1": (4.0, 4.0, 0), "MH2": (96.0, 4.0, 0), "MH3": (4.0, 96.0, 0), "MH4": (96.0, 96.0, 0),
}

# ---------------------------------------------------------------- wires ----
W_SIG, W_RAIL = 0.35, 0.6
QC_X = 65.5           # the push-pull's base bus (Q3's collector), left of the two circles
FEED_X = 88.5         # the +15 feed from the power corner up to the rail
RET_X = 87.3          # the feedback return (IN-) up the right side
OR_X = 76.5           # OUT down to the feedback box, between the two boxes
BUS_TOP, BUS_BOT = 23.9, 58.5   # the limiter's two returns to Q3 C, above and below the boxes

WIRES = [
    # +15 V rail and everything that hangs from it
    ("+15V", [(24.0, VP_Y), (93.0, VP_Y)], W_RAIL),
    ("+15V", [("Q1", "3"), (33.0, VP_Y)], W_SIG),
    ("+15V", [("R3", "1"), (45.6, VP_Y)], W_SIG),
    ("+15V", [("R8", "1"), (60.0, VP_Y)], W_SIG),
    # Q4's collector steps aside to leave the box its name, and dives under the limiter's bus
    ("+15V", [("Q4", "3"), (70.9, 28.4), (66.9, 28.4), (66.9, 25.3), (66.9, 22.5), (66.9, VP_Y)], W_SIG),
    ("+15V", [("C2", "1"), (24.0, VP_Y)], W_SIG),
    ("+15V", [("C3", "1"), (27.5, VP_Y)], W_SIG),
    ("+15V", [("R12", "1"), (93.0, VP_Y)], W_SIG),
    ("+15V", [("D3", "1"), (FEED_X, 45.2), (FEED_X, 40.8), (FEED_X, VP_Y)], W_RAIL),
    # -15 V rail
    ("-15V", [(24.0, VM_Y), (82.65, VM_Y)], W_RAIL),
    ("-15V", [("R4", "2"), (30.8, VM_Y)], W_SIG),
    ("-15V", [("R6", "2"), (43.5, VM_Y)], W_SIG),
    ("-15V", [("R7", "2"), (38.0, VM_Y)], W_SIG),
    ("-15V", [("R9", "2"), (60.0, VM_Y)], W_SIG),
    ("-15V", [("Q5", "3"), (70.9, VM_Y)], W_SIG),
    ("-15V", [("C4", "2"), (24.0, VM_Y)], W_SIG),
    ("-15V", [("C5", "2"), (27.5, VM_Y)], W_SIG),
    ("-15V", [("R13", "2"), (68.0, VM_Y)], W_SIG),
    ("-15V", [("D4", "2"), (82.65, VM_Y)], W_RAIL),
    # power entry
    ("/+15V_IN", [("J6", "1"), (FEED_X, 77.0), ("D3", "2")], W_RAIL),
    ("/-15V_IN", [("J6", "3"), ("D4", "1")], W_RAIL),
    # inputs
    ("/IN-", [("J1", "1"), ("R1", "1")], W_SIG),
    ("/IN-", [("J4", "1"), (12.5, 24.5), (12.5, 36.0)], W_SIG),
    ("/IN-", [("SW3", "3"), ("SW3", "4"), (RET_X, 74.13), (RET_X, 46.0), (RET_X, 40.0), (RET_X, 17.5), (RET_X, 12.5),
              (RET_X, FB_Y), (14.5, FB_Y), (14.5, 36.0)], W_SIG),
    ("/Q1 B", [("R1", "2"), ("Q1", "1")], W_SIG),
    ("/Q1 B", [("D1", "2"), (21.1, 36.0)], W_SIG),
    ("/Q1 B", [("D2", "1"), (24.1, 36.0)], W_SIG),
    ("/IN+", [("J2", "1"), ("R2", "1")], W_SIG),
    ("/IN+", [("J5", "1"), (12.5, 74.5), (12.5, 58.0)], W_SIG),
    ("/Q2 B", [("R2", "2"), (28.5, 58.0), (28.5, 52.0), (38.5, 52.0), (42.5, 52.0), (50.8, 52.0),
             (50.8, 36.0), ("Q2", "1")], W_SIG),
    ("/Q2 B", [("D1", "1"), (21.1, 58.0)], W_SIG),
    ("/Q2 B", [("D2", "2"), (24.1, 58.0)], W_SIG),
    # the pair's emitters, the null trimmer, the tail
    ("Net-(Q1-E)", [("Q1", "2"), (33.0, 44.3), (37.96, 44.3), ("RV1", "3")], W_SIG),
    ("Net-(Q2-E)", [("Q2", "2"), (45.6, 44.3), (43.04, 44.3), ("RV1", "1")], W_SIG),
    ("/TAIL", [("RV1", "2"), (40.5, 58.0), (44.9, 58.0), ("SW1", "2"), ("SW1", "1")], W_SIG),
    ("Net-(R4-Pad1)", [("SW1", "3"), (30.8, 59.73), ("R4", "1")], W_SIG),
    ("Net-(Q6-C)", [("SW1", "4"), (36.1, 63.6), (38.0, 63.6), ("Q6", "3")], W_SIG),
    ("Net-(Q6-B)", [("Q6", "1"), (43.5, 69.0), ("R6", "1")], W_SIG),
    ("Net-(Q6-B)", [(43.5, 69.0), (46.3, 69.0), ("R5", "2")], W_SIG),
    ("Net-(Q6-E)", [("Q6", "2"), ("R7", "1")], W_SIG),
    # the gain stage
    ("/Q2 C", [("R3", "2"), ("Q2", "3")], W_SIG),
    ("/Q2 C", [(45.6, 30.0), ("Q3", "1")], W_SIG),
    ("/Q2 C", [(53.5, 30.0), (53.5, 37.5), ("SW2", "4")], W_SIG),
    ("/Q2 C", [(53.5, 37.5), (56.04, 37.5), ("SW2", "3")], W_SIG),
    ("Net-(Q3-E)", [("Q3", "2"), ("R8", "2")], W_SIG),
    ("/Q3 C", [("Q3", "3"), (60.0, OUT_Y), (60.0, 61.5), ("R9", "1")], W_SIG),
    ("/Q3 C", [(60.0, OUT_Y), (QC_X, OUT_Y)], W_SIG),
    ("/Q3 C", [(QC_X, BUS_TOP), (QC_X, 33.0), (QC_X, OUT_Y), (QC_X, 53.0), (QC_X, BUS_BOT)], W_SIG),
    ("/Q3 C", [(QC_X, 33.0), ("Q4", "1")], W_SIG),
    ("/Q3 C", [(QC_X, 53.0), ("Q5", "1")], W_SIG),
    ("/Q3 C", [("C1", "2"), (53.5, 61.5), (60.0, 61.5)], W_SIG),
    # compensation
    ("Net-(R14-Pad1)", [("SW2", "1"), ("R14", "1")], W_SIG),
    ("Net-(C1-Pad1)", [("R14", "2"), ("C1", "1")], W_SIG),
    ("Net-(C1-Pad1)", [("SW2", "2"), (56.04, 50.5), (58.3, 50.5), (58.3, 56.0), (53.5, 56.0)], W_SIG),
    # push-pull: emitters through the sense resistors to OUT; the sense
    # transistors' bases tap the emitter wires
    ("Net-(Q4-E)", [("Q4", "2"), (70.9, 38.0), ("R15", "1")], W_SIG),
    ("Net-(Q4-E)", [(70.9, 38.0), ("Q7", "1")], W_SIG),
    ("/OUT", [("R15", "2"), (70.9, OUT_Y)], W_SIG),
    ("/OUT", [("R16", "1"), (70.9, OUT_Y)], W_SIG),
    ("Net-(Q5-E)", [("Q5", "2"), (70.9, 48.0), ("R16", "2")], W_SIG),
    ("Net-(Q5-E)", [(70.9, 48.0), ("Q8", "1")], W_SIG),
    ("/OUT", [(70.9, OUT_Y), ("J3", "1")], W_SIG),
    ("/OUT", [("J7", "1"), (94.3, 54.0), (94.3, OUT_Y)], W_SIG),
    # the current limit: Q7 and Q8 sit on OUT; D5 / D6 return to the base bus
    # along the outside of the boxes
    ("/OUT", [("Q7", "2"), (82.1, OUT_Y)], W_SIG),
    ("/OUT", [("Q8", "2"), (82.1, OUT_Y)], W_SIG),
    ("Net-(D5-K)", [("Q7", "3"), ("D5", "1")], W_SIG),
    ("/Q3 C", [("D5", "2"), (82.1, BUS_TOP), (QC_X, BUS_TOP)], W_SIG),
    ("Net-(D6-A)", [("Q8", "3"), ("D6", "2")], W_SIG),
    ("/Q3 C", [("D6", "1"), (82.1, BUS_BOT), (77.5, BUS_BOT), (75.5, BUS_BOT), (71.9, BUS_BOT), (69.9, BUS_BOT),
               (QC_X, BUS_BOT)], W_SIG),
    # the feedback box: OUT comes down between the boxes to the divider and
    # to the switch's lower input; X goes straight down into the upper one
    ("/OUT", [(OR_X, OUT_Y), (OR_X, 47.0), (OR_X, 49.0), (OR_X, 60.6), ("R10", "1")], W_SIG),
    ("/OUT", [(OR_X, 60.6), (74.0, 60.6), (74.0, 76.67), ("SW3", "2")], W_SIG),
    ("/X", [("R10", "2"), (OR_X, 65.1), (OR_X, 74.13), ("SW3", "1")], W_SIG),
    ("/X", [(OR_X, 65.1), (83.5, 65.1), ("R11", "1")], W_SIG),
    # the lamps
    ("Net-(LED1-A)", [("R12", "2"), ("LED1", "2")], W_SIG),
    ("Net-(LED2-K)", [("R13", "1"), ("LED2", "1")], W_SIG),
]

# Segments that run on the back layer, between two vias: (net, start, end).
HOPS = [
    ("/Q2 B", (38.5, 52.0), (42.5, 52.0)),        # IN+ dives under the tail
    ("+15V", (FEED_X, 45.2), (FEED_X, 40.8)),     # the +15 feed dives under OUT
    ("/IN-", (RET_X, 46.0), (RET_X, 40.0)),       # the feedback return dives under OUT
    ("/IN-", (RET_X, 17.5), (RET_X, 12.5)),       # ...and under the +15 rail
    ("+15V", (66.9, 25.3), (66.9, 22.5)),         # Q4's collector dives under D5's bus
    ("/Q3 C", (77.5, BUS_BOT), (75.5, BUS_BOT)),  # D6's bus dives under OUT's drop
    ("/Q3 C", (71.9, BUS_BOT), (69.9, BUS_BOT)),  # ...and under Q5's collector feed
    ("/OUT", (OR_X, 47.0), (OR_X, 49.0)),         # OUT's drop dives under Q8's sense lead
]

# Ground: a stub from the pad to a via (a point, or a path of points), the
# ground symbol drawn at the via pointing the way the last segment runs.
GND_STUBS = [
    # the input terminals' grounds turn down before the via so the symbol points down
    (("J4", "2"), [(9.8, 19.5), (9.8, 20.6)]), (("J5", "2"), [(9.8, 69.5), (9.8, 70.6)]),
    (("J7", "2"), [(90.8, 60.5), (90.8, 63.0)]), (("J6", "2"), [(90.6, 82.0), (90.6, 84.0)]),
    (("C2", "2"), (24.0, 21.5)), (("C3", "2"), (27.5, 21.5)),
    (("C4", "1"), (24.0, 76.5)), (("C5", "1"), (27.5, 76.5)),
    (("LED1", "1"), (93.0, 26.5)), (("LED2", "2"), (68.0, 72.5)),
    (("R11", "2"), (83.5, 69.5)), (("R5", "1"), (46.3, 74.5)),
    (("TP100", "1"), (24.0, 72.0)), (("TP101", "1"), (12.0, 83.5)), (("TP102", "1"), (92.0, 71.6)),
    (("TP103", "1"), (54.3, 71.5)),
]
# Through-hole ground posts the plane reaches directly, with where to draw the symbol.
GND_MARKS = [(10.0, 40.0), (10.0, 62.0), (90.3, OUT_Y + 4.0)]

# --------------------------------------------------------- silkscreen -----
# Transistors: ref -> (kind, base side).  The symbol is drawn round the SOT-23.
TRANSISTORS = {
    "Q1": ("NPN", "left"), "Q2": ("NPN", "right"), "Q6": ("NPN", "right"),
    "Q3": ("PNP", "left"), "Q4": ("NPN", "left"), "Q5": ("PNP", "left"),
    "Q7": ("NPN", "left"), "Q8": ("PNP", "left"),
}
Q_RADIUS = 4.0
# where each transistor's name goes, outside its circle: (x, y, justify[, size[, angle]])
Q_CAPTION = {
    "Q1": (29.6, 30.8, "left"), "Q2": (43.4, 29.3, "right"), "Q3": (54.8, 33.6, "left"),
    "Q4": (67.0, 38.2, "left", 0.8), "Q5": (67.0, 48.0, "left", 0.8), "Q6": (41.3, 65.7, "left"),
    "Q7": (84.4, 33.3, "left", 0.8), "Q8": (84.4, 52.9, "left", 0.8),
}

# Free text: (x, y, text, size, thickness, justify, angle)
TEXTS = [
    # the motto, in the band above the +15 V rail, between the fiducials
    (48.0, 7.0, "\"Op-Amps aren't magic; they're just transistors.\"", 1.8, 0.3, "center", 0),
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
    (91.8, 33.0, "OUT", 1.6, 0.3, "left", 0),
    (98.8, 36.4, "±13 V 20 mA", 0.8, 0.15, "right", 0),
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
    (33.8, 61.6, "ON", 0.8, 0.15, "center", 0),
    (46.6, 59.7, "2: 10k", 0.8, 0.15, "left", 0),
    (43.8, 64.6, "1: current", 0.8, 0.15, "left", 0),
    (43.8, 65.9, "source Q6", 0.8, 0.15, "left", 0),
    (32.3, 75.9, "CURRENT SOURCE", 0.85, 0.15, "center", 90),
    (48.4, 70.3, "R5", 0.8, 0.15, "left", 0),
    (48.4, 71.7, "62k", 0.8, 0.15, "left", 0),
    (31.3, 66.5, "R4", 0.8, 0.15, "left", 0),
    (31.3, 67.8, "10k", 0.8, 0.15, "left", 0),
    # the compensation switch, named and explained along the box's right side
    (58.2, 37.6, "SW2", 0.8, 0.15, "center", 0),
    (64.0, 54.0, "COMPENSATION", 0.9, 0.15, "center", 90),
    (58.2, 39.4, "ON", 0.8, 0.15, "center", 0),
    (62.3, 54.5, "1: 100pF+1k   2: no 1k", 0.8, 0.15, "center", 90),
    # the feedback box, explained beside its switch
    (86.2, 60.3, "FEEDBACK", 0.9, 0.18, "right", 0),
    (85.0, 72.4, "ON>", 0.8, 0.15, "center", 0),
    (78.0, 61.7, "R10 10k", 0.8, 0.15, "left", 0),
    (82.3, 67.5, "R11 1k", 0.8, 0.15, "right", 0),
    (73.8, 79.8, "1: X to IN- (x11)", 0.8, 0.15, "left", 0),
    (73.8, 81.1, "2: OUT to IN- (x1)", 0.8, 0.15, "left", 0),
    (73.8, 82.4, "off: bare op-amp", 0.8, 0.15, "left", 0),
    (48.0, 87.9, "Q1 Q2 Q4 Q6 Q7 = 2N3904 NPN       Q3 Q5 Q8 = 2N3906 PNP", 0.9, 0.15, "center", 0),
    (83.5, 31.0, "D5", 0.8, 0.15, "left", 0),
    (83.5, 55.0, "D6", 0.8, 0.15, "left", 0),
    (89.7, 76.0, "D3", 0.8, 0.15, "left", 0),
    # the clamp and the limiter's name, which says what it is
    (19.6, 44.0, "D1 D2", 0.8, 0.15, "right", 0),
    (19.6, 45.4, "1N4148W", 0.8, 0.15, "right", 0),
    (77.9, 17.6, "OUTPUT", 0.8, 0.15, "left", 0),
    (77.9, 18.85, "CURRENT", 0.8, 0.15, "left", 0),
    (77.9, 20.1, "LIMIT", 0.8, 0.15, "left", 0),
    (77.9, 21.35, "a safety net", 0.8, 0.15, "left", 0),
    (77.9, 22.85, "not in book", 0.8, 0.15, "left", 0),
]

LEGENDS = []

# Reference designators and values: (dx, dy) of each relative to the part.
FIELD_AT = {
    "R1": ((0, -2.2), (0, 2.1)), "R2": ((0, -2.2), (0, 2.1)),
    "R3": ((2.2, -0.7), (2.2, 0.7)),
    "R6": ((2.4, -0.7), (2.4, 0.7)), "R7": ((2.4, -0.7), (2.4, 0.7)),
    "R8": ((1.1, -0.7), (1.1, 0.7)), "R9": ((2.4, -0.7), (2.4, 0.7)),
    "R12": ((2.4, -0.7), (2.4, 0.7)), "R13": ((-2.4, -0.7), (-2.4, 0.7)),
    "R14": ((1.5, -0.7), (1.5, 0.7)), "C1": ((1.5, -0.7), (1.5, 0.7)),
    "R15": ((1.4, -0.7), (1.4, 0.7)), "R16": ((1.4, -0.7), (1.4, 0.7)),
    "D4": ((-2.6, -1.6), (-2.6, -0.2)),
    "LED1": ((2.4, -0.7), (2.4, 0.7)), "LED2": ((-2.4, -0.7), (-2.4, 0.7)),
}
# Parts whose reference or value is printed as free text instead, or not at all.
HIDE_REF = {"J1", "J2", "J3", "J4", "J5", "J6", "J7", "SW1", "SW2", "SW3", "D1", "D2", "D3", "D5", "D6",
            "RV1", "R4", "R5", "R10", "R11", "C2", "C3", "C4", "C5"}
HIDE_VALUE = {"SW1", "SW2", "SW3", "J1", "J2", "J3", "J4", "J5", "J6", "J7", "RV1", "D1", "D2", "D3", "D5", "D6",
              "R4", "R5", "R10", "R11", "C2", "C3", "C4", "C5",
              "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"}

# Where each probe loop's name goes, relative to the loop: (dx, dy, justify).
TP_LABEL = {
    "TP1": (0.0, -3.0, "center", 0.8), "TP2": (0.0, 3.0, "center", 0.8), "TP3": (2.0, 0.0, "left"),
    "TP4": (-1.4, -1.0, "right"), "TP5": (2.0, 0.0, "left"), "TP6": (-1.8, 0.0, "right"),
    "TP7": (-2.4, 0.0, "right"), "TP8": (0, -2.2, "center"), "TP9": None, "TP10": (0, -1.9, "center"),
    "TP11": None, "TP12": None,     # loops on the labelled rails, and by the OUT jack
    "TP13": (2.6, -0.7, "left"), "TP14": (-2.6, -0.7, "right"),
    "TP100": (2.0, 0.0, "left"), "TP101": (0, -2.6, "center"), "TP102": (2.0, 0.0, "left"), "TP103": (0, -2.2, "center"),
}

# Dashed boxes round the stages, named as the book names them:
# (x0, y0, x1, y1, [(title line, x, y[, size]), ...]); titles are short lines that dodge the wires.
BOXES = [
    (13.5, 29.0, 25.2, 63.5, [("INPUT", 15.0, 30.4), ("PROTECTION", 15.0, 32.0)]),
    (28.4, 18.5, 51.4, 50.5, [("DIFFERENCE", 34.8, 20.1), ("AMPLIFIER", 34.8, 21.9), ("x11", 34.8, 23.7)]),
    (29.6, 57.5, 51.8, 82.5, [("TAIL", 30.1, 58.6)]),
    (54.3, 18.5, 64.8, 35.4, [("GAIN", 54.8, 19.7, 0.85), ("STAGE", 54.8, 21.1, 0.85), ("x30", 54.8, 22.5, 0.85)]),
    (52.2, 36.6, 64.8, 63.0, []),
    (66.2, 24.5, 75.5, 57.8, [("PUSH-PULL", 67.5, 25.9, 0.8), ("FOLLOWER", 67.5, 27.2, 0.8)]),
    (77.5, 16.6, 86.7, 57.8, []),
    (73.2, 59.4, 86.7, 83.4, []),
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
    "POWER: +15 V, GND, -15 V into the terminal, 20 mA; set",
    "   the supply's limit to 50 mA.  Both LEDs light if right.",
    "SWITCHES, usual: TAIL 1 on (Q6 current source),",
    "   COMPENSATION 1 on (100 pF + 1k), FEEDBACK as needed.",
    "   TAIL 2 = 10k tail resistor instead.",
    "   COMPENSATION 2 = the bare 100 pF, no 1k (the book's):",
    "   the x11 amp still works, a follower rings.",
    "FEEDBACK 1 = X to IN-: gain 11.  2 = OUT to IN-:",
    "   follower.  Both off: it is a bare op-amp.",
    "AS AN OP-AMP IN YOUR OWN CIRCUIT (Labs 6-9): FEEDBACK",
    "   both off; IN-, IN+, OUT and GND on the terminals",
    "   are pins 2, 3, 6 of a '411.  Mind its 2 uA of input",
    "   bias current (no 10 M feedback); its output limits",
    "   at 20 mA, like a real one (Q7, Q8: not in the book).",
    "OFFSET NULL: as a follower with IN+ grounded,",
    "   turn RV1 until OUT reads 0 V.",
    "INPUTS: ±12 V.  OUT: ±12 V into 1k, 15 mA; a short to",
    "   ground is survived, to a rail only for seconds.",
    "PROBING: a loop on every named node for a scope",
    "   hook, and GND loops for the clip.",
]
