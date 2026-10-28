#!/usr/bin/env python3
"""Simulate every exercise in docs/HANDBOOK.md section 8 to verify what a student will actually observe."""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "project", "sim"))
import opamp_sim as S, comp_study as CS

print("=================================================================")
print("EXERCISE 2, 4, 5: OPEN-LOOP OPERATING POINT WITH IN+ = IN- = 0 V")
print("=================================================================")
# Look at what happens when FEEDBACK is OFF (open loop), IN- grounded, and IN+ driven by a generator with 0 DC offset!
for pot in (0.40, 0.45, 0.47, 0.48, 0.50, 0.52, 0.55, 0.60):
    ng = S.run(CS.core_rz("100p", 1000, pot=pot) + ["Vin inp 0 0", "Vm inm 0 0"], ["op"])
    v = lambda n: ng.vec(f"v({n})")[0]
    print(f"  pot={pot:.2f}: V(TP6 / Q2 C)={v('c2'):+7.3f} V | V(TP8 / Q3 C)={v('c3'):+7.3f} V | V(OUT)={v('out'):+7.3f} V")

print("\n--- What happens in Exercise 6 (Bring-up Step 6 -> Exercise 2/4/5)? ---")
print("In Bring-up Step 6 & Section 6, the student nulls the offset as a FOLLOWER (FEEDBACK 2) so V(OUT) = 0.000 V.")
# Find exact pot value that nulls V(OUT) = 0 in follower mode:
best_pot = 0.5
for p_int in range(400, 600):
    p = p_int / 1000.0
    ng = S.run(CS.core_rz("100p", 1000, pot=p) + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
    if abs(ng.vec("v(out)")[0]) < 0.0002:
        best_pot = p
        break
ng_fol = S.run(CS.core_rz("100p", 1000, pot=best_pot) + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
print(f"  Pot nulled as follower at pot={best_pot:.3f}: V(OUT, follower) = {ng_fol.vec('v(out)')[0]*1e3:+.3f} mV, V(c3) = {ng_fol.vec('v(c3)')[0]:+.3f} V")
# Now the student switches FEEDBACK OFF (open loop) for Exercise 2, 4, 5 without touching RV1!
ng_ol = S.run(CS.core_rz("100p", 1000, pot=best_pot) + ["Vin inp 0 0", "Vm inm 0 0"], ["op"])
print(f"  With THAT SAME pot={best_pot:.3f} in OPEN LOOP (IN+=0, IN-=0): V(TP6/c2)={ng_ol.vec('v(c2)')[0]:+.3f}V, V(TP8/c3)={ng_ol.vec('v(c3)')[0]:+.3f}V, V(OUT)={ng_ol.vec('v(out)')[0]:+.3f}V")

# Now test Exercise 4 ("Open loop, a millivolt or so in. TP8 against TP6: about 30, inverted again.")
# and Exercise 5 ("Open loop, a 50 mV triangle in. OUT against TP8: a dead band of about 1.2 V where neither Q4 nor Q5 conducts.")
for name, p_val in [("Pot at midpoint (0.500)", 0.500), (f"Pot nulled as follower ({best_pot:.3f})", best_pot)]:
    ng_tr = S.run(CS.core_rz("100p", 1000, pot=p_val) + ["Vm inm 0 0", "Vin inp 0 pulse(-0.05 0.05 0 500u 500u 1n 1m)"], ["tran 5u 1m"])
    vc2 = ng_tr.vec("v(c2)"); vc3 = ng_tr.vec("v(c3)"); vout = ng_tr.vec("v(out)")
    print(f"  Exercise 5 (50mV peak triangle, open loop) with {name}:")
    print(f"    TP6 (Q2 C): {min(vc2):+.3f}V .. {max(vc2):+.3f}V (p-p={(max(vc2)-min(vc2))*1e3:.1f}mV)")
    print(f"    TP8 (Q3 C): {min(vc3):+.3f}V .. {max(vc3):+.3f}V (p-p={max(vc3)-min(vc3):.2f}V)")
    print(f"    TP9 (OUT) : {min(vout):+.3f}V .. {max(vout):+.3f}V (p-p={max(vout)-min(vout):.2f}V)")

print("\n=================================================================")
print("EXERCISE 8: COMPENSATION (SW2 = 2 alone, and SW2 = both off, in x1 and x11)")
print("=================================================================")
for mode in ("follower", "x11"):
    for comp_name, ccomp, rz in [("SW2=2 (bare 100pF)", "100p", 1e-3), ("SW2=off (no C1)", "0", 1e-3)]:
        fb = ["Rfb out inm 1m"] if mode == "follower" else ["Rfb x inm 1m"]
        amp = 0.5 if mode == "follower" else 0.1
        L = (S.core(ccomp="0") if ccomp == "0" else CS.core_rz(ccomp, rz)) + fb + [f"Vin inp 0 pulse({-amp} {amp} 5u 20n 20n 50u 100u)"]
        ng = S.run(L, ["tran 5n 55u"])
        t = ng.vec("time"); vo = ng.vec("v(out)")
        seg = [(tt, v) for tt, v in zip(t, vo) if 6e-6 < tt < 50e-6]
        pk = max(v for _, v in seg); mn = min(v for _, v in seg)
        late = [v for tt, v in seg if tt > 35e-6]
        final = sum(late)/len(late)
        # Estimate ringing frequency from zero crossings around final
        crossings = [tt for (tt, v1), (_, v2) in zip(seg, seg[1:]) if (v1 - final)*(v2 - final) < 0]
        freq_mhz = (len(crossings)-1) / (2 * (crossings[-1] - crossings[0])) / 1e6 if len(crossings) >= 3 else 0.0
        print(f"  {mode:8s} {comp_name:20s}: peak={pk:+.3f}V, min={mn:+.3f}V, late_pp={(max(late)-min(late))*1e3:6.1f}mV, ring_freq={freq_mhz:5.2f}MHz")
