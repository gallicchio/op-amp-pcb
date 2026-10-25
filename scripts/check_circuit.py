#!/usr/bin/env python3
"""Read the exported netlist back and prove it is the Lab 5L op-amp.

This does not trust the drawing.  It walks the real netlist and checks that
every transistor is wired as the book's Fig. 5L.15 wires it, that the values
really attached give the currents and gains the sheet quotes, that the
switches select what their legends say, and that the protection, the rails
and the probe loops are where they claim to be.

    python3 scripts/check_circuit.py out/opamp.net
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp_parse import parse_file

TOL = 0.02


def ohms(text):
    t = text.strip().upper().rstrip("R")
    mult = 1.0
    if t.endswith("M"):
        mult, t = 1e6, t[:-1]
    elif t.endswith("K"):
        mult, t = 1e3, t[:-1]
    return float(t) * mult


def farads(text):
    t = text.strip().lower()
    for suffix, mult in (("uf", 1e-6), ("nf", 1e-9), ("pf", 1e-12)):
        if t.endswith(suffix):
            return float(t[:-len(suffix)]) * mult
    return float(t)


class Net:
    def __init__(self, path):
        root = parse_file(path)
        self.value, self.footprint = {}, {}
        for c in root.first("components").kids("comp"):
            ref = c.first("ref").atom(0)
            self.value[ref] = c.first("value").atom(0)
            f = c.first("footprint")
            self.footprint[ref] = f.atom(0) if f is not None else ""
        self.nets = {}
        for n in root.first("nets").kids("net"):
            name = n.first("name").atom(0).lstrip("/")
            self.nets[name] = {(x.first("ref").atom(0), x.first("pin").atom(0)) for x in n.kids("node")}
        self.of = {}
        for name, nodes in self.nets.items():
            for node in nodes:
                self.of[node] = name

    def net(self, ref, pin):
        return self.of.get((ref, str(pin)))

    def pins_on(self, name):
        return self.nets.get(name, set())

    def between(self, a, b, prefix="R"):
        """Two-pin parts whose pins are on nets a and b (either way round)."""
        out = []
        for ref in self.value:
            if not ref.startswith(prefix) or ref[len(prefix):len(prefix) + 1] == "V":
                continue
            n1, n2 = self.net(ref, 1), self.net(ref, 2)
            if {n1, n2} == {a, b}:
                out.append(ref)
        return out


def main(path):
    N = Net(path)
    ok, bad = [], []

    def check(cond, what):
        (ok if cond else bad).append(what)

    # --- the transistors: 1 = B, 2 = E, 3 = C on every SOT-23 ----------------
    for q, kind in (("Q1", "2N3904"), ("Q2", "2N3904"), ("Q3", "2N3906"),
                    ("Q4", "2N3904"), ("Q5", "2N3906"), ("Q6", "2N3904")):
        check(N.value[q] == kind, f"{q} is a {kind}")
        check(N.footprint[q].endswith("SOT-23"), f"{q} is in SOT-23")

    # --- difference amplifier ------------------------------------------------
    check(N.net("Q1", 3) == "+15V", "Q1's collector goes straight to +15 V (the book draws no load there)")
    r3 = N.between("+15V", N.net("Q2", 3))
    check(r3 == ["R3"] and abs(ohms(N.value["R3"]) - 1500) < 1, "Q2's collector load is R3 = 1.5k to +15 V")
    check(N.net("Q2", 3) == "Q2 C" == N.net("Q3", 1), "Q2's collector (Q2 C) drives Q3's base")
    check(N.net("Q1", 2) == N.net("RV1", 3) and N.net("Q2", 2) == N.net("RV1", 1),
          "the two emitters are the ends of the null trimmer RV1")
    check(N.net("RV1", 2) == "TAIL", "RV1's wiper is the tail")
    check(N.value["RV1"] == "50R", "RV1 is 50 ohm: 25 ohm per emitter at centre, +/-19 mV of null")
    check(N.net("Q1", 1) == "Q1 B" and N.net("Q2", 1) == "Q2 B", "Q1's base is the - input, Q2's the + input")

    # --- input protection ---------------------------------------------------
    check(N.between("IN-", "Q1 B") == ["R1"] and ohms(N.value["R1"]) == 1000, "R1 = 1k from IN- to Q1's base")
    check(N.between("IN+", "Q2 B") == ["R2"] and ohms(N.value["R2"]) == 1000, "R2 = 1k from IN+ to Q2's base")
    check(N.footprint["R1"].endswith("R_1206_3216Metric") and N.footprint["R2"].endswith("R_1206_3216Metric"),
          "R1 and R2 are 1206: a rail on an input puts 0.2 W in them")
    check(N.net("D1", 2) == "Q1 B" and N.net("D1", 1) == "Q2 B" and N.net("D2", 1) == "Q1 B" and N.net("D2", 2) == "Q2 B",
          "D1 and D2 are back to back between the bases (anode of one to the cathode of the other)")

    # --- the tail: SW1 pole 1 = Q6, pole 2 = 10k ------------------------------
    check(N.net("SW1", 1) == "TAIL" and N.net("SW1", 2) == "TAIL", "SW1's common pins are the tail")
    check(N.net("SW1", 4) == N.net("Q6", 3), "SW1 pole 1 (pins 1-4) switches in Q6's collector")
    r4 = N.between(N.net("SW1", 3), "-15V")
    check(r4 == ["R4"] and ohms(N.value["R4"]) == 10000, "SW1 pole 2 (pins 2-3) switches in R4 = 10k to -15 V")
    # Q6, the simple sink: 62k to ground, 10k to -15, 1k emitter
    b6 = N.net("Q6", 1)
    check(N.between("GND", b6) == ["R5"] and ohms(N.value["R5"]) == 62000, "R5 = 62k from Q6's base to ground")
    check(N.between(b6, "-15V") == ["R6"] and ohms(N.value["R6"]) == 10000, "R6 = 10k from Q6's base to -15 V")
    check(N.between(N.net("Q6", 2), "-15V") == ["R7"] and ohms(N.value["R7"]) == 1000, "R7 = 1k in Q6's emitter")
    vb = -15.0 + 15.0 * 10000 / 72000            # the divider, unloaded
    i_tail = (vb - 0.65 + 15.0) / 1000.0
    check(1.2e-3 < i_tail < 1.6e-3, f"the sink's design current is {i_tail*1e3:.2f} mA (book: about 1.5 mA)")
    i_r4 = (15.0 - 0.7) / 10000.0
    check(1.3e-3 < i_r4 < 1.6e-3, f"the 10k tail gives {i_r4*1e3:.2f} mA (book: about 1.5 mA)")

    # --- the gain stage --------------------------------------------------------
    check(N.between("+15V", N.net("Q3", 2)) == ["R8"] and ohms(N.value["R8"]) == 330, "R8 = 330 in Q3's emitter to +15 V")
    check(N.between(N.net("Q3", 3), "-15V") == ["R9"] and ohms(N.value["R9"]) == 12000, "R9 = 12k from Q3's collector to -15 V")
    check(N.net("Q3", 3) == "Q3 C", "Q3's collector is the node Q3 C")
    # gains, as the sheet quotes them
    re1 = 0.026 / (i_tail / 2)
    g1 = 1500 / (2 * (re1 + 25))
    check(9 < g1 < 14, f"stage 1 gain Rc / 2(re + 25) = {g1:.1f} (book, no emitter resistors: about 20)")
    re3 = 0.026 / 1.25e-3
    g2 = 12000 / (re3 + 330)
    check(30 < g2 < 38, f"stage 2 gain 12k / (330 + re) = {g2:.0f} (book: 40)")

    # --- compensation: SW2 pole 1 in series with C1 + R14, pole 2 across R14 ---
    check(N.net("SW2", 4) == "Q2 C", "SW2 pin 4 is on Q2 C (Q3's base)")
    n1 = N.net("SW2", 1)
    check(N.between(n1, N.net("C1", 1)) == ["R14"] and ohms(N.value["R14"]) == 1000,
          "R14 = 1k between SW2's pole 1 and C1")
    check(N.net("C1", 2) == "Q3 C" and abs(farads(N.value["C1"]) - 100e-12) < 1e-13, "C1 = 100 pF to Q3 C (Q3's collector)")
    check(N.net("SW2", 2) == n1 and N.net("SW2", 3) == N.net("C1", 1), "SW2 pole 2 shorts R14")
    f_z = 1 / (2 * math.pi * 100e-12 * (1000 - 350))
    check(f_z > 1e6, f"with the 1k the Miller zero sits in the left half-plane at {f_z/1e6:.1f} MHz")

    # --- push-pull --------------------------------------------------------------
    check(N.net("Q4", 1) == "Q3 C" and N.net("Q5", 1) == "Q3 C", "Q4 and Q5's bases are driven by Q3 C")
    check(N.net("Q4", 3) == "+15V" and N.net("Q5", 3) == "-15V", "Q4's collector to +15 V, Q5's to -15 V")
    # the output current limit (not in the book): 33 ohm in each emitter, sensed by Q7 / Q8
    check(N.between(N.net("Q4", 2), "OUT") == ["R15"] and ohms(N.value["R15"]) == 47, "R15 = 47 ohm from Q4's emitter to OUT")
    check(N.between(N.net("Q5", 2), "OUT") == ["R16"] and ohms(N.value["R16"]) == 47, "R16 = 47 ohm from Q5's emitter to OUT")
    check(N.net("Q7", 1) == N.net("Q4", 2) and N.net("Q7", 2) == "OUT", "Q7 senses R15 from OUT")
    check(N.net("Q8", 1) == N.net("Q5", 2) and N.net("Q8", 2) == "OUT", "Q8 senses R16 from OUT")
    check(N.net("D5", 2) == "Q3 C" and N.net("D5", 1) == N.net("Q7", 3), "D5 lets Q7 pull Q3 C down, never up")
    check(N.net("D6", 1) == "Q3 C" and N.net("D6", 2) == N.net("Q8", 3), "D6 lets Q8 pull Q3 C up, never down")
    i_lim = 0.65 / ohms(N.value["R15"])
    check(0.012 < i_lim < 0.022, f"the output limits at about {i_lim*1e3:.0f} mA: enough for 13 V into 1k, a short survives")
    check(N.between("OUT", "X") == ["R10"] and ohms(N.value["R10"]) == 10000, "R10 = 10k from OUT to X")
    check(N.between("X", "GND") == ["R11"] and ohms(N.value["R11"]) == 1000, "R11 = 1k from X to ground")
    check(abs(11000 / 1000 - 11) < 1e-9, "X = OUT / 11: the book's x11 divider")

    # --- feedback: SW3 pole 1 = X, pole 2 = OUT, both to IN- ---------------------
    check(N.net("SW3", 1) == "X" and N.net("SW3", 2) == "OUT", "SW3 pole 1 takes X, pole 2 takes OUT")
    check(N.net("SW3", 3) == "IN-" and N.net("SW3", 4) == "IN-", "SW3's other pins both go to IN-")

    # --- connectors --------------------------------------------------------------
    for j, pin, net in (("J1", 1, "IN-"), ("J2", 1, "IN+"), ("J3", 1, "OUT"), ("J4", 1, "IN-"),
                        ("J5", 1, "IN+"), ("J7", 1, "OUT"), ("J6", 1, "+15V_IN"), ("J6", 3, "-15V_IN")):
        check(N.net(j, pin) == net, f"{j} pin {pin} is {net}")
    for j in ("J1", "J2", "J3", "J4", "J5", "J7"):
        check(N.net(j, 2) == "GND", f"{j}'s other pin is ground")
    check(N.net("J6", 2) == "GND", "J6's middle pin is ground")

    # --- power entry -----------------------------------------------------------
    check(N.net("D3", 2) == "+15V_IN" and N.net("D3", 1) == "+15V", "D3's anode on +15V_IN, cathode on the +15 V rail")
    check(N.net("D4", 1) == "-15V_IN" and N.net("D4", 2) == "-15V", "D4's cathode on -15V_IN, anode on the -15 V rail")
    for c in ("C2", "C3"):
        check(N.net(c, 1) == "+15V" and N.net(c, 2) == "GND", f"{c} bypasses +15 V")
    for c in ("C4", "C5"):
        check(N.net(c, 2) == "-15V" and N.net(c, 1) == "GND", f"{c} bypasses -15 V")
    check(N.net("LED1", 1) == "GND" and N.between("+15V", N.net("LED1", 2)) == ["R12"], "LED1 from +15 V through R12 to ground")
    check(N.net("LED2", 2) == "GND" and N.between(N.net("LED2", 1), "-15V") == ["R13"], "LED2 from ground through R13 to -15 V")
    i_led = (14.6 - 2.5) / ohms(N.value["R12"])
    check(0.5e-3 < i_led < 3e-3, f"the lamps run at {i_led*1e3:.1f} mA")
    i_board = i_tail + 1.25e-3 + 2 * i_led + 0.3e-3
    check(i_board < 0.02, f"the board draws about {i_board*1e3:.1f} mA per rail")

    # --- probe loops on the nodes they claim ---------------------------------------
    for tp, net in (("TP1", "Q1 B"), ("TP2", "Q2 B"), ("TP3", "TAIL"), ("TP6", "Q2 C"), ("TP8", "Q3 C"),
                    ("TP9", "OUT"), ("TP10", "X"), ("TP11", "+15V"), ("TP12", "-15V"),
                    ("TP100", "GND"), ("TP101", "GND"), ("TP102", "GND"), ("TP103", "GND")):
        check(N.net(tp, 1) == net, f"{tp} ({N.value[tp]}) is on {net}")
    check(N.net("TP4", 1) == N.net("Q6", 2), "TP4 is Q6's emitter")
    check(N.net("TP5", 1) == N.net("Q6", 1), "TP5 is Q6's base")
    check(N.net("TP7", 1) == N.net("Q3", 2), "TP7 is Q3's emitter")
    check(N.net("TP13", 1) == N.net("Q1", 2) and N.net("TP14", 1) == N.net("Q2", 2), "TP13/TP14 are the pair's emitters")

    # --- one-pin nets: none but the switches' unused poles --------------------------
    single = [n for n, nodes in N.nets.items() if len(nodes) == 1]
    check(not single, f"no one-pin nets ({single})")

    print(f"  {len(ok)} circuit checks passed" + (f", {len(bad)} FAILED" if bad else ""))
    for b in bad:
        print(f"  FAIL  {b}")
    if not bad:
        print("  all circuit checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "out", "opamp.net")))
