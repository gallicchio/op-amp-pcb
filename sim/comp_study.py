#!/usr/bin/env python3
"""Which compensation network makes the follower stable? (ngspice)"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngspice_lib import NgSpice
import opamp_sim as S

def core_rz(ccomp, rz, **kw):
    return S.core(ccomp=ccomp, rz=rz, **kw)

def margins(ccomp, rz, pot=0.5):
    lines = core_rz(ccomp, rz, pot=pot) + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
    ng = S.run(lines, ["ac dec 40 1 100meg"])
    f = [abs(x) for x in ng.vec("frequency")]; vo = ng.vec("v(out)")
    g = [abs(v) for v in vo]
    # unwrap phase
    ph = []
    prev = None
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
    return g[0], out

def step(ccomp, rz, mode="follower", amp=0.5):
    fb = ["Rfb out inm 1m"] if mode == "follower" else ["Rfb x inm 1m"]
    lines = core_rz(ccomp, rz) + fb + [f"Vin inp 0 pulse(-{amp} {amp} 5u 20n 20n 100u 200u)"]
    ng = S.run(lines, ["tran 10n 105u"])
    t = ng.vec("time"); vo = ng.vec("v(out)")
    late = [v for tt, v in zip(t, vo) if 60e-6 < tt < 105e-6]
    rise = [(tt, v) for tt, v in zip(t, vo) if 5e-6 < tt < 60e-6]
    final = sum(late) / len(late)
    pp = max(late) - min(late)
    peak = max(v for _, v in rise)
    # 2% settling time after the edge at 5us
    g = 1 if mode == "follower" else 11
    ts = None
    for i in range(len(rise)):
        if all(abs(v - final) < 0.02 * abs(2 * g * amp) for _, v in rise[i:]):
            ts = rise[i][0] - 5e-6; break
    return final, peak, pp, ts

if __name__ == "__main__":
    print(f"{'Ccomp':>6} {'Rz':>5} | {'A0':>5} | x1: f_unity  PM   | x11: f   PM   | follower step: final  peak  late p-p  t_settle | x11 step: final peak p-p t_settle")
    for ccomp, rz in (("100p", 0), ("100p", 1000), ("100p", 2200), ("220p", 1000), ("470p", 1000), ("470p", 2200),
                      ("1n", 470), ("1n", 1000), ("1n", 2200), ("2.2n", 1000), ("2.2n", 2200), ("4.7n", 1000)):
        a0, m = margins(ccomp, rz)
        f1, p1 = m["x1"]; f11, p11 = m["x11"]
        fo, pk, pp, ts = step(ccomp, rz, "follower", 0.5)
        fo2, pk2, pp2, ts2 = step(ccomp, rz, "x11", 0.1)
        fmt = lambda x, s=1e6: f"{x/s:5.2f}" if x else "  -  "
        print(f"{ccomp:>6} {rz:>5} | {a0:5.0f} | {fmt(f1)} MHz {p1 if p1 is not None else float('nan'):+5.0f} | {fmt(f11)} {p11 if p11 is not None else float('nan'):+5.0f} | "
              f"{fo:+.3f} {pk:+.3f} {pp*1e3:7.1f}mV {fmt(ts,1e-6) if ts else '  -  '}us | {fo2:+.3f} {pk2:+.3f} {pp2*1e3:6.1f}mV {fmt(ts2,1e-6) if ts2 else '  -  '}us")
