#!/usr/bin/env python3
"""Simulations for Section 3 items 2d, 2e, 3, and 8."""
import math, os, sys
sys.path.insert(0, os.path.abspath("design_reviews/2026-10-27_Gemini-4-Argon/project/sim"))
from ngspice_lib import NgSpice
import opamp_sim as S
import comp_study as CS

def ac_margins(lines):
    ng = S.run(lines + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"], ["ac dec 40 1 100meg"])
    f = [abs(x) for x in ng.vec("frequency")]
    vo = ng.vec("v(out)")
    g = [abs(v) for v in vo]
    ph = []
    prev = None
    for v in vo:
        p = math.degrees(math.atan2(v.imag, v.real))
        if prev is not None:
            while p - prev > 180: p -= 360
            while p - prev < -180: p += 360
        ph.append(p); prev = p
    res = {"a0": g[0]}
    for name, tgt in (("x1", 1.0), ("x11", 11.0)):
        fu = pu = None
        for i in range(1, len(f)):
            if g[i-1] >= tgt > g[i]:
                # linear interpolation in log(f)
                t = (tgt - g[i-1]) / (g[i] - g[i-1])
                fu = f[i-1] * (f[i] / f[i-1]) ** t
                pu = ph[i-1] + t * (ph[i] - ph[i-1])
                break
        res[name] = (fu, (180 + pu) if pu is not None else None)
    return res

print("=================================================================")
print("2d. EFFECT OF LIMITER (Q7, Q8, D5, D6) ON NORMAL OPERATION")
print("=================================================================")
L_with = CS.core_rz("100p", 1000)
L_without = [l for l in L_with if not any(k in l for k in ("Q7", "D5", "Q8", "D6"))]
for name, L in [("With limiter (Q7,Q8,D5,D6)", L_with), ("Without Q7,Q8,D5,D6 (R15/R16 kept)", L_without)]:
    m = ac_margins(L)
    ng_sw = S.run(L + ["Rfb x inm 1m", "Vin inp 0 sin(0 2 1k)"], ["tran 2u 2m"])
    vo = ng_sw.vec("v(out)")
    print(f"  {name}:")
    print(f"    A0 = {m['a0']:.1f} | x1: f_u = {m['x1'][0]/1e6:.2f} MHz, PM = {m['x1'][1]:+.1f} deg | x11: f_11 = {m['x11'][0]/1e3:.1f} kHz, PM = {m['x11'][1]:+.1f} deg | swing = [{min(vo):+.2f}, {max(vo):+.2f}] V")

print("\n=================================================================")
print("3a. PROBE LOADING ON TP8 (Q3 C) AND TP6 (Q2 C) (10 pF & 15 pF + 10 MOhm)")
print("=================================================================")
for rz_label, rz in [("COMP 1 (100pF + 1k)", 1000), ("COMP 2 (bare 100pF)", 1e-3), ("COMP OFF (no C1)", None)]:
    print(f"\n--- {rz_label} ---")
    for probe_desc, extra in [
        ("No probe (3pF stray only)", []),
        ("10pF//10M on TP8 (Q3 C)", ["Cp8 c3 0 10p", "Rp8 c3 0 10meg"]),
        ("15pF//10M on TP8 (Q3 C)", ["Cp8 c3 0 15p", "Rp8 c3 0 10meg"]),
        ("10pF//10M on TP6 (Q2 C)", ["Cp6 c2 0 10p", "Rp6 c2 0 10meg"]),
        ("15pF//10M on TP6 (Q2 C)", ["Cp6 c2 0 15p", "Rp6 c2 0 10meg"]),
        ("15pF//10M on BOTH TP6 & TP8", ["Cp6 c2 0 15p", "Rp6 c2 0 10meg", "Cp8 c3 0 15p", "Rp8 c3 0 10meg"]),
    ]:
        if rz is None:
            L = S.core(ccomp="0") + extra
        else:
            L = CS.core_rz("100p", rz) + extra
        m = ac_margins(L)
        f1, pm1 = m["x1"]
        f11, pm11 = m["x11"]
        print(f"  {probe_desc:30s}: x1 f_u={f1/1e6 if f1 else 0:5.2f}MHz PM={pm1 if pm1 is not None else float('nan'):+6.1f}deg | x11 f={f11/1e3 if f11 else 0:6.1f}kHz PM={pm11 if pm11 is not None else float('nan'):+6.1f}deg")

print("\n=================================================================")
print("3b. COAX / CAPACITIVE LOAD ON OUT (FOLLOWER, COMP 1)")
print("=================================================================")
for cload in ("0", "100p", "470p", "1n", "10n"):
    extra = [] if cload == "0" else [f"Cload out 0 {cload}"]
    L = CS.core_rz("100p", 1000) + extra
    m = ac_margins(L)
    # Also run step response (+/-0.5V and +/-50mV)
    ng_st = S.run(L + ["Rfb out inm 1m", "Vin inp 0 pulse(-0.5 0.5 5u 20n 20n 100u 200u)"], ["tran 10n 105u"])
    vo = [v for t, v in zip(ng_st.vec("time"), ng_st.vec("v(out)")) if 5e-6 < t < 60e-6]
    final = vo[-1]
    pk = max(vo)
    ov = 100.0 * (pk - final) / 1.0
    print(f"  Cload={cload:>4s}: x1 f_u={m['x1'][0]/1e6:5.2f}MHz, PM={m['x1'][1]:+6.1f}deg | +/-0.5V step peak={pk:+.3f}V, final={final:+.3f}V, overshoot={ov:4.1f}%")

print("\n=================================================================")
print("3c. BOTH FEEDBACK SLIDERS ON (R10 SHORTED -> FOLLOWER WITH 1k LOAD)")
print("=================================================================")
L_both_fb = CS.core_rz("100p", 1000) + ["Rsw3_1 x inm 1m", "Rsw3_2 out inm 1m"]
ng_op = S.run(L_both_fb + ["Vin inp 0 0"], ["op"])
m_both = ac_margins(CS.core_rz("100p", 1000) + ["Rsw3_short out x 1m"])
ng_sw = S.run(L_both_fb + ["Vin inp 0 sin(0 12 1k)"], ["tran 2u 2m"])
vo = ng_sw.vec("v(out)")
print(f"  Both FEEDBACK on: Vos={ng_op.vec('v(out)')[0]*1e3:+.2f}mV, A0(with 1k load)={m_both['a0']:.1f}, PM={m_both['x1'][1]:+.1f}deg, max swing into R11(1k)=[{min(vo):+.2f}, {max(vo):+.2f}]V")

print("\n=================================================================")
print("3d. SLEW RATE AND CROSSOVER DEADBAND AT TP8 (Q3 C)")
print("=================================================================")
# Slew rate on 10V peak-to-peak (-5V to +5V) and 20V p-p (-10V to +10V) square wave as follower
for amp in (5.0, 10.0):
    L_sr = CS.core_rz("100p", 1000) + ["Rfb out inm 1m", f"Vin inp 0 pulse({-amp} {amp} 5u 10n 10n 50u 100u)"]
    ng_sr = S.run(L_sr, ["tran 5n 90u"])
    t = ng_sr.vec("time"); vo = ng_sr.vec("v(out)")
    # Rising edge at 5us: 10% to 90%
    v10, v90 = -0.8 * amp, 0.8 * amp
    t_r10 = next(tt for tt, vv in zip(t, vo) if tt > 5e-6 and vv >= v10)
    t_r90 = next(tt for tt, vv in zip(t, vo) if tt > 5e-6 and vv >= v90)
    sr_rise = (v90 - v10) / (t_r90 - t_r10) / 1e6
    # Falling edge at 55us: +80% to -80%
    t_f90 = next(tt for tt, vv in zip(t, vo) if tt > 55e-6 and vv <= v90)
    t_f10 = next(tt for tt, vv in zip(t, vo) if tt > 55e-6 and vv <= v10)
    sr_fall = (v90 - v10) / (t_f10 - t_f90) / 1e6
    print(f"  Follower +/-{amp:.0f}V step: SR_rise = {sr_rise:.2f} V/us, SR_fall = {sr_fall:.2f} V/us")

# Crossover deadband at TP8 (v(c3)) when v(out) crosses zero
L_xo = CS.core_rz("100p", 1000) + ["Rfb out inm 1m", "Vin inp 0 sin(0 0.5 1k)"]
ng_xo = S.run(L_xo, ["tran 1u 1m"])
vc3 = ng_xo.vec("v(c3)"); vout = ng_xo.vec("v(out)")
# Find v(c3) just above and below zero crossing of v(out) (say v(out) = +20mV and -20mV)
c3_pos = [c for c, o in zip(vc3, vout) if 0.015 < o < 0.025]
c3_neg = [c for c, o in zip(vc3, vout) if -0.025 < o < -0.015]
print(f"  Crossover jump at TP8 (Q3 C) for v(out) crossing 0 (+/-20mV): v(c3) jumps from {sum(c3_neg)/len(c3_neg):+.3f}V to {sum(c3_pos)/len(c3_pos):+.3f}V (span = {sum(c3_pos)/len(c3_pos) - sum(c3_neg)/len(c3_neg):.3f}V)")
