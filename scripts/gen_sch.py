#!/usr/bin/env python3
"""Draw the schematic of the Lab 5L op-amp, laid out as Fig. 5L.15 of
Learning the Art of Electronics draws it.

Left to right: the two inputs, the differential pair with its tail, the PNP
common-emitter gain stage with the compensation network hanging off it, the
push-pull follower, the 10k/1k output divider and the feedback selector; +15 V
rail along the top, -15 V along the bottom, power entry at the right.  Every
signal is a drawn wire; only the rails and ground use power symbols.  Notes sit
in a band under the circuit, each under the block it explains.

The board generator (scripts/layout.py) places the same parts in the same
arrangement, so the silkscreen is this drawing.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kienv, parts
from schlib import Sheet

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "hardware", "opamp.kicad_sch")
SIM = os.path.join(HERE, "..", "sim", "results.json")

G = 2.54


def g(n):
    """Grid units to millimetres."""
    return round(n * G, 4)


# ---------------------------------------------------------------- geometry --
VP_Y, VM_Y = g(30), g(92)              # the two rails
IN_M_Y, IN_P_Y = g(50), g(64)          # the two input lines
BASE_Y = g(50)                         # the diff pair's bases
C2_Y = g(44)                           # Q2's collector node, Q3's base
OUT_Y = g(56)                          # the output node and Q3's collector feed
X_Y = g(65)                            # the x11 tap
NOTE_Y = g(103)                        # the band of notes
FB_Y = g(100)                          # the feedback return along the bottom


def passive_fields(value):
    p = parts.PASSIVES.get(value)
    return {"LCSC": p["lcsc"], "MPN": p["mpn"]} if p else {}


def part_fields(key):
    p = parts.PARTS[key]
    return {"LCSC": p["lcsc"], "MPN": p["mpn"]}


def fp(key):
    return parts.PARTS[key]["footprint"]


def sym(key):
    return parts.PARTS[key]["symbol"]


def sim_results():
    try:
        return json.load(open(SIM))
    except (OSError, ValueError):
        return {}


def build():
    R = sim_results()
    op = R.get("op", {})

    def v(node, fmt="{:+.1f} V"):
        return fmt.format(op[node]) if node in op else "?"

    s = Sheet(kienv.share_dir(), paper="A2",
              title=f"{parts.BOARD_NAME}: the Lab 5L op-amp of Learning the Art of Electronics",
              date=parts.BOARD_DATE, rev=parts.REV,
              company="Circuit: Hayes & Horowitz, Learning the Art of Electronics (2016), Lab 5L  |  Board: Jason Gallicchio and Claude",
              comments=["2N3904 / 2N3906 (MMBT, SOT-23): the transistors of Chapter 4",
                        f"difference x{R.get('gdiff1', 11):.0f}, gain x{R.get('g2', 12):.0f}, follower x1: A = {R.get('a0', 140):.0f} open loop (crossover included)",
                        "Open source, CERN-OHL-P-2.0 -- " + parts.PROJECT_URL])
    pwr_n = [0]

    def pwr_ref():
        pwr_n[0] += 1
        return f"#PWR{pwr_n[0]:04d}"

    def gnd(x, y, up=False):
        s.place("power:GND", pwr_ref(), "GND", x, y, rot=180 if up else 0,
                in_bom=False, on_board=False, hide_ref=True, hide_value=True)

    def rail(name, x, y, rot=0, to=None):
        s.place(f"power:{name}", pwr_ref(), name, x, y, rot=rot, in_bom=False,
                on_board=False, hide_ref=True,
                val_off=(0, -3.81) if rot == 0 else (0, 3.81))
        if to is not None:
            s.wire((x, y), (x, to))

    def flag(x, y, to_y):
        """A PWR_FLAG hanging from a wire at (x, to_y)."""
        n = sum(1 for it in s.symbols if it[0].startswith("#FLG")) + 1
        s.place("power:PWR_FLAG", f"#FLG{n:02d}", "PWR_FLAG", x, y,
                in_bom=False, on_board=False, hide_ref=True,
                rot=0 if y < to_y else 180,
                val_off=(0, -3.81) if y < to_y else (0, 3.81))
        s.wire((x, y), (x, to_y))
        s.junction(x, to_y)

    def res(ref, value, x, y, rot=0, lcsc=None, side="right", footprint=None):
        """R_US: rot 0 vertical (pin 1 top), rot 90 horizontal (pin 1 left).
        Reference and value to the `side` of a vertical resistor; above and
        below a horizontal one."""
        if rot == 0:
            dx = 2.4 if side == "right" else -2.4
            ro, vo, j = (dx, -1.4), (dx, 1.4), ("left" if side == "right" else "right")
        else:
            ro, vo, j = (0, -2.6), (0, 2.6), None
        s.place("Device:R_US", ref, value, x, y, rot=rot,
                footprint=footprint or fp("R_0805"),
                fields=passive_fields(lcsc or value),
                ref_off=ro, val_off=vo, ref_justify=j, val_justify=j)

    def cap(ref, value, x, y, side="right"):
        dx = 2.6 if side == "right" else -2.6
        j = "left" if side == "right" else "right"
        s.place("Device:C", ref, value, x, y, footprint=fp("C_0805"),
                fields=passive_fields(value), ref_off=(dx, -1.4), val_off=(dx, 1.4),
                ref_justify=j, val_justify=j)

    # Every probe loop has a fixed number, so the board's placement (keyed by
    # reference) never slides when a loop is added to the sheet.
    TP_NUMBER = {"IN-": 1, "IN+": 2, "TAIL": 3, "Q6 E": 4, "Q6 B": 5, "Q2 C": 6, "Q3 E": 7, "Q3 C": 8,
                 "OUT": 9, "X": 10, "+15V": 11, "-15V": 12, "Q1 E": 13, "Q2 E": 14}
    gnd_tp = [100]

    def testpoint(x, y, name, rot=0, dx=1.8, dy=-3.0, justify="left"):
        """A test loop at the node, carrying the name of what it probes.
        rot 0: loop above the wire, 180 below, 90 left of a vertical wire, 270 right."""
        if name == "GND":
            n = gnd_tp[0]
            gnd_tp[0] += 1
        else:
            n = TP_NUMBER[name]
        ref = f"TP{n}"
        s.place("Connector:TestPoint", ref, name, x, y, rot=rot,
                footprint=fp("TP"), fields=part_fields("TP"),
                hide_ref=True, val_off=(dx, dy), val_justify=justify)
        s.junction(x, y)
        return ref

    def note(lines, x, y, size=1.3, justify="left", pitch=None):
        for i, line in enumerate(lines):
            if line:
                s.text(line, x, y + i * (pitch or size * 1.95), size=size, justify=justify)

    def label(txt, x, y, size=1.3, justify="left"):
        """A net name, anchored ON the wire so ERC sees it attached."""
        s.label(txt, x, y, size=size, justify=justify)

    # ================================================================ inputs ==
    # J4, the IN- terminal, above the IN- jack; J5, the IN+ one, below the IN+
    # jack.  Mirrored, so their pins face the circuit.
    s.place(sym("TERM2"), "J4", "IN- / GND", g(20), g(42), mirror="y",
            footprint=fp("TERM2"), fields=part_fields("TERM2"),
            ref_off=(-3.0, -1.6), val_off=(-3.0, 1.0), ref_justify="right", val_justify="right")
    j4a, j4b = s.pin("J4", 1, "1"), s.pin("J4", 1, "2")       # IN-, GND
    s.wire(j4a, (g(27), j4a[1]), (g(27), IN_M_Y))
    s.junction(g(27), IN_M_Y)
    s.wire(j4b, (g(24), j4b[1]), (g(24), g(46)))
    gnd(g(24), g(46))

    s.place("Connector:Conn_Coaxial", "J1", "BNC", g(22), IN_M_Y, mirror="y",
            footprint=fp("BNC"), fields=part_fields("BNC"),
            ref_off=(-4.0, 1.6), val_off=(-4.0, 3.4), ref_justify="right", val_justify="right")
    s.wire(s.pin("J1", 1, "1"), (g(29.5), IN_M_Y))
    s.wire(s.pin("J1", 1, "2"), (g(22), g(54)))
    gnd(g(22), g(54))
    s.text("IN-", g(13), IN_M_Y - 6.4, size=3.0)
    s.text("inverting input", g(13), IN_M_Y - 3.2, size=1.2)

    s.place("Connector:Conn_Coaxial", "J2", "BNC", g(22), IN_P_Y, mirror="y",
            footprint=fp("BNC"), fields=part_fields("BNC"),
            ref_off=(-4.0, 1.6), val_off=(-4.0, 3.4), ref_justify="right", val_justify="right")
    s.wire(s.pin("J2", 1, "1"), (g(29.5), IN_P_Y))
    s.wire(s.pin("J2", 1, "2"), (g(22), g(68)))
    gnd(g(22), g(68))
    s.text("IN+", g(13), IN_P_Y - 6.4, size=3.0)
    s.text("non-inverting input", g(13), IN_P_Y - 3.2, size=1.2)

    s.place(sym("TERM2"), "J5", "IN+ / GND", g(20), g(72), mirror="y",
            footprint=fp("TERM2"), fields=part_fields("TERM2"),
            ref_off=(-3.0, -1.6), val_off=(-3.0, 1.0), ref_justify="right", val_justify="right")
    j5a, j5b = s.pin("J5", 1, "1"), s.pin("J5", 1, "2")
    s.wire(j5a, (g(25), j5a[1]), (g(25), IN_P_Y))
    s.junction(g(25), IN_P_Y)
    s.wire(j5b, (g(24), j5b[1]), (g(24), g(76)))
    gnd(g(24), g(76))

    # --- series 1k, probe pins, and the anti-parallel clamp between the bases
    res("R1", "1k", g(31), IN_M_Y, rot=90, lcsc="1k_1206", footprint=fp("R_1206"))
    res("R2", "1k", g(31), IN_P_Y, rot=90, lcsc="1k_1206", footprint=fp("R_1206"))
    s.wire((g(29.5), IN_M_Y), (g(31) - 3.81, IN_M_Y))
    s.wire((g(29.5), IN_P_Y), (g(31) - 3.81, IN_P_Y))
    s.wire((g(31) + 3.81, IN_M_Y), (g(56), IN_M_Y))        # on to Q1's base
    s.wire((g(31) + 3.81, IN_P_Y), (g(79), IN_P_Y))        # on under the pair
    testpoint(g(35), IN_M_Y, "IN-", rot=0)
    testpoint(g(35), IN_P_Y, "IN+", rot=180, dy=3.2)
    DX1, DX2 = g(40), g(42)
    s.place("Device:D", "D1", "1N4148W", DX1, g(57), rot=90,
            footprint=fp("DSW"), fields=part_fields("DSW"),
            ref_off=(-2.4, -1.4), val_off=(-2.4, 1.4), ref_justify="right", val_justify="right")
    s.place("Device:D", "D2", "1N4148W", DX2, g(57), rot=270,
            footprint=fp("DSW"), fields=part_fields("DSW"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    for dx in (DX1, DX2):
        s.wire((dx, IN_M_Y), (dx, g(57) - 3.81))
        s.wire((dx, g(57) + 3.81), (dx, IN_P_Y))
        s.junction(dx, IN_M_Y)
        s.junction(dx, IN_P_Y)
    label("Q1 B", g(46), IN_M_Y)
    label("Q2 B", g(46), IN_P_Y)

    # ======================================================== diff pair ======
    Q1_X, Q2_X = g(58), g(76)
    s.place(sym("NPN"), "Q1", "2N3904", Q1_X, BASE_Y, footprint=fp("NPN"),
            fields=part_fields("NPN"), ref_off=(-4.4, -3.2), val_off=(-4.4, 3.4),
            ref_justify="right", val_justify="right")
    s.place(sym("NPN"), "Q2", "2N3904", Q2_X, BASE_Y, mirror="y", footprint=fp("NPN"),
            fields=part_fields("NPN"), ref_off=(4.4, -3.2), val_off=(4.4, 3.4),
            ref_justify="left", val_justify="left")
    q1b, q1c, q1e = s.pin("Q1", 1, "1"), s.pin("Q1", 1, "3"), s.pin("Q1", 1, "2")
    q2b, q2c, q2e = s.pin("Q2", 1, "1"), s.pin("Q2", 1, "3"), s.pin("Q2", 1, "2")
    s.wire((g(56), IN_M_Y), q1b)
    s.wire(q1c, (q1c[0], VP_Y))                       # Q1's collector straight to +15
    s.junction(q1c[0], VP_Y)
    res("R3", "1.5k", q2c[0], g(39))
    s.wire((q2c[0], VP_Y), (q2c[0], g(39) - 3.81))
    s.junction(q2c[0], VP_Y)
    s.wire((q2c[0], g(39) + 3.81), q2c)
    s.junction(q2c[0], C2_Y)
    # IN+ comes up from below and enters Q2's base from the right, as the
    # generator does in Fig. 5L.15
    s.wire((g(79), IN_P_Y), (g(79), BASE_Y), q2b)
    # emitters into the null trimmer, wiper to the tail
    POT_X, POT_Y = g(67), g(56)
    s.place(sym("POT"), "RV1", "50R", POT_X, POT_Y, rot=270, footprint=fp("POT"),
            fields=part_fields("POT"), ref_off=(-5.0, -2.4), val_off=(5.0, -2.4),
            ref_justify="right", val_justify="left")
    p1, p2, p3 = s.pin("RV1", 1, "1"), s.pin("RV1", 1, "2"), s.pin("RV1", 1, "3")
    s.wire(q1e, (q1e[0], POT_Y), p3)
    s.wire(q2e, (q2e[0], POT_Y), p1)
    testpoint(q1e[0], g(54), "Q1 E", rot=90, dx=-3.4, dy=0.5, justify="right")
    testpoint(q2e[0], g(54), "Q2 E", rot=270, dx=3.4, dy=0.5)
    s.text("OFFSET NULL", POT_X, POT_Y + 5.6, size=1.2, justify=None)
    TAIL_X = POT_X
    s.wire(p2, (TAIL_X, g(66)))
    label("TAIL", TAIL_X, g(60), justify="left")

    # --- the tail selector: 10k resistor or the current sink of Fig. 5L.10 ---
    SW1_X, SW1_Y = g(73), g(67)
    s.place(sym("DIP2"), "SW1", "TAIL", SW1_X, SW1_Y, footprint=fp("DIP2"),
            fields=part_fields("DIP2"), ref_off=(0, 3.4), val_off=(0, 5.8))
    w1, w2, w3, w4 = (s.pin("SW1", 1, p) for p in ("1", "2", "3", "4"))
    s.wire((TAIL_X, g(66)), w1)
    s.wire((TAIL_X, g(66)), (TAIL_X, g(67)), w2)
    s.junction(TAIL_X, g(66))
    testpoint(g(68.5), g(66), "TAIL", rot=0, dx=-1.0, dy=-3.0, justify="right")
    R4_X = g(90)                                      # pole 2 (lower pins): 10k to -15 V
    s.wire(w3, (R4_X, w3[1]), (R4_X, g(78) - 3.81))
    res("R4", "10k", R4_X, g(78))
    s.wire((R4_X, g(78) + 3.81), (R4_X, VM_Y))
    s.junction(R4_X, VM_Y)
    # pole 1 (upper pins): Q6, the book's "simple sink": 62k and 10k hold its base 2 V above -15, 1k sets 1.4 mA
    Q6_X, Q6_Y = g(81), g(76)
    s.place(sym("NPN"), "Q6", "2N3904", Q6_X, Q6_Y, footprint=fp("NPN"),
            fields=part_fields("NPN"), ref_off=(3.6, -3.2), val_off=(3.6, 3.4),
            ref_justify="left", val_justify="left")
    q6b, q6c, q6e = s.pin("Q6", 1, "1"), s.pin("Q6", 1, "3"), s.pin("Q6", 1, "2")
    s.wire(w4, (q6c[0], w4[1]), (q6c[0], w3[1] + 2.54), q6c)
    res("R7", "1k", q6c[0], g(84))
    s.wire(q6e, (q6c[0], g(84) - 3.81))
    s.wire((q6c[0], g(84) + 3.81), (q6c[0], VM_Y))
    s.junction(q6c[0], VM_Y)
    testpoint(q6c[0], g(80.5), "Q6 E", rot=270, dx=3.4, dy=0.5)
    DIV_X = g(66)
    s.wire(q6b, (DIV_X, q6b[1]))
    s.junction(DIV_X, q6b[1])
    testpoint(g(72), q6b[1], "Q6 B", rot=0)
    res("R5", "62k", DIV_X, g(71), side="left")
    s.wire((DIV_X, g(71) + 3.81), (DIV_X, q6b[1]))
    s.wire((DIV_X, g(71) - 3.81), (DIV_X, g(69)), (g(60), g(69)), (g(60), g(72)))
    gnd(g(60), g(72))
    res("R6", "10k", DIV_X, g(85), side="left")
    s.wire((DIV_X, q6b[1]), (DIV_X, g(85) - 3.81))
    s.wire((DIV_X, g(85) + 3.81), (DIV_X, VM_Y))
    s.junction(DIV_X, VM_Y)

    # ======================================================= gain stage ======
    Q3_X, Q3_Y = g(104), C2_Y
    s.place(sym("PNP"), "Q3", "2N3906", Q3_X, Q3_Y, mirror="x", footprint=fp("PNP"),
            fields=part_fields("PNP"), ref_off=(3.6, -3.4), val_off=(3.6, 3.6),
            ref_justify="left", val_justify="left")
    q3b, q3e, q3c = s.pin("Q3", 1, "1"), s.pin("Q3", 1, "2"), s.pin("Q3", 1, "3")
    s.wire((q2c[0], C2_Y), q3b)
    label("Q2 C", g(81), C2_Y)
    testpoint(g(86), C2_Y, "Q2 C", rot=0)
    res("R8", "330R", q3e[0], g(36))
    s.wire((q3e[0], VP_Y), (q3e[0], g(36) - 3.81))
    s.junction(q3e[0], VP_Y)
    s.wire((q3e[0], g(36) + 3.81), q3e)
    testpoint(q3e[0], g(40), "Q3 E", rot=270, dx=3.4, dy=0.5)
    res("R9", "12k", q3c[0], g(80))
    s.wire(q3c, (q3c[0], g(80) - 3.81))
    s.wire((q3c[0], g(80) + 3.81), (q3c[0], VM_Y))
    s.junction(q3c[0], VM_Y)
    s.junction(q3c[0], OUT_Y)
    label("Q3 C", q3c[0] + 2.54, OUT_Y)

    # --- compensation: 100 pF Miller cap, with the 1k that cancels its feed-forward zero
    CX = g(94)
    s.junction(CX, C2_Y)
    SW2_X, SW2_Y = CX + 2.54, g(48)
    s.place(sym("DIP2"), "SW2", "COMPENSATION", SW2_X, SW2_Y, rot=90, footprint=fp("DIP2"),
            fields=part_fields("DIP2"), ref_off=(-5.0, -2.0), val_off=(-5.0, 0.4),
            ref_justify="right", val_justify="right")
    c1, c2_, c3_, c4 = (s.pin("SW2", 1, p) for p in ("1", "2", "3", "4"))
    s.wire((CX, C2_Y), c4)
    RZ_Y = g(54.5)
    s.wire(c1, (CX, RZ_Y - 3.81))
    res("R14", "1k", CX, RZ_Y, side="left")
    CC_Y = g(59.5)
    s.wire((CX, RZ_Y + 3.81), (CX, CC_Y - 3.81))
    s.junction(CX, g(57))
    cap("C1", "100pF", CX, CC_Y, side="left")
    s.wire((CX, CC_Y + 3.81), (CX, g(64)), (q3c[0], g(64)))
    s.junction(q3c[0], g(64))
    # pole 2 bypasses the 1k: its upper pin up to Q2 C, its lower pin to the
    # node between R14 and C1, so "2" alone is the book's bare 100 pF
    s.wire(c3_, (g(98), c3_[1]), (g(98), C2_Y))
    s.junction(g(98), C2_Y)
    s.wire(c2_, (c2_[0], g(57)), (CX, g(57)))

    # ======================================================= push-pull =======
    # Q4 / Q5 with the book's bare emitters joined at OUT, plus the output
    # current limit a real op-amp has: 47 ohm in each emitter, sensed by Q7 / Q8,
    # which steal the drive above 0.65 V / 47 ohm = 14 mA.  Not in the book.
    Q4_X, Q4_Y, Q5_Y = g(116), g(46), g(66)
    s.place(sym("NPN"), "Q4", "2N3904", Q4_X, Q4_Y, footprint=fp("NPN"),
            fields=part_fields("NPN"), ref_off=(-7.6, -3.4), val_off=(-7.6, -0.6),
            ref_justify="right", val_justify="right")
    s.place(sym("PNP"), "Q5", "2N3906", Q4_X, Q5_Y, mirror="x", footprint=fp("PNP"),
            fields=part_fields("PNP"), ref_off=(-7.6, 0.6), val_off=(-7.6, 3.4),
            ref_justify="right", val_justify="right")
    q4b, q4c, q4e = s.pin("Q4", 1, "1"), s.pin("Q4", 1, "3"), s.pin("Q4", 1, "2")
    q5b, q5e, q5c = s.pin("Q5", 1, "1"), s.pin("Q5", 1, "2"), s.pin("Q5", 1, "3")
    BB_X = q4b[0]
    s.wire((q3c[0], OUT_Y), (BB_X, OUT_Y))
    s.junction(BB_X, OUT_Y)
    testpoint(g(111), OUT_Y, "Q3 C", rot=180, dy=3.2)
    s.wire(q4b, (BB_X, q5b[1]), q5b)
    s.wire(q4c, (q4c[0], VP_Y))
    s.junction(q4c[0], VP_Y)
    s.wire(q5c, (q5c[0], VM_Y))
    s.junction(q5c[0], VM_Y)
    OX = q4e[0]
    res("R15", "47R", OX, g(52), side="left")
    res("R16", "47R", OX, g(60), side="left")
    s.wire(q4e, (OX, g(52) - 3.81))
    s.wire((OX, g(52) + 3.81), (OX, g(60) - 3.81))
    s.wire((OX, g(60) + 3.81), q5e)
    s.junction(OX, OUT_Y)
    # the limiter: Q7 senses R15 (base on Q4's emitter), Q8 senses R16
    Q7_X = g(121)
    s.place(sym("NPN"), "Q7", "2N3904", Q7_X, g(49), footprint=fp("NPN"),
            fields=part_fields("NPN"), ref_off=(3.6, -3.4), val_off=(3.6, -0.6),
            ref_justify="left", val_justify="left")
    s.place(sym("PNP"), "Q8", "2N3906", Q7_X, g(63), mirror="x", footprint=fp("PNP"),
            fields=part_fields("PNP"), ref_off=(3.6, 0.6), val_off=(3.6, 3.4),
            ref_justify="left", val_justify="left")
    q7b, q7c, q7e = s.pin("Q7", 1, "1"), s.pin("Q7", 1, "3"), s.pin("Q7", 1, "2")
    q8b, q8e, q8c = s.pin("Q8", 1, "1"), s.pin("Q8", 1, "2"), s.pin("Q8", 1, "3")
    s.wire((OX, q7b[1]), q7b)
    s.junction(OX, q7b[1])
    s.wire((OX, q8b[1]), q8b)
    s.junction(OX, q8b[1])
    LX = q7e[0]
    s.wire(q7e, (LX, OUT_Y), q8e)
    s.junction(LX, OUT_Y)
    # D5 / D6 block the idle sense transistor's base-collector junction, which
    # the other half's Vbe would otherwise forward-bias (anodes toward Q3 C)
    s.place("Device:D", "D5", "1N4148W", LX, g(44), rot=90,
            footprint=fp("DSW"), fields=part_fields("DSW"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.place("Device:D", "D6", "1N4148W", LX, g(68), rot=90,
            footprint=fp("DSW"), fields=part_fields("DSW"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.wire(q7c, (LX, g(44) + 3.81))
    s.wire((LX, g(44) - 3.81), (LX, g(40)), (BB_X, g(40)), q4b)   # crosses Q4's collector wire: no dot
    s.wire(q8c, (LX, g(68) - 3.81))
    s.wire((LX, g(68) + 3.81), (LX, g(72)), (BB_X, g(72)), q5b)
    OUT_X0 = g(126)
    s.wire((OX, OUT_Y), (OUT_X0, OUT_Y))
    label("OUT", LX + 2.54, OUT_Y + 0.0)

    # --- the 10k / 1k that load the output and make the x11 feedback ---------
    s.junction(OUT_X0, OUT_Y)
    res("R10", "10k", OUT_X0, g(61))
    s.wire((OUT_X0, OUT_Y), (OUT_X0, g(61) - 3.81))
    s.wire((OUT_X0, g(61) + 3.81), (OUT_X0, X_Y))
    s.junction(OUT_X0, X_Y)
    label("X", OUT_X0 + 2.54, X_Y)
    testpoint(OUT_X0, g(66), "X", rot=90, dx=-3.4, dy=0.5, justify="right")
    res("R11", "1k", OUT_X0, g(69.5))
    s.wire((OUT_X0, X_Y), (OUT_X0, g(69.5) - 3.81))
    s.wire((OUT_X0, g(69.5) + 3.81), (OUT_X0, g(74)))
    gnd(OUT_X0, g(74))
    testpoint(OUT_X0, g(58), "OUT", rot=270, dx=3.4, dy=0.5)

    # --- feedback selector: x11 from X (pole 1), x1 from OUT (pole 2) --------
    # Drawn mirrored top-to-bottom so pole 1 (X, gain 11) is the lower pair of
    # pins, level with the X wire, and pole 2 (OUT, the follower) the upper:
    # the OUT wire then drops to its pin without crossing the X wire.  On the
    # board pole 1 is the switch's left column, where X arrives.
    SW3_X, SW3_Y = g(136), g(64)
    s.place(sym("DIP2"), "SW3", "FEEDBACK", SW3_X, SW3_Y, mirror="x", footprint=fp("DIP2"),
            fields=part_fields("DIP2"), ref_off=(0, 6.0), val_off=(0, 8.4))
    f1, f2, f3, f4 = (s.pin("SW3", 1, p) for p in ("1", "2", "3", "4"))
    s.wire((OUT_X0, X_Y), f1)                                          # x11
    OUT_X1 = g(131)
    s.wire((OUT_X0, OUT_Y), (OUT_X1, OUT_Y))
    s.junction(OUT_X1, OUT_Y)
    s.wire((OUT_X1, OUT_Y), (OUT_X1, f2[1]), f2)                        # x1
    FBX = g(141)
    s.wire(f4, (FBX, f4[1]), (FBX, f3[1]), f3)
    s.junction(FBX, f3[1])
    # ...and back to IN-: down under the -15 V rail, along the bottom, up the
    # left margin and into the IN- terminal's wire
    s.wire((FBX, f3[1]), (FBX, FB_Y), (g(17), FB_Y), (g(17), g(44)), (g(27), g(44)))
    s.junction(g(27), g(44))
    label("IN-", g(60), FB_Y)
    label("IN+", g(28), IN_P_Y)

    # --- OUT jack and terminal ------------------------------------------------
    s.wire((OUT_X1, OUT_Y), (g(145), OUT_Y))
    s.place("Connector:Conn_Coaxial", "J3", "BNC", g(147), OUT_Y,
            footprint=fp("BNC"), fields=part_fields("BNC"),
            ref_off=(4.0, -2.6), val_off=(4.0, 0.4), ref_justify="left", val_justify="left")
    s.wire(s.pin("J3", 1, "2"), (g(147), g(60)))
    gnd(g(147), g(60))
    s.text("OUT", g(150), OUT_Y + 1.0, size=3.0)
    s.place(sym("TERM2"), "J7", "OUT / GND", g(149), g(48),
            footprint=fp("TERM2"), fields=part_fields("TERM2"),
            ref_off=(3.0, -1.0), val_off=(3.0, 1.6), ref_justify="left", val_justify="left")
    j7a, j7b = s.pin("J7", 1, "1"), s.pin("J7", 1, "2")
    s.wire((g(137), OUT_Y), (g(137), j7a[1]), j7a)
    s.junction(g(137), OUT_Y)
    s.wire(j7b, (g(143), j7b[1]), (g(143), g(52)))
    gnd(g(143), g(52))

    # ========================================================== rails ========
    PR = g(156)
    s.wire((q1c[0], VP_Y), (PR, VP_Y))
    s.wire((DIV_X, VM_Y), (PR, VM_Y))
    rail("+15V", g(62), VP_Y - 3.81, to=VP_Y)
    s.junction(g(62), VP_Y)
    rail("-15V", g(62), VM_Y + 3.81, rot=180, to=VM_Y)
    s.junction(g(62), VM_Y)
    s.wire((g(62), VP_Y), (q1c[0], VP_Y))
    s.wire((g(62), VM_Y), (DIV_X, VM_Y))
    testpoint(g(136), VP_Y, "+15V", rot=0)
    testpoint(g(136), VM_Y, "-15V", rot=180, dy=3.2)

    # ====================================================== power entry ======
    s.place(sym("TERM3"), "J6", "+15 / GND / -15", g(160), g(60),
            footprint=fp("TERM3"), fields=part_fields("TERM3"),
            ref_off=(3.0, -2.0), val_off=(3.0, 1.0), ref_justify="left", val_justify="left")
    j6a, j6b, j6c = s.pin("J6", 1, "1"), s.pin("J6", 1, "2"), s.pin("J6", 1, "3")
    s.text("POWER", g(160), g(54.5), size=3.0)
    s.text("+15 V, GND, -15 V from a bench supply; 20 mA", g(160), g(56.3), size=1.2)
    DP_X = g(152)                                     # +15 in: Schottky, then the rail
    s.place("Device:D_Schottky", "D3", "B5819W", DP_X, g(40), rot=270,
            footprint=fp("DSCH"), fields=part_fields("DSCH"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.wire(j6a, (DP_X, j6a[1]), (DP_X, g(40) + 3.81))
    s.wire((DP_X, g(40) - 3.81), (DP_X, VP_Y))
    s.junction(DP_X, VP_Y)
    label("+15V_IN", g(152.5), j6a[1])
    flag(g(157), j6a[1] - 2.54, j6a[1])
    DM_X = g(150)                                     # -15 in: Schottky the other way
    s.place("Device:D_Schottky", "D4", "B5819W", DM_X, g(76), rot=270,
            footprint=fp("DSCH"), fields=part_fields("DSCH"),
            ref_off=(2.4, -1.4), val_off=(2.4, 1.4), ref_justify="left", val_justify="left")
    s.wire(j6c, (g(157), j6c[1]), (g(157), g(66)), (DM_X, g(66)), (DM_X, g(76) - 3.81))
    s.wire((DM_X, g(76) + 3.81), (DM_X, VM_Y))
    s.junction(DM_X, VM_Y)
    label("-15V_IN", g(150.5), g(66))
    flag(g(156), g(66) + 2.54, g(66))
    s.wire(j6b, (g(154), j6b[1]))
    gnd(g(154), j6b[1])
    flag(g(155.5), j6b[1] + 2.54, j6b[1])
    flag(g(150), VP_Y - 2.54, VP_Y)                   # the rails themselves are sources too
    flag(g(146), VM_Y + 2.54, VM_Y)
    # bulk and bypass on each rail, and a lamp per rail
    for i, (ref, val) in enumerate((("C2", "10uF"), ("C3", "100nF"))):
        cx = g(140 + 4 * i)
        cap(ref, val, cx, g(36))
        s.wire((cx, VP_Y), (cx, g(36) - 3.81))
        s.wire((cx, g(36) + 3.81), (cx, g(40)))
        gnd(cx, g(40))
        s.junction(cx, VP_Y)
    for i, (ref, val) in enumerate((("C4", "10uF"), ("C5", "100nF"))):
        cx = g(140 + 4 * i)
        cap(ref, val, cx, g(86))
        s.wire((cx, VM_Y), (cx, g(86) + 3.81))
        s.wire((cx, g(86) - 3.81), (cx, g(82)))
        gnd(cx, g(82), up=True)
        s.junction(cx, VM_Y)
    LX = PR
    res("R12", "10k", LX, g(36))
    s.wire((LX, VP_Y), (LX, g(36) - 3.81))
    s.place("Device:LED", "LED1", "GREEN", LX, g(42), rot=90, footprint=fp("LED"),
            fields=part_fields("LED"), ref_off=(2.8, -1.4), val_off=(2.8, 1.4),
            ref_justify="left", val_justify="left")
    s.wire((LX, g(36) + 3.81), s.pin("LED1", 1, "2"))
    s.wire(s.pin("LED1", 1, "1"), (LX, g(46)))
    gnd(LX, g(46))
    s.text("+15 V present", LX + 2.8, g(36) + 4.6, size=1.2)
    res("R13", "10k", LX, g(86))
    s.wire((LX, VM_Y), (LX, g(86) + 3.81))
    s.place("Device:LED", "LED2", "GREEN", LX, g(80), rot=90, footprint=fp("LED"),
            fields=part_fields("LED"), ref_off=(2.8, -1.4), val_off=(2.8, 1.4),
            ref_justify="left", val_justify="left")
    s.wire((LX, g(86) - 3.81), s.pin("LED2", 1, "1"))
    s.wire(s.pin("LED2", 1, "2"), (LX, g(76)))
    gnd(LX, g(76), up=True)
    s.text("-15 V present", LX + 2.8, g(86) - 3.6, size=1.2)

    # ================================================== probe grounds ========
    for x in (g(40), g(70), g(100), g(126)):
        testpoint(x, g(96), "GND", rot=0, dx=1.8, dy=-3.0)
        s.wire((x, g(96)), (x, g(97)))
        gnd(x, g(97))
    s.text("ground loops for the scope's clip", g(40) + 3.5, g(96) + 0.4, size=1.1)

    # ================================================== mechanical ===========
    for i in range(4):
        s.place(sym("MH"), f"MH{i + 1}", "MountingHole", g(150 + 4 * i), g(122),
                footprint=fp("MH"), in_bom=False, ref_off=(0, -3.5), val_off=(0, 3.5),
                hide_value=True)
    s.text("M3 mounting holes, one per corner", g(148), g(126), size=1.2)

    # ================================================== the story ============
    note([f"{parts.BOARD_NAME.upper()}",
          "",
          "The op-amp of Lab 5L (Learning the Art of Electronics, Hayes & Horowitz, 2016), built from the NPN and",
          "PNP of Chapter 4 as eight SOT-23 transistors, on a board whose silkscreen is this drawing.",
          "Three stages, as the book's Fig. 5L.11 and 5N.32:",
          "",
          f"    difference    Q1 Q2, 1.5k collector load on the + side, tail from RV1 through SW1     x{R.get('gdiff1', 11):.0f}",
          f"    gain          Q3, PNP common emitter: 12k / (330 + re) = 30; the push-pull's dead zone takes a third of it     x{R.get('g2', 12):.0f}",
          "    follower      Q4 Q5 push-pull, unbiased, so crossover distortion shows until feedback hides it     x1",
          "",
          f"Open-loop gain at DC about {R.get('a0', 140):.0f} (the book says 'approximately 1000' for its CA3096 version, before the",
          f"dead zone).  As a follower it settles in {R.get('ts_x1_us', 0.5):.1f} us with {R.get('pm_x1', 55):.0f} deg of phase margin; the x11 amplifier",
          f"has a bandwidth of {R.get('f11_khz', 380):.0f} kHz and a gain of {R.get('g11', 10.2):.1f}, {100 * (1 - R.get('g11', 10.2) / 11):.0f} % low, as the book predicts for so little loop gain.",
          "",
          "Quiescent as a follower with IN+ grounded (simulated with the 2N3904/2N3906 models, sim/opamp_sim.py):",
          f"    TAIL {v('tail')}    Q2 C {v('c2')}    Q3 E {v('e3')}    Q3 C {v('c3')}    OUT {v('out')}    tail {R.get('i_tail_ma', 1.4):.2f} mA    Q3 {R.get('i_q3_ma', 1.3):.2f} mA    rails +/-{R.get('vrail', 14.6):.1f} V"],
         g(13), g(8), size=1.5, pitch=3.1)

    # ================================================== the notes band =======
    col = [g(13), g(44), g(78), g(112), g(146)]
    note(["INPUTS",
          "Each input has a BNC and a screw terminal in",
          "parallel; +/-12 V on either.  For a common-mode",
          "test, tee one generator into both jacks.",
          "",
          "INPUT PROTECTION  (R1, R2, D1, D2: not in the book)",
          "1k in series with each input, and two 1N4148",
          "back to back between the bases: the bases never",
          "differ by more than 0.7 V, so no base-emitter",
          "junction sees its 6 V reverse breakdown when one",
          "input is driven hard and the other is not.",
          "A 1 M probe or a 50 ohm generator never notices",
          "the 1k; Ib (about 5 uA) drops 5 mV across it."],
         col[0], NOTE_Y)
    note(["TAIL  (SW1)",
          "1 ON: Q6, the 'simple sink' of Fig. 5L.10, 1.4 mA",
          "2 ON: 10k to -15 V, 1.4 mA  (Fig. 5L.1)",
          "The sink raises the tail's impedance from 10k to",
          "about 1 M; stage 1's common-mode gain falls from",
          f"{R.get('gcm_r', 0.07):.3f} to {R.get('gcm_cs', 0.0004):.4f}.  Both OFF: no tail current, dead.",
          "Normal: 1 ON, 2 OFF.",
          "",
          "OFFSET NULL  (RV1: not in the book)",
          "The two halves of the 50 ohm trimmer are the pair's",
          "emitter resistors, 25 ohm each at centre.  Turning it",
          f"unbalances the pair by up to +/-{R.get('null_mv', 33):.0f} mV at the input:",
          "enough to centre the output in open loop and to",
          "cancel the pair's Vbe mismatch in closed loop.",
          "It costs half of stage 1's gain (11 instead of 20)."],
         col[1], NOTE_Y)
    note(["COMPENSATION  (SW2)",
          "1 ON: 100 pF from Q3's collector to its base, Miller-",
          "multiplied by the stage's gain of 30 into a 3 nF",
          "low-pass at C2.  The book's Fig. 5L.17.",
          "2 ON: the bare 100 pF, no 1k: the book's version.",
          "1 and 2 ON: the same as 2.",
          "",
          "The 1k is not in the book.  A bare Miller cap feeds",
          "the signal FORWARD above 4 MHz, the loop's sign",
          "flips, and a follower oscillates: the book's 'risky",
          f"business'.  With the 1k the follower has {R.get('pm_x1', 55):.0f} deg of",
          f"phase margin and settles in {R.get('ts_x1_us', 0.5):.1f} us; the x11 amp is",
          "stable either way.  Both OFF: no compensation,",
          "and the x11 amplifier rings.",
          "Normal: 1 ON, 2 OFF."],
         col[2], NOTE_Y)
    note(["FEEDBACK  (SW3)",
          "1 ON: X to IN-, gain 11  (Fig. 5L.16)",
          "2 ON: OUT to IN-, a follower  (Fig. 5L.18)",
          "Both OFF: nothing; wire your own network between",
          "the OUT, IN- and GND terminals.  The feedback goes",
          "to the IN- terminal, so R1 and the clamp still guard",
          "Q1's base.  The 10k + 1k are the book's load and its",
          "x11 divider in one: X = OUT / 11.",
          "",
          "OUTPUT",
          f"{R['swing'][0]:+.0f} to {R['swing'][1]:+.0f} V into the 11k; 10 mA max." if "swing" in R else "+/-13 V into the 11k; 10 mA max.",
          "Q7, Q8, D5, D6 and the 47 ohm resistors are not in the",
          "book: they limit the output to about 20 mA, as a real",
          "op-amp does: a short to ground is survived, to a rail for seconds."],
         col[3], NOTE_Y)
    note(["POWER",
          "+15 V, GND, -15 V from a bench supply, 20 mA.",
          "Series Schottkys: a supply connected backwards",
          "does nothing instead of forward-biasing every",
          "transistor.  The rails run 0.35 V below the",
          f"terminals: +/-{R.get('vrail', 14.6):.1f} V on the board.  Everything",
          "in the book's circuit is referred to those rails,",
          "and nothing in it minds.  A green LED per rail",
          "says the supply is on and the right way round.",
          "",
          "PROBING",
          "A wire loop on every node named on the sheet;",
          "a scope hook grabs it.  Four ground loops for",
          "the clip."],
         col[4], NOTE_Y)
    return s


if __name__ == "__main__":
    s = build()
    added = s.add_missing_junctions()
    if added:
        print(f"  auto-placed {added} junction(s) where wires meet end-to-middle")
    bad = s.check_grid()
    if bad:
        print(f"  !! {len(bad)} off-grid endpoint(s):")
        for what, pt in bad[:12]:
            print(f"       {what} at {pt}")
        raise SystemExit("off-grid endpoints would confuse KiCad's connectivity")
    s.write(OUT)
    print(f"  wrote {os.path.relpath(OUT)}")
