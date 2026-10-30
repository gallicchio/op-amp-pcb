#!/usr/bin/env python3
"""Place JLCPCB's own drawing of every part where the upload CPL says, and
measure it against the board's pads.

    python3 scripts/check_overlay.py

check_rotations.py fits each footprint in isolation; this takes the files that
are uploaded, as JLCPCB's placer reads them: each row's Mid X, Mid Y and
Rotation applied to the part's land pattern (scripts/easyeda.py, the drawing
JLCPCB's preview shows), then

  - every one of their pads within 0.25 mm of one of the board's pads of that
    part (posts and tabs included: a pin row alone is symmetric under 180
    degrees, CLAUDE_PCB.md section 8);
  - pad for pad by number where both sides number the same way, which is what
    puts a diode's cathode or a transistor's base on the right pad;
  - for the connectors whose pins are symmetric, the face a cable enters
    (their drawing's barrel or wire openings) pointing off the nearest edge;
  - the centre of their whole drawing (body, silkscreen and pads) within
    BODY_TOL of our courtyard's centre.  Pads alone cannot see a body that
    sits off its pins: rev A's 3362P footprint centred the body on the pins,
    Bourns and JLCPCB put it 1.3 mm toward pins 1 and 3, and the preview
    showed their body off our box (Jason nudged it, 2026-10-29).

Calibrated on the BNC, whose +90 was read off a real preview (Lorenz board).
"""
import csv, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import easyeda, parts
from check_rotations import turn
from sexp_parse import parse_file

STEM = "opamp"
TOL = 0.25                         # mm, any of their pads to the nearest of ours
BODY_TOL = 0.5                     # mm, their drawing's centre to our courtyard's (a terminal's side tab: 0.4)
# bodies known to sit off our courtyard: printed, not failed
KNOWN_BODY = {
    "C52754333": "3362P: rev A's footprint centres the body on the pins; Bourns has pins 1 and 3 3.53 mm "
                 "from the body's edge, so the body sits 1.3 mm toward them.  Harmless on rev A (nothing "
                 "under the overhang); fix the footprint in rev B",
}
# pad numbers that mean something else on their side: compare positions only
OTHER_NUMBERING = {
    "C41416668": "BNC: their centre pin is 5 and the posts 1-4, ours 1 and 2",
    "C2297": "KT-0805G: numbered the other way round; read at 0 in GPiBridge's preview",
    "C474881": "KF301-2P: identical screws; turned for its wire openings, their pin 1 sits in our hole 2",
    "C474882": "KF301-3P: identical screws; turned for its wire openings, their pin 1 sits in our hole 3",
}
# the face a cable enters, as a direction in their drawing (y down), read off
# its silkscreen: the BNC's barrel, the terminal blocks' wire openings
FACE = {
    "C41416668": ((0.0, 1.0), "barrel"),
    "C474881": ((0.0, 1.0), "wire openings"),
    "C474882": ((0.0, 1.0), "wire-entry arrows"),
}


def courtyards():
    """{ref: centre of its courtyard on the board}, y down."""
    out = {}
    for fp in parse_file(os.path.join(ROOT, "hardware", STEM + ".kicad_pcb")).kids("footprint"):
        ref = next((pr.atom(1) for pr in fp.kids("property") if pr.atom(0) == "Reference"), None)
        at = fp.first("at")
        pts = [(float(ln.first(k).atom(0)), float(ln.first(k).atom(1)))
               for ln in list(fp.kids("fp_line")) + list(fp.kids("fp_rect"))
               if ln.first("layer").atom(0) == "F.CrtYd" for k in ("start", "end")]
        if pts:
            c = ((min(p[0] for p in pts) + max(p[0] for p in pts)) / 2, (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2)
            t = turn(c, float(at.atom(2) or 0))
            out[ref] = (float(at.atom(0)) + t[0], float(at.atom(1)) + t[1])
    return out


def drawing_centre(code):
    """The centre of EasyEDA's whole drawing of a part (its bbox), from the land pattern's origin, y down."""
    res, _ = easyeda.svgs(code)
    fpd = next((r for r in res if r.get("docType") == 4 and r.get("bbox")), None)
    lp, _ = easyeda.land_pattern(code)
    if not fpd or not lp:
        return None
    b, (ox, oy) = fpd["bbox"], lp["origin"]
    return ((b["x"] + b["width"] / 2 - ox) * easyeda.UNIT, (b["y"] + b["height"] / 2 - oy) * easyeda.UNIT)


def main():
    root = os.path.join(ROOT, "out")
    import json
    geom = json.load(open(os.path.join(root, "pcb_geom.json")))
    crt = courtyards()
    H, W = geom["board_h"], geom["board_w"]
    pads = {}
    for p in geom["pads"]:
        pads.setdefault(p["ref"], []).append((p["pad"], p["x"], p["y"]))
    lcsc = {}
    with open(os.path.join(root, STEM, STEM + "_bom_jlcpcb_upload.csv"), newline="") as fh:
        for row in csv.DictReader(fh):
            for ref in row["Designator"].split(","):
                lcsc[ref.strip()] = row["LCSC Part #"]
    bad, n = [], 0
    with open(os.path.join(root, STEM, STEM + "_cpl_jlcpcb_upload.csv"), newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        ref, code = row["Designator"], lcsc.get(row["Designator"])
        if not code or ref not in pads:
            continue
        lp, _ = easyeda.land_pattern(code)
        if not lp or not lp["pads"]:
            print("  ?     %-5s %-10s no land pattern" % (ref, code))
            continue
        mx, my, rot = float(row["Mid X"]), H - float(row["Mid Y"]), float(row["Rotation"])
        theirs = [(q["number"], mx + turn((q["x"], q["y"]), rot)[0], my + turn((q["x"], q["y"]), rot)[1])
                  for q in lp["pads"]]
        ours = pads[ref]
        near = max(min(math.hypot(tx - ox, ty - oy) for _, ox, oy in ours) for _, tx, ty in theirs)
        msg = ["nearest pad %.2f mm" % near]
        ok = near <= TOL
        if code not in OTHER_NUMBERING:
            byn = []
            for num, tx, ty in theirs:
                mine = [(ox, oy) for k, ox, oy in ours if k == num]
                if mine:
                    byn.append(min(math.hypot(tx - ox, ty - oy) for ox, oy in mine))
            if byn:
                msg.append("by number %.2f mm" % max(byn))
                ok &= max(byn) <= TOL
        if code in FACE:
            (fx, fy), what = FACE[code]
            dx, dy = turn((fx, fy), rot)
            # outward normal of the nearest board edge
            edge = min(((mx, (-1, 0)), (W - mx, (1, 0)), (my, (0, -1)), (H - my, (0, 1))), key=lambda e: e[0])[1]
            dot = dx * edge[0] + dy * edge[1]
            msg.append("%s face %s" % (what, "off the edge" if dot > 0.9 else "INTO THE BOARD"))
            ok &= dot > 0.9
        flag = "ok" if ok else "BAD"
        bc = drawing_centre(code)
        if bc and ref in crt:
            t = turn(bc, rot)
            off = math.hypot(mx + t[0] - crt[ref][0], my + t[1] - crt[ref][1])
            if off > BODY_TOL:
                msg.append("their drawing %.2f mm off our courtyard's centre" % off)
                if code in KNOWN_BODY:
                    msg.append("known: " + KNOWN_BODY[code])
                    flag = "known" if ok else flag
                else:
                    ok, flag = False, "BAD"
        n += 1
        line = "  %-5s %-5s %-10s rot %5.1f  %s" % (flag, ref, code, rot, ", ".join(msg))
        if not ok or flag == "known" or code in FACE or ref in ("Q1", "Q3", "D1", "D3", "SW1", "LED1", "TP1"):
            print(line)
        if not ok:
            bad.append(line)
    print("\n%d placements overlaid; %d off their pads" % (n, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
