#!/usr/bin/env python3
"""Which way round does JLCPCB place each part?  Fit JLCPCB's own land pattern (easyeda, scripts/easyeda.py) onto the
footprint on our board, pad number by pad number, at each quarter turn, and compare the turn that fits with
parts.JLC_ROTATION and parts.JLC_DATUM.  Ported from AMOD-and-RFMOD (its Prompt 17), the method CLAUDE_PCB.md
credits with 32 right of 32 on CostasLink rev A.

    python3 scripts/check_rotations.py            (the opamp board)

A part whose pads are all one number, or two of a two-terminal part with no polarity, is "symmetric" and skipped; a
fit whose best two turns are close is "ambiguous" and printed for a look.  AMOD-and-RFMOD wrote it after JLCPCB's
SOT-23 drawings turned out to be KiCad's turned 180 degrees while the table said 0.
"""
import csv, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parts, easyeda
from sexp_parse import parse_file

UNPOLAR = ("Resistor_SMD:", "Capacitor_SMD:", "Inductor_SMD:")
# fits that disagree with the table for a known reason: the table is right
KNOWN = {
    "C2297": "KT-0805G: read at 0 in GPiBridge's preview; JLCPCB numbers this LED's pads the other way round",
    "C41416668": "BNC-KYWE: their centre pin is 5 and the posts 1-4, ours 1 and 2; read at +90 on the Lorenz board, "
                 "whose footprint has the same pads and origin as this one",
    "C474881": "KF301-2P: the pin row is symmetric, so the pins fit either way; the turn is the body's, their wire "
               "openings drawn on +y and ours on -y (the board edge)",
    "C474882": "KF301-3P: as the 2P, their wire-entry arrows on +y",
}


def footprints(stem):
    """{ref: (fpid, [(pad, x, y)])} with pad positions footprint-local, unrotated."""
    root = parse_file(os.path.join(ROOT, "hardware", stem + ".kicad_pcb"))
    out = {}
    for fp in root.kids("footprint"):
        fpid = fp.atom(0)
        ref = None
        for pr in fp.kids("property"):
            if pr.atom(0) == "Reference":
                ref = pr.atom(1)
        pads = []
        for pd in fp.kids("pad"):
            at = pd.first("at")
            pads.append((pd.atom(0), float(at.atom(0)), float(at.atom(1))))
        out[ref] = (fpid, pads)
    return out


def lcsc_of(stem):
    out = {}
    with open(os.path.join(ROOT, "out", stem, stem + "_bom_jlcpcb_upload.csv")) as fh:
        for row in csv.DictReader(fh):
            for ref in row["Designator"].split(","):
                out[ref.strip()] = row["LCSC Part #"]
    return out


def centroids(pads):
    """{pad number: centre of its pads}, and the numbers that have one pad only."""
    acc = {}
    for num, x, y in pads:
        if not num:
            continue
        acc.setdefault(num, []).append((x, y))
    cen = {k: (sum(p[0] for p in v) / len(v), sum(p[1] for p in v) / len(v)) for k, v in acc.items()}
    return cen, {k for k, v in acc.items() if len(v) == 1}


def turn(p, a):
    """Rotate by a degrees counter-clockwise as seen on a y-down board (KiCad's sense)."""
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return (p[0] * c + p[1] * s, -p[0] * s + p[1] * c)


def fit(ours, theirs, single=None):
    """[(rms, correction, datum)] over the four corrections, best first.  JLCPCB's drawing D = our footprint F turned by
    a; the CPL then needs -a.  The datum (where their origin sits in our footprint) comes from the numbers with one pad
    on both sides when there are two or more of them: a SOT-89's tab is pad 2 with its middle lead, drawn differently."""
    keys = sorted(set(ours) & set(theirs))
    if len(keys) < 2:
        return None
    tkeys = sorted(single) if single and len(single) >= 2 else keys
    res = []
    for a in (0, 90, 180, 270):
        F = [turn(ours[k], a) for k in keys]
        D = [theirs[k] for k in keys]
        fx, fy = sum(p[0] for p in F) / len(F), sum(p[1] for p in F) / len(F)
        dx, dy = sum(p[0] for p in D) / len(D), sum(p[1] for p in D) / len(D)
        e = math.sqrt(sum((f[0] - fx - d[0] + dx) ** 2 + (f[1] - fy - d[1] + dy) ** 2 for f, d in zip(F, D)) / len(F))
        tk = list(tkeys)
        while True:                       # drop the worst-fitting pad while the rest disagree (a tab drawn as pad 2)
            Ft = [turn(ours[k], a) for k in tk]
            Dt = [theirs[k] for k in tk]
            fx, fy = sum(p[0] for p in Ft) / len(Ft), sum(p[1] for p in Ft) / len(Ft)
            dx, dy = sum(p[0] for p in Dt) / len(Dt), sum(p[1] for p in Dt) / len(Dt)
            r = [math.hypot(f[0] - fx - d[0] + dx, f[1] - fy - d[1] + dy) for f, d in zip(Ft, Dt)]
            if len(tk) <= 2 or max(r) < 0.5:
                break
            tk.pop(r.index(max(r)))
        # their origin in our footprint's own frame: D = turn(F, a) + t, so their (0, 0) is turn(-t, -a) in ours
        datum = turn((fx - dx, fy - dy), -a)
        res.append((e, (360 - a) % 360, datum))
    return sorted(res, key=lambda r: r[0])


def main(stems):
    seen, bad = {}, []
    for stem in stems:
        fps, codes = footprints(stem), lcsc_of(stem)
        for ref, (fpid, pads) in sorted(fps.items()):
            code = codes.get(ref)
            if not code or code in seen:
                continue
            seen[code] = (stem, ref, fpid)
            ours, ours1 = centroids(pads)
            if len(ours) < 2 or (len(ours) == 2 and fpid.startswith(UNPOLAR)):
                continue
            try:
                lp, _ = easyeda.land_pattern(code)
            except Exception as e:
                print("  %-10s %-6s %-46s cannot fetch JLCPCB's drawing: %s" % (code, ref, fpid[:46], e))
                continue
            if not lp:
                print("  %-10s %-6s %-46s no drawing" % (code, ref, fpid[:46]))
                continue
            theirs, theirs1 = centroids([(p["number"], p["x"], p["y"]) for p in lp["pads"]])
            r = fit(ours, theirs, ours1 & theirs1)
            if r is None:
                print("  %-10s %-6s %-46s pad numbers do not match (ours %s, theirs %s)" % (code, ref, fpid[:46], sorted(ours)[:6], sorted(theirs)[:6]))
                continue
            (e0, best, datum), (e1, nxt, _) = r[0], r[1]
            table = parts.JLC_ROTATION.get(code, (0, "absent"))
            flag = "ok" if table[0] == best else ("known" if code in KNOWN else "DIFFERS")
            amb = " ambiguous (%.2f vs %.2f mm)" % (e0, e1) if e1 - e0 < 0.15 else ""
            have = getattr(parts, "JLC_DATUM", {}).get(code, (0.0, 0.0))[:2]
            dat = ""
            if math.hypot(datum[0] - have[0], datum[1] - have[1]) > 0.15:
                dat = "; their origin at (%.3f, %.3f) in ours, table (%.3f, %.3f)" % (datum[0], datum[1], have[0], have[1])
                if not amb:
                    flag = "DATUM" if flag == "ok" else flag
            line = "  %-7s %-10s %-6s %-46s fits +%-3d (rms %.2f mm); table +%d %s%s%s" % (flag, code, ref, fpid[:46], best, e0, table[0], table[1], amb, dat)
            print(line)
            if flag not in ("ok", "known") and not amb:
                bad.append(line)
    print("\n%d codes checked; %d differ from the table" % (len(seen), len(bad)))
    for b in bad:
        print(b)
    return 1 if bad else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    sys.exit(main(args or ["opamp"]))
