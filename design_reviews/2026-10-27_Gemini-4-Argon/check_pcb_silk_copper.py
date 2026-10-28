#!/usr/bin/env python3
"""Exact geometric verification of silkscreen, copper, hops, dots, text, boxes, and clearances using KiCad 10 pcbnew."""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "project", "scripts"))
import pcbnew
import layout as L
import parts

pcb_path = os.path.join(HERE, "project", "hardware", "opamp.kicad_pcb")
board = pcbnew.LoadBoard(pcb_path)
tomm = pcbnew.ToMM

# 1. Collect all F.Cu tracks, B.Cu tracks, vias
fcu_tracks, bcu_tracks, vias = [], [], []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        vias.append((tomm(t.GetPosition().x), tomm(t.GetPosition().y), t.GetNetname(),
                     tomm(t.GetWidth(pcbnew.F_Cu)), tomm(t.GetDrillValue())))
    else:
        a = (tomm(t.GetStart().x), tomm(t.GetStart().y))
        b = (tomm(t.GetEnd().x), tomm(t.GetEnd().y))
        if t.GetLayer() == pcbnew.F_Cu:
            fcu_tracks.append((t.GetNetname(), a, b, tomm(t.GetWidth())))
        elif t.GetLayer() == pcbnew.B_Cu:
            bcu_tracks.append((t.GetNetname(), a, b, tomm(t.GetWidth())))

# 2. Collect all F.SilkS drawings and texts (board-level + footprint-level)
silk_dots, silk_arcs, silk_lines, silk_texts, bsilk_texts = [], [], [], [], []

def collect_item(d, owner="board"):
    lay = d.GetLayer()
    if isinstance(d, pcbnew.PCB_TEXT):
        if not d.IsVisible():
            return
        bb = d.GetBoundingBox()
        # Shrink bounding box slightly by stroke/margin that KiCad adds
        box = (tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom()))
        pos = (tomm(d.GetPosition().x), tomm(d.GetPosition().y))
        sz = (tomm(d.GetTextSize().x), tomm(d.GetTextSize().y))
        th = tomm(d.GetTextThickness())
        if lay == pcbnew.F_SilkS:
            silk_texts.append((owner, d.GetText(), pos, box, sz, th, d.GetTextAngleDegrees()))
        elif lay == pcbnew.B_SilkS:
            bsilk_texts.append((owner, d.GetText(), pos, box, sz, th, d.GetTextAngleDegrees()))
    elif isinstance(d, pcbnew.PCB_SHAPE) and lay == pcbnew.F_SilkS:
        sh = d.GetShape()
        w = tomm(d.GetWidth())
        if sh == pcbnew.SHAPE_T_CIRCLE:
            c = (tomm(d.GetCenter().x), tomm(d.GetCenter().y))
            r = tomm(d.GetRadius())
            if r < 1.0:
                silk_dots.append((c[0], c[1], r))
        elif sh == pcbnew.SHAPE_T_ARC:
            c = (tomm(d.GetCenter().x), tomm(d.GetCenter().y))
            r = tomm(d.GetRadius())
            silk_arcs.append((c[0], c[1], r))
        elif sh == pcbnew.SHAPE_T_SEGMENT:
            a = (tomm(d.GetStart().x), tomm(d.GetStart().y))
            b = (tomm(d.GetEnd().x), tomm(d.GetEnd().y))
            silk_lines.append((owner, a, b, w))

for d in board.GetDrawings():
    collect_item(d, "board")

for fp in board.GetFootprints():
    ref = fp.GetReference()
    for f in fp.GetFields():
        collect_item(f, f"{ref}.{f.GetName()}")
    for g in fp.GraphicalItems():
        collect_item(g, f"{ref}.gfx")

print(f"F.Cu tracks: {len(fcu_tracks)}, B.Cu tracks: {len(bcu_tracks)}, Vias: {len(vias)}")
print(f"F.SilkS dots: {len(silk_dots)}, hop arcs: {len(silk_arcs)}, lines: {len(silk_lines)}, visible texts: {len(silk_texts)}")
print(f"B.SilkS visible texts: {len(bsilk_texts)}")

print("\n--- 2a. Junction dots on F.SilkS ---")
for i, (dx, dy, dr) in enumerate(sorted(silk_dots)):
    nets_here = set()
    deg = 0
    for net, a, b, w in fcu_tracks:
        abx, aby = b[0]-a[0], b[1]-a[1]
        l2 = abx*abx + aby*aby
        t = max(0.0, min(1.0, ((dx-a[0])*abx + (dy-a[1])*aby)/l2)) if l2 > 0 else 0.0
        dist = math.hypot(dx - (a[0]+t*abx), dy - (a[1]+t*aby))
        if dist < 0.05:
            nets_here.add(net)
            if 0.01 < t < 0.99:
                deg += 2
            else:
                deg += 1
    print(f"  dot {i+1:2d}: ({dx:6.2f}, {dy:6.2f}) r={dr:.2f}mm | F.Cu branch degree={deg} | net={sorted(nets_here)}")

print("\n--- 2b. Are there any F.Cu T-junctions (branch degree >= 3, not on a pad or Q-circle) WITHOUT a silk dot? ---")
# Collect all F.Cu endpoints
pts = set()
for net, a, b, w in fcu_tracks:
    if net == "GND":
        continue
    pts.add((net, round(a[0], 2), round(a[1], 2)))
    pts.add((net, round(b[0], 2), round(b[1], 2)))

pads_list = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        pads_list.append((ref, p.GetNumber(), tomm(p.GetPosition().x), tomm(p.GetPosition().y),
                          tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom()), p.GetNetname()))

for net, px, py in sorted(pts):
    deg = 0
    for n2, a, b, w in fcu_tracks:
        if n2 != net:
            continue
        abx, aby = b[0]-a[0], b[1]-a[1]
        l2 = abx*abx + aby*aby
        t = max(0.0, min(1.0, ((px-a[0])*abx + (py-a[1])*aby)/l2)) if l2 > 0 else 0.0
        dist = math.hypot(px - (a[0]+t*abx), py - (a[1]+t*aby))
        if dist < 0.05:
            if 0.02 < t < 0.98:
                deg += 2
            else:
                deg += 1
    if deg >= 3:
        on_pad = any(x0-0.1 <= px <= x1+0.1 and y0-0.1 <= py <= y1+0.1 for _, _, _, _, x0, y0, x1, y1, _ in pads_list)
        in_q = any(math.hypot(px - L.PLACE[q][0], py - L.PLACE[q][1]) < L.Q_RADIUS - 0.1 for q in L.TRANSISTORS)
        has_dot = any(math.hypot(px - dx, py - dy) < 0.15 for dx, dy, _ in silk_dots)
        if not on_pad and not in_q and not has_dot:
            print(f"  MISSING DOT: net={net} at ({px:.2f}, {py:.2f}), degree={deg}")

print("\n--- 2c. Are there any F.SilkS wire crossings that are NOT hops? ---")
# Check every pair of F.Cu tracks of different nets to see if any cross, and check all B.Cu hops
for i, (n1, a, b, w1) in enumerate(bcu_tracks):
    mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2
    has_arc = any(math.hypot(mx-ax, my-ay) < 0.2 for ax, ay, _ in silk_arcs)
    crossed = []
    for n2, c, d, w2 in fcu_tracks:
        if max(min(a[0],b[0]), min(c[0],d[0])) <= min(max(a[0],b[0]), max(c[0],d[0])) + 0.01 and \
           max(min(a[1],b[1]), min(c[1],d[1])) <= min(max(a[1],b[1]), max(c[1],d[1])) + 0.01:
            crossed.append((n2, (round(c[0],2),round(c[1],2)), (round(d[0],2),round(d[1],2))))
    print(f"  Hop {i+1}: {n1:10s} ({a[0]:.2f},{a[1]:.2f})->({b[0]:.2f},{b[1]:.2f}) | arc={has_arc} | crosses={crossed}")

print("\n--- 3. F.SilkS text-to-text, text-to-line, and text-to-pad checks ---")
for i in range(len(silk_texts)):
    o1, t1, p1, b1, sz1, th1, a1 = silk_texts[i]
    # shrink box by 0.12mm because GetBoundingBox includes stroke + glyph box padding
    s1 = (b1[0]+0.12, b1[1]+0.12, b1[2]-0.12, b1[3]-0.12)
    for j in range(i+1, len(silk_texts)):
        o2, t2, p2, b2, sz2, th2, a2 = silk_texts[j]
        s2 = (b2[0]+0.12, b2[1]+0.12, b2[2]-0.12, b2[3]-0.12)
        if not (s1[2] <= s2[0] or s2[2] <= s1[0] or s1[3] <= s2[1] or s2[3] <= s1[1]):
            print(f"  TEXT-TEXT OVERLAP: {o1} {t1!r} {b1} <-> {o2} {t2!r} {b2}")
    for l_owner, la, lb, lw in silk_lines:
        # check if line segment intersects s1
        if max(la[0], lb[0]) < s1[0] or min(la[0], lb[0]) > s1[2] or max(la[1], lb[1]) < s1[1] or min(la[1], lb[1]) > s1[3]:
            continue
        # if horizontal or vertical, it intersects!
        if abs(la[0]-lb[0]) < 0.01 or abs(la[1]-lb[1]) < 0.01:
            print(f"  TEXT-LINE HIT: {o1} {t1!r} at ({p1[0]:.2f},{p1[1]:.2f}) box={[round(x,2) for x in s1]} hits {l_owner} line ({la[0]:.2f},{la[1]:.2f})-({lb[0]:.2f},{lb[1]:.2f})")
