#!/usr/bin/env python3
"""Simulate every student abuse scenario in Section 3 items 2e and 8."""
import math, os, sys
sys.path.insert(0, os.path.abspath("design_reviews/2026-10-27_Gemini-4-Argon/project/sim"))
from ngspice_lib import NgSpice
import opamp_sim as S, comp_study as CS

def check_stress(desc, extra_lines, vsup_p=14.6, vsup_n=-14.6, rfb=True):
    L = CS.core_rz("100p", 1000)
    L = [f"VP vp 0 {vsup_p}" if l.startswith("VP ") else
         f"VN vn 0 {vsup_n}" if l.startswith("VN ") else l for l in L]
    if rfb:
        L += ["Rfb out inm 1m"]
    L += extra_lines
    ng = S.run(L, ["op"])
    v = lambda n: ng.vec(f"v({n})")[0]
    vp, vn = v("vp"), v("vn")
    # Resistor powers
    p_res = {
        "R1(1206,250mW)": (v("inm") - v("b1"))**2 / 1000.0,
        "R2(1206,250mW)": (v("inp") - v("b2"))**2 / 1000.0,
        "R3(0805,125mW)": (vp - v("c2"))**2 / 1500.0,
        "R5(0805,125mW)": (0 - v("b6"))**2 / 62000.0,
        "R6(0805,125mW)": (v("b6") - vn)**2 / 10000.0,
        "R7(0805,125mW)": (v("e6") - vn)**2 / 1000.0,
        "R8(0805,125mW)": (vp - v("e3"))**2 / 330.0,
        "R9(0805,125mW)": (v("c3") - vn)**2 / 12000.0,
        "R10(0805,125mW)": (v("out") - v("x"))**2 / 10000.0,
        "R11(0805,125mW)": v("x")**2 / 1000.0,
        "R15(0805,125mW)": (v("e4") - v("out"))**2 / 47.0,
        "R16(0805,125mW)": (v("out") - v("e5"))**2 / 47.0,
    }
    # Transistor approximate currents and powers
    ir8 = (vp - v("e3")) / 330.0
    ir9 = (v("c3") - vn) / 12000.0
    ir15 = (v("e4") - v("out")) / 47.0
    ir16 = (v("out") - v("e5")) / 47.0
    ir7 = (v("e6") - vn) / 1000.0
    pq3 = max(0.0, ir8 * (v("e3") - v("c3")))
    pq4 = max(0.0, ir15 * (vp - v("e4")))
    pq5 = max(0.0, ir16 * (v("e5") - vn))
    pq6 = max(0.0, ir7 * (v("tail") - v("e6")))
    hot_r = [(k, val*1e3) for k, val in p_res.items() if val > 0.05]
    hot_q = [(k, val*1e3) for k, val in [("Q3", pq3), ("Q4", pq4), ("Q5", pq5), ("Q6", pq6)] if val > 0.05]
    # Check any reverse Vbe > 1V
    veb = {
        "Q1": v("e1") - v("b1"),
        "Q2": v("e2") - v("b2"),
        "Q3": v("b2" if False else "c2") - v("e3"),
        "Q4": v("e4") - v("c3"),
        "Q5": v("c3") - v("e5"),
        "Q6": v("e6") - v("b6"),
        "Q7": v("out") - v("e4"),
        "Q8": v("e5") - v("out"),
    }
    rev_vbe = [(k, val) for k, val in veb.items() if val > 1.0]
    print(f"  {desc:42s}: hot_R={[(k, round(w,1)) for k,w in hot_r]} | hot_Q={[(k, round(w,1)) for k,w in hot_q]} | rev_Veb>1V={[(k, round(w,2)) for k,w in rev_vbe]}")

print("=== 1. GROUND CLIP ON EACH SIGNAL LOOP (TP1..TP14) ===")
tp_nodes = [
    ("TP1 (Q1 B)", "b1"), ("TP2 (Q2 B)", "b2"), ("TP13 (Q1 E)", "e1"), ("TP14 (Q2 E)", "e2"),
    ("TP3 (TAIL)", "tail"), ("TP5 (Q6 B)", "b6"), ("TP4 (Q6 E)", "e6"), ("TP6 (Q2 C)", "c2"),
    ("TP7 (Q3 E)", "e3"), ("TP8 (Q3 C)", "c3"), ("TP9 (OUT)", "out"), ("TP10 (X)", "x"),
]
for name, node in tp_nodes:
    check_stress(f"GND clip on {name}", ["Vin inp 0 0", f"Rclip {node} 0 0.01"])

print("\n=== 2. SINGLE RAIL, 30V RAIL, 20V INPUT, 100 OHM LOAD, OUT TIED TO IN+ ===")
check_stress("+15V only (-15V open/0V)", ["Vin inp 0 0"], vsup_p=14.6, vsup_n=0.0)
check_stress("-15V only (+15V open/0V)", ["Vin inp 0 0"], vsup_p=0.0, vsup_n=-14.6)
check_stress("+30V on +15V rail, -15V normal", ["Vin inp 0 0"], vsup_p=29.6, vsup_n=-14.6)
check_stress("+15V normal, -30V on -15V rail", ["Vin inp 0 0"], vsup_p=14.6, vsup_n=-29.6)
check_stress("+30V on +15V rail, 0V on -15V", ["Vin inp 0 0"], vsup_p=29.6, vsup_n=0.0)
check_stress("+20V into IN+, IN- at -20V (open loop)", ["Vin inp 0 20", "Vm inm 0 -20"], rfb=False)
check_stress("+20V into IN+ as follower", ["Vin inp 0 20"], rfb=True)
check_stress("-20V into IN+ as follower", ["Vin inp 0 -20"], rfb=True)
check_stress("OUT tied to IN+ (positive feedback)", ["Rpos out inp 1m", "Rin_gnd inm 0 1m"], rfb=False)
check_stress("100 ohm load on OUT, Vin=+10V follower", ["Vin inp 0 10", "Rload out 0 100"], rfb=True)
check_stress("100 ohm load on OUT, Vin=-10V follower", ["Vin inp 0 -10", "Rload out 0 100"], rfb=True)
