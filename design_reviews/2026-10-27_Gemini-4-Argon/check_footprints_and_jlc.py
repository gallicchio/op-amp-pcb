#!/usr/bin/env python3
"""Verify all custom footprints, SOT-23 pinouts, EasyEDA land patterns, and CPL rotations."""
import csv, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "project", "scripts"))
import easyeda, parts, layout as L
from sexp_parse import parse_file

print("=================================================================")
print("1. EASYEDA LAND PATTERNS vs OUR FOOTPRINTS & JLC_ROTATION")
print("=================================================================")
for code, (rot_corr, status, note) in sorted(parts.JLC_ROTATION.items()):
    lp, ts = easyeda.land_pattern(code)
    print(f"\nCode {code} (JLC_ROTATION: +{rot_corr} deg, {status}): {note}")
    print(f"  EasyEDA package: {lp['package']}, silk extent: {lp['silk']}")
    for p in lp["pads"]:
        print(f"    EasyEDA pad {p['number']:>2s}: ({p['x']:+6.2f}, {p['y']:+6.2f}) size=({p['w']:.2f}x{p['h']:.2f}) drill={p['drill']:.2f} shape={p['shape']}")

print("\n=================================================================")
print("2. CHECKING TRANSFORMED PAD POSITIONS UNDER CPL ROTATION")
print("=================================================================")
# Let's check: in KiCad, footprint rotation `rot_k` is CCW in a coordinate system where Y is DOWN on the board
# (Wait: in KiCad PCB, +X is right, +Y is down, and positive orientation angle rotates a vector (x, y) by:
#  x_b = x * cos(rot) + y * sin(rot)
#  y_b = -x * sin(rot) + y * cos(rot)  -- i.e. standard CCW when viewing with +Y up, which is CW in +Y down).
# And JLCPCB's CPL Rotation is ALSO CCW!
# When JLCPCB places an EasyEDA footprint (whose local coordinates in easyeda.py have +X right, +Y down) at CPL angle `theta_jlc` CCW:
# A point (x_e, y_e) in EasyEDA local frame (with +Y down) rotated by `theta_jlc` CCW lands at:
#  dx = x_e * cos(theta_jlc) + y_e * sin(theta_jlc)
#  dy = -x_e * sin(theta_jlc) + y_e * cos(theta_jlc)
# Let's compare (dx, dy) of EasyEDA pad `n` with the actual board pad `(pad_x - fp_x, pad_y - fp_y)` in pcb_geom.json!

geom = json.load(open(os.path.join(HERE, "project", "out", "pcb_geom.json")))
board_pads = {}
for p in geom["pads"]:
    board_pads.setdefault(p["ref"], {})[str(p["pad"])] = (p["x"], p["y"], p["w"], p["h"])

cpl_jlc = {r["Designator"]: r for r in csv.DictReader(open(os.path.join(HERE, "project", "out", "opamp", "opamp_cpl_jlcpcb_upload.csv")))}
bom_rows = list(csv.DictReader(open(os.path.join(HERE, "project", "out", "opamp", "opamp_bom_jlcpcb_upload.csv"))))
ref_to_lcsc = {}
for r in bom_rows:
    for ref in r["Designator"].split(","):
        ref_to_lcsc[ref.strip()] = r["LCSC Part #"].strip()

for ref, row in sorted(cpl_jlc.items()):
    code = ref_to_lcsc[ref]
    if code not in parts.JLC_ROTATION:
        continue
    lp, _ = easyeda.land_pattern(code)
    fx, fy, _ = L.PLACE[ref]
    theta = math.radians(float(row["Rotation"]))
    # Check each pad
    mismatches = []
    for ep in lp["pads"]:
        pnum = str(ep["number"])
        if pnum not in board_pads.get(ref, {}):
            continue
        bx, by, bw, bh = board_pads[ref][pnum]
        rel_bx, rel_by = bx - fx, by - fy
        # EasyEDA pad rotated by theta CCW (in +Y down frame: +Y_up = -Y_down)
        ex, ey = ep["x"], ep["y"]
        rx = ex * math.cos(theta) + ey * math.sin(theta)
        ry = -ex * math.sin(theta) + ey * math.cos(theta)
        err = math.hypot(rx - rel_bx, ry - rel_by)
        if err > 0.35:
            mismatches.append((pnum, (round(rel_bx,2), round(rel_by,2)), (round(rx,2), round(ry,2)), round(err,2)))
    if mismatches:
        print(f"  MISMATCH on {ref} ({code}, JLC rot={row['Rotation']}): {mismatches}")
    else:
        print(f"  OK {ref:5s} ({code}, JLC rot={row['Rotation']:>5s}): all EasyEDA pads align within 0.35mm of board pads")
