#!/usr/bin/env python3
"""Questions the project's simulation was not asked (design review, 2026-10-24).

Runs against the review copy's sim/ modules (project/sim); writes nothing but stdout.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "project", "sim"))
import opamp_sim as S
import comp_study as CS


def margins(lines, label):
    """Open-loop AC: unity-gain and |A|=11 crossings with the phase margin there."""
    L = lines + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
    ng = S.run(L, ["ac dec 40 1 100meg"])
    f = [abs(x) for x in ng.vec("frequency")]; vo = ng.vec("v(out)")
    g = [abs(v) for v in vo]
    ph, prev = [], None
    for v in vo:
        p = math.degrees(math.atan2(v.imag, v.real))
        if prev is not None:
            while p - prev > 180: p -= 360
            while p - prev < -180: p += 360
        ph.append(p); prev = p
    out = {}
    for name, tgt in (("x1", 1.0), ("x11", 11.0)):
        fu = pu = None
        for i in range(1, len(f)):
            if g[i-1] >= tgt > g[i]:
                fu, pu = f[i], ph[i]; break
        out[name] = (fu, (180 + pu) if pu is not None else None)
    def fmt(k):
        fu, pm = out[k]
        return f"{fu/1e6:6.2f} MHz PM {pm:+6.1f} deg" if fu else "   no crossing         "
    print(f"  {label:50s} A0 {g[0]:5.0f}  x1: {fmt('x1')}  x11: {fmt('x11')}")
    return out


def step(lines, label, mode="follower", amp=0.5, load=None):
    fb = ["Rfb out inm 1m"] if mode == "follower" else ["Rfb x inm 1m"]
    L = lines + fb + [f"Vin inp 0 pulse(-{amp} {amp} 5u 20n 20n 100u 200u)"] + (load or [])
    ng = S.run(L, ["tran 10n 105u"])
    t = ng.vec("time"); vo = ng.vec("v(out)")
    late = [v for tt, v in zip(t, vo) if 60e-6 < tt < 105e-6]
    rise = [(tt, v) for tt, v in zip(t, vo) if 5e-6 < tt < 60e-6]
    final = sum(late) / len(late); pp = max(late) - min(late)
    peak = max(v for _, v in rise)
    g = 1 if mode == "follower" else 11
    print(f"  {label:50s} final {final:+.3f} V  peak {peak:+.3f} V  overshoot {100*(peak-final)/(2*g*amp):5.1f} %  late p-p {pp*1e3:7.1f} mV")


def no_limiter(L):
    """The book's bare push-pull: Q4/Q5 emitters straight to OUT."""
    drop = ("R15", "Q7", "D5", "R16", "Q8", "D6")
    L = [l for l in L if not l.startswith(drop)]
    return L + ["R15 e4 out 0.001", "R16 out e5 0.001"]


def no_comp(L):
    return [l for l in L if not l.startswith(("Ccomp", "Rz"))]


print("=== 1. baseline (reproduce the project's numbers) ===")
margins(CS.core_rz("100p", 1000), "as built, 100 pF + 1 k")
margins(CS.core_rz("100p", 1e-3), "bare 100 pF")

print("\n=== 2. a 10x scope probe (15 pF) on the loops: open-loop margins ===")
for rz, tag in ((1000, "with 1 k"), (1e-3, "bare 100 pF")):
    for extra, where in (([], "no probe"), (["Cp c3 0 15p"], "probe on TP8 (Q3 C)"),
                         (["Cp c2 0 15p"], "probe on TP6 (Q2 C)"),
                         (["Cp c3 0 15p", "Cq c2 0 15p"], "probes on TP6 and TP8"),
                         (["Cp out 0 15p"], "probe on TP9 (OUT)"),
                         (["Cp e3 0 15p"], "probe on TP7 (Q3 E)")):
        margins(CS.core_rz("100p", rz) + extra, f"{tag:12s} {where}")
print("  -- follower steps, 0.5 V, with the 1 k:")
for extra, where in (([], "no probe"), (["Cp c3 0 15p"], "probe on TP8"), (["Cp c2 0 15p"], "probe on TP6")):
    step(CS.core_rz("100p", 1000) + extra, where)

print("\n=== 3. cable capacitance on OUT (a metre of coax = 100 pF) ===")
for c in ("100p", "300p", "1n", "10n"):
    margins(CS.core_rz("100p", 1000) + [f"Ccable out 0 {c}"], f"as built, {c} on OUT")
    step(CS.core_rz("100p", 1000) + [f"Ccable out 0 {c}"], f"   step, {c} on OUT")
print("  -- without the limiter's 47 ohm (the bare push-pull the rev B '47 ohm in series' note assumed):")
for c in ("100p", "1n"):
    margins(no_limiter(CS.core_rz("100p", 1000)) + [f"Ccable out 0 {c}"], f"bare push-pull, {c} on OUT")
    step(no_limiter(CS.core_rz("100p", 1000)) + [f"Ccable out 0 {c}"], f"   step, {c} on OUT")

print("\n=== 4. does the limiter itself change the loop? (Q7/Q8/D5/D6 removed, emitters to OUT) ===")
margins(no_limiter(CS.core_rz("100p", 1000)), "no limiter, with 1 k")
margins(no_limiter(CS.core_rz("100p", 1e-3)), "no limiter, bare")

print("\n=== 5. COMPENSATION as wired: pole 2 alone opens the chain = no compensation ===")
margins(no_comp(S.core()), "no compensation (both off, or 2 alone)")
step(no_comp(S.core()), "   follower step, no compensation")
step(no_comp(S.core()), "   x11 step, no compensation", mode="x11", amp=0.1)

print("\n=== 6. both FEEDBACK on: R10 shorted, follower into 1 k ===")
ng = S.run(S.core() + ["Rsh out x 0.001", "Rfb out inm 1m", "Vin inp 0 0"], ["op"])
print(f"  OUT = {ng.vec('v(out)')[0]*1e3:+.1f} mV, X = {ng.vec('v(x)')[0]*1e3:+.1f} mV")
margins(CS.core_rz("100p", 1000) + ["Rsh out x 0.001"], "R10 shorted (1 k load)")

print("\n=== 7. the output shorted: currents and powers (follower asked for +/-10 V) ===")
def short_case(label, short_to, vin):
    L = S.core() + [f"Vin inp 0 {vin}", "Rfb out inm 1m", f"Rshort out {short_to} 0.01"]
    ng = S.run(L, ["op"])
    v = lambda n: ng.vec("v(" + n + ")")[0]
    i15 = (v("e4") - v("out")) / 47; i16 = (v("out") - v("e5")) / 47
    p4 = (15 - v("e4")) * i15; p5 = (v("e5") + 15) * i16
    print(f"  {label:30s} OUT {v('out'):+7.3f} V  I(R15) {i15*1e3:+6.1f} mA  I(R16) {i16*1e3:+6.1f} mA  "
          f"P(Q4) {p4*1e3:5.0f} mW  P(Q5) {p5*1e3:5.0f} mW  Q3 C {v('c3'):+7.2f} V")
short_case("to ground, +10 V asked", "0", 10)
short_case("to ground, -10 V asked", "0", -10)
short_case("to -15 V rail, +10 V asked", "vn", 10)
short_case("to -15 V rail, 0 V asked", "vn", 0)
short_case("to +15 V rail, -10 V asked", "vp", -10)
short_case("to +15 V rail, 0 V asked", "vp", 0)
print("  -- 100 ohm load, +/-10 V asked:")
for vin in (10, -10):
    ng = S.run(S.core() + [f"Vin inp 0 {vin}", "Rfb out inm 1m", "Rload out 0 100"], ["op"])
    v = lambda n: ng.vec("v(" + n + ")")[0]
    print(f"    vin {vin:+3d}: OUT {v('out'):+.2f} V, I(R15) {(v('e4')-v('out'))/47*1e3:+.1f} mA, "
          f"P(Q4) {(15-v('e4'))*(v('e4')-v('out'))/47*1e3:.0f} mW, P(Q5) {(v('e5')+15)*(v('out')-v('e5'))/47*1e3:.0f} mW")

print("\n=== 8. input abuse, open loop (inputs driven directly) ===")
def abuse(label, vp_in, vm_in):
    L = S.core() + [f"Vin inp 0 {vp_in}", f"Vm inm 0 {vm_in}"]
    ng = S.run(L, ["op"]); v = lambda n: ng.vec("v(" + n + ")")[0]
    i1 = (v("inm") - v("b1")) / 1000; i2 = (v("inp") - v("b2")) / 1000
    print(f"  {label:24s} b1 {v('b1'):+7.2f} b2 {v('b2'):+7.2f} e {v('e1'):+7.2f} V  I(R1) {i1*1e3:+6.2f} mA {i1*i1*1000*1e3:4.0f} mW  "
          f"I(R2) {i2*1e3:+6.2f} mA {i2*i2*1000*1e3:4.0f} mW  Vbe1 {v('b1')-v('e1'):+5.2f} Vbe2 {v('b2')-v('e2'):+5.2f}  OUT {v('out'):+6.2f}")
abuse("IN+ = +15, IN- = 0", 15, 0)
abuse("IN+ = -15, IN- = 0", -15, 0)
abuse("IN+ = +15, IN- = -15", 15, -15)
abuse("IN+ = -15, IN- = +15", -15, 15)
abuse("IN+ = +20, IN- = 0", 20, 0)
abuse("IN+ = 0, IN- = -20", 0, -20)

print("\n=== 9. the null trimmer at its ends ===")
for pot in (0.0, 0.5, 1.0):
    ng = S.run(S.core(pot=pot) + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
    print(f"  pot {pot:.1f}: follower OUT {ng.vec('v(out)')[0]*1e3:+7.2f} mV;", end="")
    margins(CS.core_rz("100p", 1000, pot=pot), "")

print("\n=== 10. slew rate (follower, +/-5 V square) ===")
for a, b, lab in ((-5, 5, "rising"), (5, -5, "falling")):
    L = CS.core_rz("100p", 1000) + ["Rfb out inm 1m", f"Vin inp 0 pulse({a} {b} 5u 20n 20n 100u 200u)"]
    ng = S.run(L, ["tran 5n 30u"])
    t = ng.vec("time"); vo = ng.vec("v(out)")
    seg = [(tt, v) for tt, v in zip(t, vo) if 5e-6 < tt < 25e-6]
    if b > a:
        t1 = next(tt for tt, v in seg if v > -4); t2 = next(tt for tt, v in seg if v > 4)
    else:
        t1 = next(tt for tt, v in seg if v < 4); t2 = next(tt for tt, v in seg if v < -4)
    print(f"  {lab}: 8 V in {(t2-t1)*1e6:.2f} us = {8/((t2-t1)*1e6):.1f} V/us; extreme {max(v for _, v in seg) if b > a else min(v for _, v in seg):+.2f} V")

print("\n=== 11. x11 into real loads ===")
for amp, load in ((1.0, "1k"), (1.3, "1k"), (1.0, "330"), (0.5, "100")):
    L = CS.core_rz("100p", 1000) + ["Rfb x inm 1m", f"Vin inp 0 sin(0 {amp} 1k)", f"Rload out 0 {load}"]
    ng = S.run(L, ["tran 2u 2m"]); vo = ng.vec("v(out)")
    print(f"  {amp} V peak in, {load} ohm load: OUT {min(vo):+.2f} .. {max(vo):+.2f} V (ideal +/-{11*amp:.1f})")
