#!/usr/bin/env python3
"""Second batch: stage gains, and what a scope's ground clip on the wrong loop does."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "project", "sim"))
import opamp_sim as S
import comp_study as CS

print("=== A. stage gains at 100 Hz, open loop, IN- grounded for AC (where does 138 come from?) ===")
L = CS.core_rz("100p", 1000) + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
ng = S.run(L, ["ac dec 10 10 1meg"])
f = [abs(x) for x in ng.vec("frequency")]
i = min(range(len(f)), key=lambda k: abs(f[k] - 100))
g = {n: abs(ng.vec("v(" + n + ")")[i]) for n in ("c2", "c3", "out")}
print(f"  |c2| = {g['c2']:.1f}  |c3| = {g['c3']:.1f}  |out| = {g['out']:.1f}   -> stage 2 = {g['c3']/g['c2']:.1f}, push-pull at rest = {g['out']/g['c3']:.2f}")
L = CS.core_rz("100p", 1000) + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9", "Rload out 0 1k"]
ng = S.run(L, ["ac dec 10 10 1meg"])
g = {n: abs(ng.vec("v(" + n + ")")[i]) for n in ("c2", "c3", "out")}
print(f"  with 1 k load: |c2| = {g['c2']:.1f}  |c3| = {g['c3']:.1f}  |out| = {g['out']:.1f}")
# with the output biased into conduction: a 2 V DC offset on IN+ through the x11 loop, then AC
L = CS.core_rz("100p", 1000) + ["Vin inp 0 dc 0.5 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
ng = S.run(L, ["ac dec 10 10 1meg"])
g = {n: abs(ng.vec("v(" + n + ")")[i]) for n in ("c2", "c3", "out")}
print(f"  biased (OUT at +0.5 V): |c2| = {g['c2']:.1f}  |c3| = {g['c3']:.1f}  |out| = {g['out']:.1f}")

print("\n=== B. a scope's ground clip on a signal loop (node shorted to ground), open loop, inputs as given ===")
print("    power in the 0805 resistors (rated 0.125 W) and in the transistors")
cases = [
    ("TP6 Q2 C -> 0, IN+ = IN- = 0", "c2", 0, 0),
    ("TP7 Q3 E -> 0, IN+ = IN- = 0", "e3", 0, 0),
    ("TP8 Q3 C -> 0, IN+ = +0.1, IN- = 0", "c3", 0.1, 0),
    ("TP8 Q3 C -> 0, IN+ = -0.1, IN- = 0", "c3", -0.1, 0),
    ("TP3 TAIL -> 0, IN+ = IN- = 0", "tail", 0, 0),
    ("TP4 Q6 E -> 0, IN+ = IN- = 0", "e6", 0, 0),
    ("TP5 Q6 B -> 0, IN+ = IN- = 0", "b6", 0, 0),
    ("TP13 Q1 E -> 0, IN+ = IN- = 0", "e1", 0, 0),
    ("TP9 OUT -> 0, IN+ = +1, IN- = 0", "out", 1, 0),
]
for label, node, vp, vm in cases:
    L = S.core() + [f"Vin inp 0 {vp}", f"Vm inm 0 {vm}", f"Rclip {node} 0 0.01"]
    ng = S.run(L, ["op"]); v = lambda n: ng.vec("v(" + n + ")")[0]
    p = {
        "R3": (15 - v("c2")) ** 2 / 1500, "R8": (15 - v("e3")) ** 2 / 330, "R9": (v("c3") + 15) ** 2 / 12000,
        "R7": (v("e6") + 15) ** 2 / 1000, "R6": (v("b6") + 15) ** 2 / 10000,
        "Q3": (15 - v("e3")) / 330 * (v("e3") - v("c3")), "Q6": (v("e6") + 15) / 1000 * (v("tail") - v("e6")),
        "Q4": (15 - v("e4")) * (v("e4") - v("out")) / 47, "Q5": (v("e5") + 15) * (v("out") - v("e5")) / 47,
    }
    hot = {k: round(x * 1e3) for k, x in p.items() if x > 0.05}
    irail = (15 - v("e3")) / 330 + (15 - v("c2")) / 1500 + (v("e4") - v("out")) / 47 + 1.2e-3
    print(f"  {label:36s} +rail about {irail*1e3:5.1f} mA; over 50 mW: {hot if hot else 'nothing'}")
