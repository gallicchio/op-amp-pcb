#!/usr/bin/env python3
"""Check copper clearances to M3 holes, BNC flanges, fiducials, B.Cu ground plane integrity, and DSIC02 switch."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "project", "scripts"))
import pcbnew
import layout as L, parts

pcb_path = os.path.join(HERE, "project", "hardware", "opamp.kicad_pcb")
board = pcbnew.LoadBoard(pcb_path)
tomm = pcbnew.ToMM

print("=================================================================")
print("1. CLEARANCES TO M3 MOUNTING HOLES (MH1..MH4)")
print("=================================================================")
# M3 hole is 3.2mm drill; M3 pan-head screw / hex standoff is ~5.5-6.0mm OD (radius 3.0mm)
mhs = [(ref, L.PLACE[ref][0], L.PLACE[ref][1]) for ref in ("MH1", "MH2", "MH3", "MH4")]
for ref, mx, my in mhs:
    min_trk = 999.0
    nearest_trk = None
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            d = math.hypot(tomm(t.GetPosition().x) - mx, tomm(t.GetPosition().y) - my) - tomm(t.GetWidth(pcbnew.F_Cu))/2
            if d < min_trk:
                min_trk, nearest_trk = d, f"via({t.GetNetname()}) at ({tomm(t.GetPosition().x):.1f},{tomm(t.GetPosition().y):.1f})"
        else:
            a = (tomm(t.GetStart().x), tomm(t.GetStart().y))
            b = (tomm(t.GetEnd().x), tomm(t.GetEnd().y))
            abx, aby = b[0]-a[0], b[1]-a[1]
            l2 = abx*abx + aby*aby
            u = max(0.0, min(1.0, ((mx-a[0])*abx + (my-a[1])*aby)/l2)) if l2 > 0 else 0.0
            d = math.hypot(mx - (a[0]+u*abx), my - (a[1]+u*aby)) - tomm(t.GetWidth())/2
            if d < min_trk:
                min_trk, nearest_trk = d, f"track({t.GetNetname()}) ({a[0]:.1f},{a[1]:.1f})->({b[0]:.1f},{b[1]:.1f})"
    min_fp = 999.0
    nearest_fp = None
    for fp in board.GetFootprints():
        fref = fp.GetReference()
        if fref == ref:
            continue
        for p in fp.Pads():
            d = math.hypot(tomm(p.GetPosition().x) - mx, tomm(p.GetPosition().y) - my)
            if d < min_fp:
                min_fp, nearest_fp = d, f"{fref}.{p.GetNumber()} at ({tomm(p.GetPosition().x):.1f},{tomm(p.GetPosition().y):.1f})"
    min_fid = min(math.hypot(fx - mx, fy - my) for fx, fy in L.FIDUCIALS)
    print(f"  {ref} at ({mx:.1f},{my:.1f}): nearest track/via center-to-edge={min_trk:.2f}mm ({nearest_trk}); nearest pad center={min_fp:.2f}mm ({nearest_fp}); nearest fiducial center={min_fid:.2f}mm")

print("\n=================================================================")
print("2. BNC JACKS (J1, J2, J3) SETBACK & BARREL OVERHANG")
print("=================================================================")
# BNC-KYWE-295-W4-N: body 10x10mm centered on pin 1 (0,0), front face of body at +5.0mm from center, barrel extends to +24.5mm
for ref in ("J1", "J2", "J3"):
    jx, jy, jrot = L.PLACE[ref]
    # At rot 180 (J1, J2), +x of footprint points to -x (left edge x=0). Body front face is at jx - 5.0.
    # At rot 0 (J3), +x of footprint points to +x (right edge x=100). Body front face is at jx + 5.0.
    if jrot == 180:
        face_x = jx - 5.0
        barrel_tip = jx - 24.5
        edge_x = 0.0
        gap_to_edge = face_x - edge_x
    else:
        face_x = jx + 5.0
        barrel_tip = jx + 24.5
        edge_x = 100.0
        gap_to_edge = edge_x - face_x
    print(f"  {ref} at ({jx:.1f},{jy:.1f}, rot={jrot}): body front face at x={face_x:.1f}mm (board edge at {edge_x:.1f}mm -> setback={gap_to_edge:+.1f}mm), barrel tip at x={barrel_tip:.1f}mm")

print("\n=================================================================")
print("3. B.Cu GROUND PLANE INTEGRITY & HOP SLOTS")
print("=================================================================")
for z in board.Zones():
    lay = board.GetLayerName(z.GetLayer())
    poly = z.GetFilledPolysList(z.GetLayer())
    print(f"  Zone on {lay}: net={z.GetNetname()}, filled outline count={poly.OutlineCount()}, hole count={sum(poly.HoleCount(i) for i in range(poly.OutlineCount()))}")
    for i in range(poly.OutlineCount()):
        bb = poly.COutline(i).BBox()
        print(f"    Outline {i}: bbox=({tomm(bb.GetLeft()):.2f},{tomm(bb.GetTop()):.2f})..({tomm(bb.GetRight()):.2f},{tomm(bb.GetBottom()):.2f}), holes={poly.HoleCount(i)}")

# Check distance between the 8 B.Cu hop tracks to see if any two hops merge into a long slot in B.Cu
bcu = []
for t in board.GetTracks():
    if not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu:
        bcu.append((t.GetNetname(), (tomm(t.GetStart().x), tomm(t.GetStart().y)), (tomm(t.GetEnd().x), tomm(t.GetEnd().y))))
for i in range(len(bcu)):
    for j in range(i+1, len(bcu)):
        n1, a1, b1 = bcu[i]
        n2, a2, b2 = bcu[j]
        # min endpoint-to-endpoint distance
        dmin = min(math.hypot(p[0]-q[0], p[1]-q[1]) for p in (a1, b1) for q in (a2, b2))
        if dmin < 10.0:
            print(f"  Nearby B.Cu hops (<10mm): Hop {i+1} ({n1} {a1}->{b1}) <-> Hop {j+1} ({n2} {a2}->{b2}): min_endpoint_dist = {dmin:.2f}mm")
