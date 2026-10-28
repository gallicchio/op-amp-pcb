#!/usr/bin/env python3
"""Detailed simulations for Section 3 items 2, 3, 7, 8."""
import math, os, sys
sys.path.insert(0, os.path.abspath("design_reviews/2026-10-27_Gemini-4-Argon/project/sim"))
from ngspice_lib import NgSpice
import opamp_sim as S
import comp_study as CS

print("=================================================================")
print("2d. OUTPUT CURRENT LIMIT: BOTH POLARITIES, SHORTS TO GND, +15V, -15V")
print("=================================================================")

for vshort_name, vshort in [("GND (0V)", 0.0), ("+15V rail", 15.0), ("-15V rail", -15.0)]:
    print(f"\n--- OUT shorted to {vshort_name} ({vshort:+.1f} V) ---")
    for vin in (1.0, 10.0, -1.0, -10.0):
        L = S.core() + [
            f"Vin inp 0 {vin}",
            "Rfb out inm 1m",
            f"Vsh out_sh 0 {vshort}",
            "Rshort out out_sh 0.01"
        ]
        ng = S.run(L, ["op"])
        v = lambda n: ng.vec(f"v({n})")[0]
        i_short = (v("out") - vshort) / 0.01
        i_r15 = (v("e4") - v("out")) / 47.0
        i_r16 = (v("out") - v("e5")) / 47.0
        i_r8 = (15.0 - v("e3")) / 330.0
        i_r9 = (v("c3") - (-15.0)) / 12000.0
        # Q4 Vce = 15 - v(e4), Ic4 ~ i_r15 (minus Q7 base current; actually i_r15 + i_e7 = i_short, wait: Q4 emitter current goes into R15 AND Q7 base!)
        # Wait: Q7 collector goes through D5 to c3, Q7 emitter goes to out!
        # Let's measure exact Q4, Q5, Q7, Q8 collector currents by inserting 1m sense resistors or reading node voltages
        v_r15 = v("e4") - v("out")
        v_r16 = v("out") - v("e5")
        print(f"  Vin={vin:+5.1f}V: I_short={i_short*1e3:+6.2f}mA | V(R15)={v_r15*1e3:+6.1f}mV (I_R15={i_r15*1e3:+5.2f}mA) | V(R16)={v_r16*1e3:+6.1f}mV (I_R16={i_r16*1e3:+5.2f}mA) | I(R8)={i_r8*1e3:5.2f}mA | V(c2)={v('c2'):+6.2f}V, V(c3)={v('c3'):+6.2f}V")

# Measure exact transistor currents and power dissipation in Q4, Q5, Q7, Q8, R8 under shorts
print("\n--- Exact transistor currents & powers under short-circuit conditions ---")
def sim_short_detail(vin, vshort, vsup=14.6):
    L = S.core(vsup=vsup)
    # Replace Q4, Q5, Q7, Q8 collectors with 1m sense resistors to measure Ic accurately
    L = [l.replace("Q4 vp c3 e4", "Rc4 vp c4_c 1m\nQ4 c4_c c3 e4")
          .replace("Q5 vn c3 e5", "Rc5 vn c5_c 1m\nQ5 c5_c c3 e5")
          for l in L]
    L += [f"Vin inp 0 {vin}", "Rfb out inm 1m", f"Vsh out_sh 0 {vshort}", "Rshort out out_sh 0.001"]
    ng = S.run(L, ["op"])
    v = lambda n: ng.vec(f"v({n})")[0]
    ic4 = (vsup - v("c4_c")) / 1e-3
    ic5 = (v("c5_c") - (-vsup)) / 1e-3
    ir15 = (v("e4") - v("out")) / 47.0
    ir16 = (v("out") - v("e5")) / 47.0
    ishort = (v("out") - vshort) / 0.001
    ir8 = (vsup - v("e3")) / 330.0
    pq4 = ic4 * (vsup - v("e4"))
    pq5 = ic5 * (v("e5") - (-vsup))
    pr8 = (vsup - v("e3")) * ir8
    print(f"  vsup=+/-{vsup}V, Vin={vin:+5.1f}V, Vshort={vshort:+6.1f}V:")
    print(f"    I_short={ishort*1e3:+6.2f}mA | Ic(Q4)={ic4*1e3:5.2f}mA, P(Q4)={pq4*1e3:5.1f}mW | Ic(Q5)={ic5*1e3:5.2f}mA, P(Q5)={pq5*1e3:5.1f}mW | I(R15)={ir15*1e3:5.2f}mA, I(R16)={ir16*1e3:5.2f}mA | I(R8)={ir8*1e3:5.2f}mA, P(R8)={pr8*1e3:4.1f}mW")

for vsup in (15.0, 14.6):
    sim_short_detail(+10.0, 0.0, vsup)
    sim_short_detail(-10.0, 0.0, vsup)
    sim_short_detail(+10.0, -vsup, vsup)
    sim_short_detail(-10.0, +vsup, vsup)
