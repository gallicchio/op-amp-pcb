#!/usr/bin/env python3
"""Model sensitivity: phase margins with slow/low-beta transistors and with
datasheet-max capacitances, plus more stray C.  Uses the copy's sim modules."""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "project", "sim"))
import opamp_sim as S
import comp_study as CS


def margins_with_models(models, label, stray="3p"):
    """Same measurement as comp_study.margins but with swapped .model cards."""
    import ngspice_lib
    saved = S.MODELS
    try:
        S.MODELS = models
        lines = CS.core_rz("100p", 1000, stray=stray) + [
            "Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
        ng = S.run(lines, ["ac dec 40 1 100meg"])
        f = [abs(x) for x in ng.vec("frequency")]
        g = [abs(v) for v in ng.vec("v(out)")]
        ph, prev = [], None
        for v in ng.vec("v(out)"):
            p = math.degrees(math.atan2(v.imag, v.real))
            if prev is not None:
                while p - prev > 180: p -= 360
                while p - prev < -180: p += 360
            ph.append(p); prev = p
        for i in range(1, len(f)):
            if g[i-1] >= 1 > g[i]:
                print(f"  {label:52s}: A0={g[0]:5.0f}  x1 fu={f[i]/1e6:6.2f} MHz  PM={180+ph[i]:+6.1f}")
                return
        print(f"  {label:52s}: no unity crossing (A0={g[0]:.0f}, floor {min(g):.3f})")
    finally:
        S.MODELS = saved


M = S.MODELS
margins_with_models(M, "as shipped (Bf 300/200, Cjc 4/4.5p, TF 350p)")

# low beta (datasheet mins at 1 mA are 70/80; 100/100 is a conservative floor)
margins_with_models([M[0].replace("Bf=300", "Bf=100"), M[1].replace("Bf=200", "Bf=100"), M[2]],
                    "Bf=100/100 (near datasheet floor)")
margins_with_models([M[0].replace("Bf=300", "Bf=70"), M[1].replace("Bf=200", "Bf=80"), M[2]],
                    "Bf=70/80 (datasheet min at 1 mA)")

# slow: TF doubled (fT ~150 MHz), Cjc/Cje at max +50%
slow0 = M[0].replace("TF=350E-12", "TF=700E-12").replace("CJC=4E-12", "CJC=6E-12").replace("CJE=8E-12", "CJE=12E-12")
slow1 = M[1].replace("TF=350E-12", "TF=700E-12").replace("CJC=4.5E-12", "CJC=6.8E-12").replace("CJE=10E-12", "CJE=15E-12")
margins_with_models([slow0, slow1, M[2]], "slow: fT ~150 MHz, caps +50%")

# more stray capacitance
margins_with_models(M, "stray 10 pF instead of 3 pF", stray="10p")

# both FEEDBACK sliders on is covered in sim_extra; here: TAIL=10k margins
def margins_tail_r():
    lines = [l for l in CS.core_rz("100p", 1000) if not l.startswith(("Q6", "R5", "R6", "R7"))]
    lines += ["R4 tail vn 10k", "Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
    ng = S.run(lines, ["ac dec 40 1 100meg"])
    f = [abs(x) for x in ng.vec("frequency")]
    g = [abs(v) for v in ng.vec("v(out)")]
    ph, prev = [], None
    for v in ng.vec("v(out)"):
        p = math.degrees(math.atan2(v.imag, v.real))
        if prev is not None:
            while p - prev > 180: p -= 360
            while p - prev < -180: p += 360
        ph.append(p); prev = p
    for i in range(1, len(f)):
        if g[i-1] >= 1 > g[i]:
            print(f"  TAIL 2 (10k resistor), follower: A0={g[0]:5.0f}  fu={f[i]/1e6:6.2f} MHz  PM={180+ph[i]:+6.1f}")
            return
margins_tail_r()

# both COMPENSATION sliders off: no Miller cap at all, x11 and follower
lines = [l for l in CS.core_rz("100p", 1000) if not l.startswith(("Ccomp", "Rz"))]
lines += ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
ng = S.run(lines, ["ac dec 40 1 100meg"])
f = [abs(x) for x in ng.vec("frequency")]
g = [abs(v) for v in ng.vec("v(out)")]
ph, prev = [], None
for v in ng.vec("v(out)"):
    p = math.degrees(math.atan2(v.imag, v.real))
    if prev is not None:
        while p - prev > 180: p -= 360
        while p - prev < -180: p += 360
    ph.append(p); prev = p
for name, tgt in (("x1", 1.0), ("x11", 11.0)):
    for i in range(1, len(f)):
        if g[i-1] >= tgt > g[i]:
            print(f"  COMPENSATION both off: {name} f={f[i]/1e6:6.2f} MHz  PM={180+ph[i]:+6.1f}")
            break
