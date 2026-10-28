#!/usr/bin/env python3
"""Extra questions for the review: probe loading, coax on OUT, both FEEDBACK
sliders on, slew rate, crossover at TP8, short-circuit dissipation, and the
switch-combination states.  Imports the circuit from the project copy's
sim/opamp_sim.py and sim/comp_study.py unchanged; only adds loads/sources.
Run from this directory:  python3 sim_extra.py
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "project", "sim"))
import opamp_sim as S
import comp_study as CS


def margins_with(extra, label):
    """Open-loop margins (follower and x11) with extra netlist lines."""
    for rz in (1000, 1e-3):
        lines = CS.core_rz("100p", rz) + extra + [
            "Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
        ng = S.run(lines, ["ac dec 40 1 100meg"])
        f = [abs(x) for x in ng.vec("frequency")]
        vo = ng.vec("v(out)")
        g = [abs(v) for v in vo]
        ph, prev = [], None
        for v in vo:
            p = math.degrees(math.atan2(v.imag, v.real))
            if prev is not None:
                while p - prev > 180: p -= 360
                while p - prev < -180: p += 360
            ph.append(p); prev = p
        res = {}
        for name, tgt in (("x1", 1.0), ("x11", 11.0)):
            fu = pu = None
            for i in range(1, len(f)):
                if g[i-1] >= tgt > g[i]:
                    fu, pu = f[i], ph[i]; break
            res[name] = (fu, 180 + pu if pu is not None else None)
        tag = "1k  " if rz == 1000 else "bare"
        x1, x11 = res["x1"], res["x11"]
        print(f"  {label:34s} Rz={tag}: x1 fu={x1[0]/1e6:6.2f} MHz PM={x1[1]:+7.1f} | "
              f"x11 f={x11[0]/1e6:5.2f} MHz PM={x11[1]:+7.1f}")


print("== probe loading: 10x probe = 15 pF || 10 Meg on TP8 (c3) and TP6 (c2) ==")
margins_with([], "no probe (baseline)")
margins_with(["Cpr8 c3 0 15p", "Rpr8 c3 0 10meg"], "15pF on TP8 (Q3 C)")
margins_with(["Cpr6 c2 0 15p", "Rpr6 c2 0 10meg"], "15pF on TP6 (Q2 C)")
margins_with(["Cpr8 c3 0 15p", "Cpr6 c2 0 15p", "Rpr8 c3 0 10meg", "Rpr6 c2 0 10meg"],
             "15pF on both")

print()
print("== capacitive load on OUT, follower, Rz=1k (1 m coax ~ 100 pF, and 10 nF) ==")


def step_load(cload, mode="follower", amp=0.5, rz=1000):
    fb = ["Rfb out inm 1m"] if mode == "follower" else ["Rfb x inm 1m"]
    lines = CS.core_rz("100p", rz) + fb + [
        f"Cload out 0 {cload}",
        f"Vin inp 0 pulse(-{amp} {amp} 5u 20n 20n 100u 200u)"]
    ng = S.run(lines, ["tran 10n 105u"])
    t = ng.vec("time"); vo = ng.vec("v(out)")
    late = [v for tt, v in zip(t, vo) if 60e-6 < tt < 105e-6]
    final = sum(late) / len(late)
    pp = max(late) - min(late)
    rise = [(tt, v) for tt, v in zip(t, vo) if 5e-6 < tt < 60e-6]
    peak = max(v for _, v in rise)
    g = 1 if mode == "follower" else 11
    os_pct = 100 * (peak - final) / abs(2 * g * amp)
    # count zero crossings of error after settling window as a ringing meter
    err = [v - final for v in late]
    sc = sum(1 for a, b in zip(err, err[1:]) if a * b < 0)
    return final, pp, os_pct, sc


for cl in ("100p", "1n", "10n"):
    final, pp, osp, sc = step_load(cl)
    print(f"  follower, {cl} on OUT: overshoot {osp:5.1f} %, late p-p {pp*1e3:7.2f} mV, late zero-xings {sc}")

print()
print("== both FEEDBACK sliders on: R10 shorted -> follower with 1k load ==")
lines = CS.core_rz("100p", 1000) + ["Vin inp 0 dc 0", "Rfb out inm 1m"]  # pole 2: OUT->IN-
# pole 1 shorts X to IN- as well: X tied to inm:
lines += ["Rfb2 x inm 1m"]
ng = S.run(lines, ["op"])
print(f"  op: OUT = {ng.vec('v(out)')[0]*1e3:+.2f} mV, X = {ng.vec('v(x)')[0]*1e3:+.2f} mV, "
      f"tail OK, i(out divider through R11) = {ng.vec('v(x)')[0]/1000*1e3:+.3f} mA")
# margin with both on: feedback is unity from OUT (pole 2); with pole 1 also on,
# X is tied to IN- so R10 sits from OUT to IN- and R11 from IN- to ground:
# for the loop-gain question this is the follower loop with R10+R11 as the load
# and the tap pinned to the summing node -> same as a follower into ~1k.
m_lines = CS.core_rz("100p", 1000) + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9",
                                      "Rloadb out 0 1k"]
ng = S.run(m_lines, ["ac dec 40 1 100meg"])
f = [abs(x) for x in ng.vec("frequency")]; g = [abs(v) for v in ng.vec("v(out)")]
ph, prev = [], None
for v in ng.vec("v(out)"):
    p = math.degrees(math.atan2(v.imag, v.real))
    if prev is not None:
        while p - prev > 180: p -= 360
        while p - prev < -180: p += 360
    ph.append(p); prev = p
crossed = False
for i in range(1, len(f)):
    if g[i-1] >= 1 > g[i]:
        print(f"  both on (R10 shorted): x1 fu={f[i]/1e6:.2f} MHz PM={180+ph[i]:+.1f}")
        crossed = True
        break
if not crossed:
    print(f"  both on (R10 shorted): gain at 1 Hz = {g[0]:.0f}, at 100 MHz = {g[-1]:.3f} -- no unity crossing found")
    print(f"    gain floor: min = {min(g):.3f} at {f[g.index(min(g))]/1e6:.2f} MHz")

print()
print("== slew rate: follower, 10 V step ==")
lines = CS.core_rz("100p", 1000) + ["Rfb out inm 1m",
                                    "Vin inp 0 pulse(-5 5 5u 1n 1n 100u 200u)"]
ng = S.run(lines, ["tran 5n 130u"])
t = ng.vec("time"); vo = ng.vec("v(out)")


def slew_report(t, vo, t0, t1, direction):
    """10%-90% style slew over the edge between t0 and t1."""
    seg = [(tt, v) for tt, v in zip(t, vo) if t0 < tt < t1]
    v0, v1 = seg[0][1], seg[-1][1]
    lo, hi = (v0 + 0.2 * (v1 - v0), v0 + 0.8 * (v1 - v0)) if direction == "up" \
        else (v0 + 0.8 * (v1 - v0), v0 + 0.2 * (v1 - v0))
    ta = next(tt for tt, v in seg if (v >= lo if direction == "up" else v <= lo))
    tb = next(tt for tt, v in seg if (v >= hi if direction == "up" else v <= hi))
    return 0.6 * abs(v1 - v0) / (tb - ta)


print(f"  follower 10V step: slew up (20-80%) = {slew_report(t, vo, 5e-6, 30e-6, 'up')/1e6:.2f} V/us")
print(f"  follower 10V step: slew down (80-20%) = {slew_report(t, vo, 105e-6, 130e-6, 'down')/1e6:.2f} V/us")
print(f"  (tail-limited ceiling I/C = 1.39 mA / 100 pF = {1.39e-3/100e-12/1e6:.0f} V/us at the Miller node)")

print()
print("== x11, 2 V peak sine in: slew, crossover at TP8 ==")
lines = CS.core_rz("100p", 1000) + ["Rfb x inm 1m", "Vin inp 0 sin(0 2 1k)"]
ng = S.run(lines, ["tran 1u 2m"])
vo = ng.vec("v(out)"); v8 = ng.vec("v(c3)"); t = ng.vec("time")
dv = [(b - a) / (tb - ta) for (ta, a), (tb, b) in zip(zip(t, vo), zip(t[1:], vo[1:]))]
print(f"  OUT swing {min(vo):+.2f} .. {max(vo):+.2f} V, max |dV/dt| = {max(abs(x) for x in dv)/1e6:.2f} V/us")
# crossover dead band: sweep TP8 slowly open-loop, measure OUT vs v(c3)
lines = S.core() + ["Vin inp 0 0", "Vm inm 0 0"]  # open loop, both inputs grounded
ng = S.run(lines, ["op"])
print(f"  open loop rest: c3 = {ng.vec('v(c3)')[0]:+.3f} V, out = {ng.vec('v(out)')[0]:+.3f} V")
# dead band width: push current into c3 and watch out move
for i_ua in (-50, -20, -10, -5, 0, 5, 10, 20, 50):
    lines = S.core() + ["Vin inp 0 0", "Vm inm 0 0", f"Iinj 0 c3 DC {i_ua}u"]
    ng = S.run(lines, ["op"])
    print(f"    Iinj {i_ua:+4d} uA into Q3 C: c3 = {ng.vec('v(c3)')[0]:+8.3f} V, out = {ng.vec('v(out)')[0]:+8.3f} V")

print()
print("== short circuit: OUT to gnd, to +15, to -15; dissipation in Q4 / Q5 ==")
for where, net in (("gnd", "0"), ("+15V", "vp"), ("-15V", "vn")):
    for vin in (10, -10):
        lines = S.core() + [f"Vin inp 0 {vin}", "Rfb out inm 1meg", f"Rshort out {net} 0.01"]
        ng = S.run(lines, ["op"])
        vout = ng.vec("v(out)")[0]
        isc = vout / 0.01
        # Q4: Vce = vp - v(e4); Ic from v(e4) drop over R15 minus base share ~ isc
        ve4 = ng.vec("v(e4)")[0]; ve5 = ng.vec("v(e5)")[0]
        vp = ng.vec("v(vp)")[0]; vn = ng.vec("v(vn)")[0]
        i4 = (ve4 - vout) / 47.0; i5 = (vout - ve5) / 47.0
        p4 = abs((vp - ve4) * i4); p5 = abs((ve5 - vn) * i5)
        print(f"  OUT shorted to {where:4s}, Vin {vin:+3d} V: Ishort {isc*1e3:+7.1f} mA, "
              f"I(Q4e) {i4*1e3:+7.1f} mA P(Q4)~{p4*1e3:5.0f} mW, I(Q5e) {i5*1e3:+7.1f} mA P(Q5)~{p5*1e3:5.0f} mW")

print()
print("== limiter quiet in normal use: leakage/capacitance effect on swing ==")
lines = CS.core_rz("100p", 1000) + ["Rfb x inm 1m", "Vin inp 0 sin(0 2 1k)"]
ng = S.run(lines, ["tran 1u 2m"])
vo = ng.vec("v(out)")
print(f"  x11 2 V peak with limiter in place: swing {min(vo):+.2f} .. {max(vo):+.2f} V (results.json: -14.28 .. +13.41)")
# and with Q7/Q8/D5/D6 removed:
lines = [l for l in CS.core_rz("100p", 1000)
         if not l.startswith(("Q7", "Q8", "D5", "D6"))]
lines += ["Rfb x inm 1m", "Vin inp 0 sin(0 2 1k)"]
ng = S.run(lines, ["tran 1u 2m"])
vo = ng.vec("v(out)")
print(f"  same with Q7/Q8/D5/D6 removed:          swing {min(vo):+.2f} .. {max(vo):+.2f} V")

print()
print("== TAIL both on: resistor parallel to sink ==")
lines = S.core() + ["R4both tail vn 10k", "Vin inp 0 0", "Rfb out inm 1m"]
ng = S.run(lines, ["op"])
i_tail = (ng.vec("v(e6)")[0] + 15) / 1000 + (ng.vec("v(tail)")[0] + 15) / 10000
print(f"  tail current = {i_tail*1e3:.2f} mA (sink 1.39 + R4 share); c2 = {ng.vec('v(c2)')[0]:+.2f} V "
      f"(13.9 V normal), out = {ng.vec('v(out)')[0]*1e3:+.2f} mV")

print()
print("== wiper open at one end: tail broken ==")
lines = [l for l in S.core() if not l.startswith(("RV1a", "RV1b"))]
lines += ["RV1a e1 e2 50", "Vin inp 0 0", "Rfb out inm 1m"]
ng = S.run(lines, ["op"])
print(f"  wiper open (emitters joined by 50R track only): out = {ng.vec('v(out)')[0]:+.2f} V "
      f"c2 = {ng.vec('v(c2)')[0]:+.2f} V (output stuck at a rail: pair has no tail current)")
