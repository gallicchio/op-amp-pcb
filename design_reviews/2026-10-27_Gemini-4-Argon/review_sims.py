#!/usr/bin/env python3
"""Comprehensive verification simulations for the review report."""
import math, os, sys
sys.path.insert(0, os.path.abspath("design_reviews/2026-10-27_Gemini-4-Argon/project/sim"))
from ngspice_lib import NgSpice
import opamp_sim as S
import comp_study as CS

print("=================================================================")
print("1. OPERATING POINT: SIMULATED (15.0V no D3/D4) vs ACTUAL BOARD (with B5819W D3/D4)")
print("=================================================================")

# Add B5819W model and R14=1k to see actual board behavior
B5819_MODEL = ".model DB5819 D(IS=3.5e-6 RS=0.18 N=1.08 CJO=110e-12 VJ=0.35 M=0.4 BV=40)"

def board_core(tail="cs", pot=0.5, ccomp="100p", rz=1000, vsup_in=15.0, use_schottky=True):
    P = 50.0
    ra, rb = max(P * pot, 0.01), max(P * (1 - pot), 0.01)
    L = [B5819_MODEL]
    if use_schottky:
        L += [
            f"VP_IN vp_in 0 {vsup_in}",
            f"VN_IN vn_in 0 {-vsup_in}",
            "D3 vp_in vp DB5819",
            "D4 vn vn_in DB5819",
            "R12 vp led1_a 10k", "Vled1 led1_a 0 2.7",
            "R13 0 led2_k 10k", "Vled2 led2_k vn 2.7",
        ]
    else:
        L += [f"VP vp 0 {vsup_in}", f"VN vn 0 {-vsup_in}"]
    L += [
        "R1 inm b1 1k", "R2 inp b2 1k", "D1 b1 b2 D4148", "D2 b2 b1 D4148",
        "Q1 vp b1 e1 Q3904", "Q2 c2 b2 e2 Q3904",
        f"RV1a e1 tail {ra}", f"RV1b e2 tail {rb}",
        "R3 vp c2 1.5k",
        "Q6 tail b6 e6 Q3904", "R5 0 b6 62k", "R6 b6 vn 10k", "R7 e6 vn 1k",
        "Q3 c3 c2 e3 Q3906", "R8 vp e3 330", "R9 c3 vn 12k",
    ]
    if ccomp != "0":
        if rz > 0:
            L += [f"Ccomp c3 cz {ccomp}", f"R14 cz c2 {rz}"]
        else:
            L += [f"Ccomp c3 c2 {ccomp}"]
    L += [
        "Q4 vp c3 e4 Q3904", "R15 e4 out 47", "Q7 c7 e4 out Q3904", "D5 c3 c7 D4148",
        "Q5 vn c3 e5 Q3906", "R16 out e5 47", "Q8 c8 e5 out Q3906", "D6 c8 c3 D4148",
        "R10 out x 10k", "R11 x 0 1k",
        "Cs2 c2 0 3p", "Cs3 c3 0 3p", "Cso out 0 3p"
    ]
    if tail == "r":
        L = [l for l in L if not l.startswith(("Q6", "R5", "R6", "R7"))] + ["R4 tail vn 10k"]
    return L

for label, use_sch, v_in in [
    ("opamp_sim.py (15.0V ideal rails, no D3/D4)", False, 15.0),
    ("14.6V ideal rails (matching vrail=14.6)", False, 14.6),
    ("15.0V input with B5819W D3/D4 + LEDs", True, 15.0),
]:
    ng = S.run(board_core(use_schottky=use_sch, vsup_in=v_in) + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
    vp = ng.vec("v(vp)")[0]
    vn = ng.vec("v(vn)")[0]
    c2 = ng.vec("v(c2)")[0]
    e3 = ng.vec("v(e3)")[0]
    c3 = ng.vec("v(c3)")[0]
    tail = ng.vec("v(tail)")[0]
    b6 = ng.vec("v(b6)")[0]
    e6 = ng.vec("v(e6)")[0]
    e1 = ng.vec("v(e1)")[0]
    e2 = ng.vec("v(e2)")[0]
    out = ng.vec("v(out)")[0]
    itail = (e6 - vn) / 1000.0
    iq3 = (vp - e3) / 330.0
    print(f"\n--- {label} ---")
    print(f"  TP11 (+15V) = {vp:+.3f} V (table: +14.6 V)")
    print(f"  TP12 (-15V) = {vn:+.3f} V (table: -14.6 V)")
    print(f"  TP6  (Q2 C) = {c2:+.3f} V (table: +13.9 V) | TP11 - TP6 = {vp-c2:.3f} V -> I(R3) = {(vp-c2)/1.5:.3f} mA")
    print(f"  TP7  (Q3 E) = {e3:+.3f} V (table: +14.6 V) | TP11 - TP7 = {vp-e3:.3f} V -> I(R8) = {iq3*1e3:.3f} mA")
    print(f"  TP8  (Q3 C) = {c3:+.3f} V (table: +0.5 V)")
    print(f"  TP13 (Q1 E) = {e1:+.3f} V (table: -0.6 V)")
    print(f"  TP14 (Q2 E) = {e2:+.3f} V (table: -0.6 V)")
    print(f"  TP3  (TAIL) = {tail:+.3f} V (table: -0.7 V)")
    print(f"  TP5  (Q6 B) = {b6:+.3f} V (table: -13.0 V)")
    print(f"  TP4  (Q6 E) = {e6:+.3f} V (table: -13.6 V) | TP4 - TP12 = {e6-vn:.3f} V -> I(R7) = {itail*1e3:.3f} mA")
    print(f"  TP9  (OUT)  = {out*1e3:+.2f} mV")

print("\n=================================================================")
print("2. OFFSET NULL & POT EXTREMES / FAULTS")
print("=================================================================")
for pot in (0.0, 0.25, 0.5, 0.75, 1.0):
    # Closed-loop follower offset
    ng_op = S.run(board_core(pot=pot, use_schottky=False) + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
    vos = ng_op.vec("v(out)")[0] * 1e3
    # Stage 1 and total AC gain around follower operating point
    ng_ac = S.run(board_core(pot=pot, use_schottky=False) + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"], ["ac dec 10 10 1meg"])
    f = [abs(x) for x in ng_ac.vec("frequency")]
    i100 = min(range(len(f)), key=lambda k: abs(f[k]-100))
    g1_cl = abs(ng_ac.vec("v(c2)")[i100])
    a0_cl = abs(ng_ac.vec("v(out)")[i100])
    # Open-loop grounded inputs operating point and gain
    ng_ol = S.run(board_core(pot=pot, use_schottky=False) + ["Vin inp 0 dc 0 ac 1", "Vm inm 0 0"], ["op", "ac dec 10 10 1meg"])
    g1_ol = abs(ng_ol.vec("v(c2)")[i100])
    print(f"  pot={pot:.2f}: Vos={vos:+6.2f} mV | closed-loop G1={g1_cl:.2f}, A0={a0_cl:.1f} | open-loop(Vin=0) G1={g1_ol:.2f}")

# Wiper open fault (Rwiper = 1G)
L_open_wiper = [l if not l.startswith("Q6") else "Ropen tail tail_q6 1G\nQ6 tail_q6 b6 e6 Q3904" for l in board_core(use_schottky=False)]
ng_ow = S.run(L_open_wiper + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
print(f"  Wiper OPEN: v(c2)={ng_ow.vec('v(c2)')[0]:+.3f}V, v(c3)={ng_ow.vec('v(c3)')[0]:+.3f}V, v(out)={ng_ow.vec('v(out)')[0]:+.3f}V")

# Ends shorted fault (e1 shorted to e2)
ng_es = S.run(board_core(use_schottky=False) + ["Rshort_e e1 e2 1m", "Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"], ["ac dec 10 10 1meg"])
f = [abs(x) for x in ng_es.vec("frequency")]
i100 = min(range(len(f)), key=lambda k: abs(f[k]-100))
print(f"  Ends SHORTED (pot=0.5): G1={abs(ng_es.vec('v(c2)')[i100]):.2f}, A0={abs(ng_es.vec('v(out)')[i100]):.1f}")
