#!/usr/bin/env python3
"""Simulate the Lab 5L discrete op-amp as the board builds it (ngspice via ctypes).

Prints the operating point, open-loop gain and phase, closed-loop step response
as a follower and as the x11 amplifier, output swing, the null trimmer's reach,
and the common-mode gain with the tail resistor against the current source.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngspice_lib import NgSpice

MODELS = [
    ".model Q3904 NPN(IS=1E-14 VAF=100 Bf=300 IKF=0.4 XTB=1.5 BR=4 CJC=4E-12 CJE=8E-12 RB=20 RC=0.1 RE=0.1 TR=250E-9 TF=350E-12 ITF=1 VTF=2 XTF=3)",
    ".model Q3906 PNP(IS=1E-14 VAF=100 Bf=200 IKF=0.4 XTB=1.5 BR=4 CJC=4.5E-12 CJE=10E-12 RB=20 RC=0.1 RE=0.1 TR=250E-9 TF=350E-12 ITF=1 VTF=2 XTF=3)",
    ".model D4148 D(IS=2.52e-9 RS=0.568 N=1.752 CJO=4e-12 M=0.4 TT=20e-9 BV=75)",
    # B5819W, fitted to its datasheet's 25 C forward curve: 0.27 V at 0.1 A, 0.55 V at
    # 1 A; at the board's 4 mA it drops 0.18 V, so the rails sit near +/-14.8 V
    ".model DB5819 D(IS=7.5e-6 N=1.1 RS=0.2 CJO=150e-12 M=0.4 BV=40)",
]


def core(tail="cs", pot=0.5, ccomp="100p", rz=1000, bf_n=300, bf_p=200, stray="3p", vsup=15):
    """The board's op-amp: nodes inm inp out (the jacks, where the feedback is taken)
    and pp (the push-pull's emitters, which reach OUT through R17), rails vp vn after D3 / D4 from a +/-vsup bench supply, ground 0.
    COMPENSATION 1 by default: ccomp in series with rz from Q3 C to Q2 C; rz=0 is
    the bare capacitor (position 2), ccomp="0" none at all."""
    P = 50.0
    ra, rb = max(P * pot, 0.01), max(P * (1 - pot), 0.01)
    L = [f"VPS vps 0 {vsup}", f"VNS vns 0 {-vsup}", "D3 vps vp DB5819", "D4 vn vns DB5819",
         "C2 vp 0 10u", "C3 vp 0 100n", "C4 vn 0 10u", "C5 vn 0 100n",
         "R1 inm b1 1k", "R2 inp b2 1k", "D1 b1 b2 D4148", "D2 b2 b1 D4148",
         "Q1 vp b1 e1 Q3904", "Q2 c2 b2 e2 Q3904",
         f"RV1a e1 tail {ra}", f"RV1b e2 tail {rb}",
         "R3 vp c2 1.5k",
         "Q6 tail b6 e6 Q3904", "R5 0 b6 62k", "R6 b6 vn 10k", "R7 e6 vn 1k",
         "Q3 c3 c2 e3 Q3906", "R8 vp e3 330", "R9 c3 vn 12k",
         f"Ccomp c3 cz {ccomp}", f"Rz cz c2 {max(float(rz), 1e-3)}",
         # the book's bare push-pull; R17 (not in the book) inside the loop is the output's
         # only protection: a short at the jacks draws about 40 mA and Q4 / Q5 stay cool
         "Q4 vp c3 pp Q3904", "Q5 vn c3 pp Q3906", "R17 pp out 330",
         "R10 out x 10k", "R11 x 0 1k",
         f"Cs2 c2 0 {stray}", f"Cs3 c3 0 {stray}", f"Cso pp 0 {stray}"]
    if str(ccomp) in ("0", "None"):
        L = [l for l in L if not l.startswith(("Ccomp", "Rz"))]
    if tail == "r":
        L = [l for l in L if not l.startswith(("Q6", "R5", "R6", "R7"))] + ["R4 tail vn 10k"]
    return L


def run(lines, cmds):
    ng = NgSpice()
    ng.circuit(["opamp"] + MODELS + lines + [".end"])
    for c in cmds:
        ng.cmd(c)
    return ng


def op_point():
    print("=== operating point, follower (IN- tied to OUT), IN+ = 0 ===")
    ng = run(core() + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
    for n in ("c2", "e3", "c3", "out", "tail", "e6", "b6", "x"):
        print(f"  v({n:4s}) = {ng.vec('v('+n+')')[0]:+8.4f} V")
    vp, vn = ng.vec("v(vp)")[0], ng.vec("v(vn)")[0]
    ir7 = (ng.vec("v(e6)")[0] - vn) / 1000
    print(f"  rails {vp:+.3f} / {vn:+.3f} V after D3 / D4")
    print(f"  tail current (R7) = {ir7*1e3:.3f} mA;  Q3 Ie = {(vp-ng.vec('v(e3)')[0])/330*1e3:.3f} mA")
    print(f"  input offset as a follower (OUT with IN+ = 0): {ng.vec('v(out)')[0]*1e3:+.2f} mV")
    print("=== operating point, open loop, IN+ = IN- = 0 (where does OUT sit?) ===")
    ng = run(core() + ["Vin inp 0 0", "Vm inm 0 0"], ["op"])
    print(f"  v(c3) = {ng.vec('v(c3)')[0]:+.3f} V,  v(out) = {ng.vec('v(out)')[0]:+.3f} V")


def open_loop(tail="cs", pot=0.5, ccomp="100p"):
    # DC bias held by feedback through a huge inductor; AC applied through a huge cap
    lines = core(tail=tail, pot=pot, ccomp=ccomp) + [
        "Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
    # Cin grounds inm for AC: differential drive = v(inp)-v(inm) = 1
    ng = run(lines, ["ac dec 20 1 100meg"])
    f = ng.vec("frequency")
    vo = ng.vec("v(out)")
    f = [abs(x) for x in f]
    gain = [abs(v) for v in vo]
    ph, prev = [], None
    for v in vo:
        p_ = math.degrees(math.atan2(v.imag, v.real))
        if prev is not None:
            while p_ - prev > 180: p_ -= 360
            while p_ - prev < -180: p_ += 360
        ph.append(p_); prev = p_
    a0 = gain[0]
    # unity-gain crossing and phase there
    fu, pu = None, None
    for i in range(1, len(f)):
        if gain[i-1] >= 1 > gain[i]:
            fu, pu = f[i], ph[i]
            break
    f11, p11 = None, None
    for i in range(1, len(f)):
        if gain[i-1] >= 11 > gain[i]:
            f11, p11 = f[i], ph[i]
            break
    print(f"=== open loop, tail={tail}, pot={pot}, Ccomp={ccomp}: A0 = {a0:.0f} ({20*math.log10(a0):.1f} dB)")
    for tgt in (1e3, 1e4, 1e5, 1e6, 1e7):
        i = min(range(len(f)), key=lambda k: abs(math.log(f[k]/tgt)))
        print(f"    {tgt:9.0f} Hz: |A| = {gain[i]:8.2f}  phase {ph[i]:+7.1f} deg")
    print(f"    unity gain at {fu/1e6 if fu else float('nan'):.2f} MHz, phase {pu if pu else float('nan'):+.0f} deg"
          f" -> phase margin as follower {180+pu if pu else float('nan'):.0f} deg")
    print(f"    |A| = 11 at {f11/1e6 if f11 else float('nan'):.3f} MHz, phase {p11 if p11 else float('nan'):+.0f} deg"
          f" -> phase margin at x11 {180+p11 if p11 else float('nan'):.0f} deg")
    return a0


def closed_loop_step(mode="follower", ccomp="100p", amp=0.5):
    fb = ["Rfb out inm 1m"] if mode == "follower" else ["Rfb x inm 1m"]
    lines = core(ccomp=ccomp) + fb + [f"Vin inp 0 pulse(-{amp} {amp} 10u 20n 20n 100u 200u)"]
    ng = run(lines, ["tran 20n 220u"])
    t = ng.vec("time"); vo = ng.vec("v(out)")
    # settle value and overshoot after the first rising edge
    seg = [(tt, v) for tt, v in zip(t, vo) if 10e-6 < tt < 110e-6]
    peak = max(v for _, v in seg); final = seg[-1][1]
    g = (1 if mode == "follower" else 11)
    # ringing: count sign changes of (v - final) after 2us past the edge
    tail_ = [v - final for tt, v in seg if tt > 30e-6]
    sc = sum(1 for a, b in zip(tail_, tail_[1:]) if a * b < 0)
    print(f"=== step {mode}, Ccomp={ccomp}: +/-{amp} V in -> final {final:+.3f} V (ideal {g*amp:+.3f}), "
          f"peak {peak:+.3f} V, overshoot {100*(peak-final)/max(abs(2*g*amp),1e-9):.0f} %, "
          f"late zero crossings {sc}")
    return final, peak, sc


def swing():
    lines = core() + ["Rfb x inm 1m", "Vin inp 0 sin(0 2 1k)"]
    ng = run(lines, ["tran 2u 2m"])
    vo = ng.vec("v(out)")
    print(f"=== x11, 2 V peak in: OUT swings {min(vo):+.2f} .. {max(vo):+.2f} V (into 11k)")
    lines = core() + ["Rfb out inm 1m", "Vin inp 0 sin(0 0.05 1k)", "Rload out 0 1k"]
    ng = run(lines, ["tran 2u 2m"])
    vo = ng.vec("v(out)"); vi = ng.vec("v(inp)")
    print(f"=== follower, 50 mV peak, 1k load: OUT {min(vo)*1e3:+.1f} .. {max(vo)*1e3:+.1f} mV (crossover shows as a wiggle)")


def null_range():
    print("=== offset null: follower offset vs pot position (IN+ = 0)")
    for pot in (0.0, 0.25, 0.5, 0.75, 1.0):
        ng = run(core(pot=pot) + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
        print(f"    pot {pot:.2f}: OUT = {ng.vec('v(out)')[0]*1e3:+7.2f} mV")
    print("=== beta spread: follower offset with Q1 Bf=150 / Q2 Bf=300 (pot centred)")
    L = core()
    L = [l.replace("Q1 vp b1 e1 Q3904", "Q1 vp b1 e1 Q3904L") for l in L]
    ng = NgSpice()
    ng.circuit(["opamp"] + MODELS + [MODELS[0].replace("Q3904", "Q3904L").replace("Bf=300", "Bf=150")]
               + L + ["Vin inp 0 0", "Rfb out inm 1m", ".end"])
    ng.cmd("op")
    print(f"    OUT = {ng.vec('v(out)')[0]*1e3:+.2f} mV")


def cmrr():
    print("=== common-mode gain of stage 1 (both inputs driven, measured at c2), tail R vs current source")
    for tail in ("r", "cs"):
        lines = core(tail=tail) + ["Vin inp 0 dc 0 ac 1", "Vm inm inp 0"]
        ng = run(lines, ["ac dec 10 10 1meg"])
        f = [abs(x) for x in ng.vec("frequency")]; v = [abs(x) for x in ng.vec("v(c2)")]
        i100 = min(range(len(f)), key=lambda k: abs(f[k]-100)); i10k = min(range(len(f)), key=lambda k: abs(f[k]-1e4))
        print(f"    tail={tail}: Gcm(stage1) = {v[i100]:.4f} at 100 Hz, {v[i10k]:.4f} at 10 kHz")
    lines = core() + ["Vin inp 0 dc 0 ac 1", "Vm inm 0 0", "Lfb out inm 1e9"]
    # differential gain of stage 1 for comparison: open loop, inm grounded
    lines = core() + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"]
    ng = run(lines, ["ac dec 10 10 1meg"])
    f = [abs(x) for x in ng.vec("frequency")]; v = [abs(x) for x in ng.vec("v(c2)")]
    i100 = min(range(len(f)), key=lambda k: abs(f[k]-100))
    print(f"    Gdiff(stage1) = {v[i100]:.2f} at 100 Hz (pot centred: 25 ohm per emitter)")


def results_json(path):
    """The numbers the schematic, the silkscreen and the documents quote, from one run."""
    import comp_study as CS
    out = {"date": __import__("datetime").date.today().isoformat()}
    ng = run(core() + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
    out["op"] = {n: round(ng.vec("v(" + n + ")")[0], 3) for n in ("c2", "e3", "c3", "out", "tail", "e6", "b6", "x")}
    vp, vn = ng.vec("v(vp)")[0], ng.vec("v(vn)")[0]
    out["i_tail_ma"] = round((ng.vec("v(e6)")[0] - vn) / 1000 * 1e3, 3)
    out["i_q3_ma"] = round((vp - ng.vec("v(e3)")[0]) / 330 * 1e3, 3)
    out["vos_follower_mv"] = round(ng.vec("v(out)")[0] * 1e3, 2)
    out["vrail"] = round((vp - vn) / 2, 2)
    out["vschottky"] = round(15 - vp, 3)
    a0, m = CS.margins("100p", 1000)
    out["a0"] = round(a0, 1)
    out["pm_x1"] = round(m["x1"][1], 1)
    out["f_unity_mhz"] = round(m["x1"][0] / 1e6, 2)
    out["pm_x11"] = round(m["x11"][1], 1)
    out["f11_khz"] = round(m["x11"][0] / 1e3, 1)
    a0b, mb = CS.margins("100p", 1e-3)
    out["pm_x1_bare"] = round(mb["x1"][1], 1) if mb["x1"][1] is not None else None
    out["pm_x11_bare"] = round(mb["x11"][1], 1) if mb["x11"][1] is not None else None
    fo, pk, pp, ts = CS.step("100p", 1000, "follower", 0.5)
    out["ts_x1_us"] = round(ts * 1e6, 2) if ts else None
    out["overshoot_x1_pct"] = round(100 * (pk - fo) / 1.0, 1)
    fo2, pk2, pp2, ts2 = CS.step("100p", 1000, "x11", 0.1)
    out["g11"] = round(fo2 / 0.1, 2)
    out["ts_x11_us"] = round(ts2 * 1e6, 2) if ts2 else None
    # swing
    lines = core() + ["Rfb x inm 1m", "Vin inp 0 sin(0 2 1k)"]
    ng = run(lines, ["tran 2u 2m"])
    vo = ng.vec("v(out)")
    out["swing"] = [round(min(vo), 2), round(max(vo), 2)]
    # null range
    offs = []
    for pot in (0.0, 1.0):
        ng = run(core(pot=pot) + ["Vin inp 0 0", "Rfb out inm 1m"], ["op"])
        offs.append(ng.vec("v(out)")[0] * 1e3)
    out["null_mv"] = round((offs[1] - offs[0]) / 2, 1)
    # swing at the jacks into 1k, the follower driven to the rails
    sw = []
    for vin in (14, -14):
        ng = run(core() + [f"Vin inp 0 {vin}", "Rfb out inm 1m", "Rl out 0 1k"], ["op"])
        sw.append(round(ng.vec("v(out)")[0], 2))
    out["swing_1k"] = sw
    # a short at the jacks, open loop and driven hard both ways (no input current can
    # reach the short this way; a follower's would, through the clamp): the current,
    # and the most Q4 or Q5 ever dissipates, found by sweeping a follower's target
    isc = []
    for vin in (0.2, -0.2):
        ng = run(core() + [f"Vin inp 0 {vin}", "Vm inm 0 0", "Rshort out 0 0.01"], ["op"])
        isc.append(round(abs(ng.vec("v(out)")[0] / 0.01) * 1e3, 1))
    out["isc_ma"] = max(isc)
    pq = [0.0]
    for k in range(1, 57):
        for sgn in (1, -1):
            ng = run(core() + [f"Vin inp 0 {sgn * k / 4}", "Rfb out inm 1m", "Rshort out 0 0.01"], ["op"])
            vp, vn, vpp = (ng.vec(f"v({n})")[0] for n in ("vp", "vn", "pp"))
            i = ng.vec("v(out)")[0] / 0.01
            pq.append(abs(i) * ((vp - vpp) if i > 0 else (vpp - vn)))
            isc.append(round(abs(i) * 1e3, 1))
    out["isc_ma"] = max(isc)
    out["pq_short_mw"] = round(max(pq) * 1e3)
    # a cable on the jacks: the follower stepped 4 -> 6 V, -6 -> -4 V and across 0 with
    # 100 pF (a metre of coax) up to 2.2 nF; the worst ringing left 30 us after the edge
    worst = 0.0
    for c in ("100p", "470p", "1n", "2.2n"):
        for lo, hi in ((4, 6), (-6, -4), (-0.1, 0.1)):
            ng = run(core() + ["Rfb out inm 1m", f"Cl out 0 {c}", f"Vin inp 0 pulse({lo} {hi} 10u 20n 20n 50u 100u)"],
                     ["tran 10n 60u"])
            seg = [x for tt, x in zip(ng.vec("time"), ng.vec("v(out)")) if 40e-6 < tt < 58e-6]
            worst = max(worst, max(seg) - min(seg))
    out["ring_cable_mv"] = round(worst * 1e3, 1)
    out["pr17_short_mw"] = round(max(isc) ** 2 * 330 / 1e3)
    # common-mode gain of stage 1
    for tail, key in (("r", "gcm_r"), ("cs", "gcm_cs")):
        ng = run(core(tail=tail) + ["Vin inp 0 dc 0 ac 1", "Vm inm inp 0"], ["ac dec 10 10 1meg"])
        f = [abs(x) for x in ng.vec("frequency")]; vv = [abs(x) for x in ng.vec("v(c2)")]
        i = min(range(len(f)), key=lambda k: abs(f[k] - 100))
        out[key] = round(vv[i], 4)
    ng = run(core() + ["Vin inp 0 dc 0 ac 1", "Lfb out inm 1e9", "Cin inm 0 1e9"], ["ac dec 10 10 1meg"])
    f = [abs(x) for x in ng.vec("frequency")]; vv = [abs(x) for x in ng.vec("v(c2)")]
    i100 = min(range(len(f)), key=lambda k: abs(f[k] - 100))
    out["gdiff1"] = round(vv[i100], 2)
    out["g2_stage"] = round(abs(ng.vec("v(c3)")[i100]) / abs(ng.vec("v(c2)")[i100]), 1)
    out["g2"] = round(a0 / out["gdiff1"], 1)
    json.dump(out, open(path, "w"), indent=1, sort_keys=True)
    return out


if __name__ == "__main__":
    import json
    if "--json" in sys.argv:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")
        r = results_json(path)
        print(f"  wrote {os.path.relpath(path)}: A0 {r['a0']}, follower PM {r['pm_x1']} deg, "
              f"x11 {r['g11']} at {r['f11_khz']} kHz, Vos {r['vos_follower_mv']} mV, null +/-{r['null_mv']} mV")
        sys.exit(0)
    op_point()
    for cc in ("100p", "0", "470p"):
        open_loop(ccomp=cc)
    for cc in ("100p", "470p"):
        closed_loop_step("follower", cc)
        closed_loop_step("x11", cc, amp=0.1)
    swing()
    null_range()
    cmrr()
