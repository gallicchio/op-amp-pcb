#!/usr/bin/env python3
"""Build the PCB from scripts/layout.py: outline, placement, planned copper,
ground plane and the silkscreen that is the schematic.

Runs under KiCad's bundled Python (it needs pcbnew):
    <AppRun> python3.11 scripts/gen_pcb.py out/opamp.net hardware/opamp.kicad_pcb

There is no autorouter.  Every wire in layout.WIRES is a schematic wire: it is
laid as copper exactly where it is drawn, and drawn again on the silkscreen
(clipped round pads and part bodies), so the printed picture and the copper
cannot disagree.  Two segments dive under others on the back layer (HOPS);
the silkscreen draws those as hops.  Ground is the back plane.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from sexp_parse import parse_file
import layout as L
import parts

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.abspath(os.path.join(HERE, "..", "hardware"))
LOCAL_FP = os.path.join(HW, "lib", "opamp.pretty")
SHARE_FP = None

SILK_W = 0.3            # the schematic wires on the silkscreen
SILK_CLEAR = 0.3        # silkscreen to pad
VIA_DIA, VIA_DRILL = 0.8, 0.3


def mm(v):
    return pcbnew.FromMM(float(v))


def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def tomm(v):
    return pcbnew.ToMM(v)


def find_share():
    here = os.path.dirname(os.path.abspath(pcbnew.__file__))
    for up in range(2, 8):
        base = os.path.abspath(os.path.join(here, *([".."] * up)))
        for sub in ("share/kicad/footprints", "usr/share/kicad/footprints"):
            cand = os.path.join(base, sub)
            if os.path.isdir(cand):
                return cand
    env = os.environ.get("KICAD_SHARE_DIR")
    if env and os.path.isdir(os.path.join(env, "footprints")):
        return os.path.join(env, "footprints")
    raise SystemExit("cannot find KiCad's footprint libraries")


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = LOCAL_FP if lib == "opamp" else os.path.join(SHARE_FP, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit(f"footprint {fpid} not found in {path}")
    return fp


def read_netlist(path):
    root = parse_file(path)
    comps = {}
    for c in root.first("components").kids("comp"):
        fields = {}
        fl = c.first("fields")
        if fl is not None:
            for f in fl.kids("field"):
                nm = f.first("name").atom(0)
                val = f.atom(0)
                if nm not in ("Footprint", "Datasheet", "Description") and val:
                    fields[nm] = val
        ts = c.first("tstamps")
        val = c.first("value").atom(0)
        comps[c.first("ref").atom(0)] = {
            "value": "" if val == "~" else val,
            "footprint": c.first("footprint").atom(0),
            "fields": fields, "tstamp": ts.atom(0) if ts is not None else ""}
    nets = {}
    for n in root.first("nets").kids("net"):
        name = n.first("name").atom(0)
        nets[name] = [(x.first("ref").atom(0), x.first("pin").atom(0)) for x in n.kids("node")]
    return comps, nets


# ------------------------------------------------------------- the board ---
BOARD_RULES = dict(m_MinClearance=0.20, m_HoleClearance=0.30, m_HoleToHoleMin=0.50,
                   m_CopperEdgeClearance=0.30, m_SilkClearance=0.15)


def apply_rules(board):
    ds = board.GetDesignSettings()
    for name, value in BOARD_RULES.items():
        setattr(ds, name, mm(value))


def board_outline(board):
    w, h, r = L.BOARD_W, L.BOARD_H, 3.0
    for (a, b) in (((r, 0), (w - r, 0)), ((w, r), (w, h - r)), ((w - r, h), (r, h)), ((0, h - r), (0, r))):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a)); s.SetEnd(pt(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)
    for (cx, cy, a0) in ((r, r, 180), (w - r, r, 270), (w - r, h - r, 0), (r, h - r, 90)):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetCenter(pt(cx, cy))
        s.SetStart(pt(cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), True)
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)


class Board:
    def __init__(self, netlist_path, out_path):
        global SHARE_FP
        SHARE_FP = find_share()
        self.comps, self.nets = read_netlist(netlist_path)
        self.board = pcbnew.CreateEmptyBoard()
        self.board.SetCopperLayerCount(2)
        apply_rules(self.board)
        self.out_path = out_path
        self.netmap = {}
        for name in sorted(self.nets):
            ni = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(ni)
            self.netmap[name] = ni
        self.pad_net = {}
        for name, nodes in self.nets.items():
            for node in nodes:
                self.pad_net[node] = name
        self.fps = {}
        self.pads = {}            # (ref, pad) -> dict(x, y, w, h, through, net)
        self.problems = []

    # ------------------------------------------------------------ parts --
    def place(self):
        for ref, info in sorted(self.comps.items()):
            if ref not in L.PLACE:
                raise SystemExit(f"{ref} has no entry in layout.PLACE")
            x, y, rot = L.PLACE[ref]
            fp = load_fp(info["footprint"])
            fp.SetFPIDAsString(info["footprint"])
            if info["tstamp"]:
                fp.SetPath(pcbnew.KIID_PATH("/" + info["tstamp"]))
            fp.SetSheetname("/")
            fp.SetSheetfile(os.path.basename(self.out_path).replace(".kicad_pcb", ".kicad_sch"))
            fp.SetReference(ref)
            fp.SetValue(info["value"])
            for fname, fval in info["fields"].items():
                fp.SetField(fname, fval)
            for f in fp.GetFields():
                if f.GetName() in ("Reference", "Value"):
                    continue
                f.SetVisible(False)
                f.SetLayer(pcbnew.F_Fab)
            if fp.HasField("Description"):
                fp.SetField("Description", "")
            self.board.Add(fp)
            fp.SetPosition(pt(x, y))
            if rot:
                fp.SetOrientationDegrees(rot)
            for pad in fp.Pads():
                key = (ref, pad.GetNumber())
                if key in self.pad_net:
                    pad.SetNet(self.netmap[self.pad_net[key]])
            if ref[:2] == "MH":
                fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM
                                 | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
                fp.Value().SetVisible(False)
                fp.Reference().SetVisible(False)
            self.fps[ref] = fp
        for ref, fp in self.fps.items():
            for pad in fp.Pads():
                b = pad.GetBoundingBox()
                self.pads[(ref, pad.GetNumber())] = dict(
                    x=tomm(pad.GetPosition().x), y=tomm(pad.GetPosition().y),
                    x0=tomm(b.GetLeft()), y0=tomm(b.GetTop()), x1=tomm(b.GetRight()), y1=tomm(b.GetBottom()),
                    through=pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH),
                    net=pad.GetNetname())
        self.board.GetDesignSettings().SetAuxOrigin(pt(0, L.BOARD_H))
        board_outline(self.board)

    # ----------------------------------------------------------- copper --
    def resolve(self, p, net):
        if isinstance(p[0], str):
            pad = self.pads.get((p[0], p[1]))
            if pad is None:
                raise SystemExit(f"wire on {net}: no pad {p[0]}.{p[1]}")
            if pad["net"] != net:
                self.problems.append(f"wire on {net} ends on {p[0]}.{p[1]}, which is on {pad['net']!r}")
            return (pad["x"], pad["y"])
        return (float(p[0]), float(p[1]))

    def track(self, a, b, width, net, layer=pcbnew.F_Cu):
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            return
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pt(*a)); t.SetEnd(pt(*b))
        t.SetWidth(mm(width)); t.SetLayer(layer)
        t.SetNet(self.netmap[net])
        self.board.Add(t)
        self.segments.append((net, a, b, layer))

    def via(self, x, y, net):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pt(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetDrill(mm(VIA_DRILL)); v.SetWidth(mm(VIA_DIA))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.netmap[net])
        v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED)
        v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
        self.board.Add(v)
        self.vias.append((net, x, y))

    def wires(self):
        self.segments, self.vias, self.hops = [], [], []
        hops = {(n, a, b): True for (n, a, b) in L.HOPS}
        hops.update({(n, b, a): True for (n, a, b) in L.HOPS})
        for (net, points, width) in L.WIRES:
            if net not in self.netmap:
                raise SystemExit(f"wire names a net that is not in the netlist: {net!r}")
            pts = [self.resolve(p, net) for p in points]
            for a, b in zip(pts, pts[1:]):
                key = (net, (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))
                if key in hops:
                    self.via(*a, net); self.via(*b, net)
                    self.track(a, b, width, net, pcbnew.B_Cu)
                    self.hops.append((net, a, b))
                else:
                    self.track(a, b, width, net)
        self.stub_dir = {}
        for (padref, path) in L.GND_STUBS:
            pad = self.pads[padref]
            if pad["net"] != "GND":
                self.problems.append(f"ground stub from {padref}, which is on {pad['net']!r}")
            pts = [(pad["x"], pad["y"])] + (list(path) if isinstance(path, list) else [path])
            for a, b in zip(pts, pts[1:]):
                self.track(a, b, L.W_SIG, "GND")
            vx, vy = pts[-1]
            self.via(vx, vy, "GND")
            dx, dy = vx - pts[-2][0], vy - pts[-2][1]
            n = math.hypot(dx, dy) or 1.0
            self.stub_dir[(round(vx, 3), round(vy, 3))] = (dx / n, dy / n)


    def plane(self):
        z = pcbnew.ZONE(self.board)
        z.SetLayer(pcbnew.B_Cu)
        z.SetNet(self.netmap["GND"])
        z.SetAssignedPriority(0)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.5))
        z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.2))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline(); o.NewOutline()
        m = 0.3
        for (x, y) in ((m, m), (L.BOARD_W - m, m), (L.BOARD_W - m, L.BOARD_H - m), (m, L.BOARD_H - m)):
            o.Append(mm(x), mm(y))
        self.board.Add(z)
        self.board.BuildConnectivity()
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())

    # ------------------------------------------------------- silkscreen --
    def _line(self, a, b, layer=pcbnew.F_SilkS, width=SILK_W):
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            return
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a)); s.SetEnd(pt(*b))
        s.SetLayer(layer); s.SetWidth(mm(width))
        self.board.Add(s)

    def _dashed(self, a, b, dash=1.2, gap=0.7, width=0.2):
        """A dashed line, drawn as its dashes (pcbnew's line styles are not reachable here)."""
        L_ = math.hypot(b[0] - a[0], b[1] - a[1])
        if L_ < 1e-6:
            return
        ux, uy = (b[0] - a[0]) / L_, (b[1] - a[1]) / L_
        t = 0.0
        while t < L_:
            e = min(t + dash, L_)
            self._line((a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e), width=width)
            t = e + gap

    def _circle(self, cx, cy, r, filled=False, width=SILK_W, layer=pcbnew.F_SilkS):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetCenter(pt(cx, cy)); s.SetEnd(pt(cx + r, cy))
        s.SetFilled(filled); s.SetWidth(mm(width)); s.SetLayer(layer)
        self.board.Add(s)

    def _arc(self, cx, cy, r, a0, sweep, width=SILK_W):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetCenter(pt(cx, cy))
        s.SetStart(pt(cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(sweep, pcbnew.DEGREES_T), True)
        s.SetLayer(pcbnew.F_SilkS); s.SetWidth(mm(width))
        self.board.Add(s)

    def _poly(self, points, filled=True, layer=pcbnew.F_SilkS):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_POLY)
        s.SetPolyPoints([pt(*p) for p in points])
        s.SetFilled(filled); s.SetWidth(mm(0.1)); s.SetLayer(layer)
        self.board.Add(s)

    def _text(self, x, y, txt, size, thickness=0.15, justify="center", angle=0, layer=pcbnew.F_SilkS):
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(txt)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thickness))
        t.SetLayer(layer)
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        t.SetTextAngleDegrees(angle)
        t.SetHorizJustify({"center": pcbnew.GR_TEXT_H_ALIGN_CENTER, "left": pcbnew.GR_TEXT_H_ALIGN_LEFT,
                           "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT}[justify])
        t.SetPosition(pt(x, y))
        self.board.Add(t)
        return t

    def keepouts(self):
        """Boxes the silkscreen wires must not cross: pads with clearance, and
        the bodies (courtyards) of every part, so a wire stops at the part the
        way a schematic wire stops at a symbol."""
        boxes = []
        for key, p in self.pads.items():
            boxes.append((p["x0"] - SILK_CLEAR, p["y0"] - SILK_CLEAR, p["x1"] + SILK_CLEAR, p["y1"] + SILK_CLEAR))
        for ref, fp in self.fps.items():
            if ref[:2] in ("TP", "MH"):
                continue
            poly = fp.GetCourtyard(pcbnew.F_CrtYd)
            if poly.OutlineCount():
                bb = poly.BBox()
                box = [tomm(bb.GetLeft()) - 0.4, tomm(bb.GetTop()) - 0.4, tomm(bb.GetRight()) + 0.4, tomm(bb.GetBottom()) + 0.4]
                boxes.append(tuple(box))
        self.boxes = boxes
        return boxes

    def clip(self, a, b):
        """Pieces of segment a-b that lie outside every keep-out box."""
        (x1, y1), (x2, y2) = a, b
        dx, dy = x2 - x1, y2 - y1
        cuts = []
        for (bx0, by0, bx1, by1) in self.boxes:
            # parametric overlap of the segment with the box (axis-aligned Liang-Barsky)
            t0, t1 = 0.0, 1.0
            ok = True
            for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
                if abs(p) < 1e-9:
                    if q < 0:
                        ok = False
                        break
                    continue
                r = q / p
                if p < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
            if ok and t0 < t1:
                cuts.append((max(0.0, t0), min(1.0, t1)))
        cuts.sort()
        pieces, t = [], 0.0
        for (c0, c1) in cuts:
            if c0 > t:
                pieces.append((t, c0))
            t = max(t, c1)
        if t < 1.0:
            pieces.append((t, 1.0))
        out = []
        for (p0, p1) in pieces:
            if (p1 - p0) * math.hypot(dx, dy) < 0.25:
                continue
            out.append(((x1 + dx * p0, y1 + dy * p0), (x1 + dx * p1, y1 + dy * p1)))
        return out

    def silk_wires(self):
        self.keepouts()
        hopset = {(round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)) for (_, a, b) in self.hops}
        hopset |= {(round(b[0], 3), round(b[1], 3), round(a[0], 3), round(a[1], 3)) for (_, a, b) in self.hops}
        ends = {}
        for (net, a, b, layer) in self.segments:
            if net == "GND":
                continue
            key = (round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3))
            if key in hopset:
                # a hop: a semicircle over the wire it crosses, at the middle
                cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                r = 0.5
                if abs(a[1] - b[1]) < 1e-6:          # horizontal hop
                    self._line(a, (cx - r, cy)); self._line((cx + r, cy), b)
                    self._arc(cx, cy, r, 180, 180)
                else:                               # vertical hop
                    self._line(a, (cx, cy - r)); self._line((cx, cy + r), b)
                    self._arc(cx, cy, r, 270, 180)
                continue
            for (p, q) in self.clip(a, b):
                self._line(p, q)
            for e in (a, b):
                k = (round(e[0], 2), round(e[1], 2))
                ends.setdefault(k, set()).add(net)
        # junction dots: a point where three or more segment ends of one net meet,
        # or where a segment ends on the interior of another of the same net
        count = {}
        for (net, a, b, layer) in self.segments:
            for e in (a, b):
                k = (net, round(e[0], 2), round(e[1], 2))
                count[k] = count.get(k, 0) + 1
        for (net, a, b, layer) in self.segments:
            if net == "GND":
                continue
            for e in (a, b):
                for (n2, c, d, l2) in self.segments:
                    if n2 != net or (c, d) == (a, b):
                        continue
                    if self._interior(e, c, d):
                        k = (net, round(e[0], 2), round(e[1], 2))
                        count[k] = max(count[k], 3)
        for (net, x, y), n in count.items():
            if net != "GND" and n >= 3 and not self._on_pad(x, y):
                self._circle(x, y, 0.5, filled=True, width=0)

    @staticmethod
    def _interior(p, a, b, tol=0.01):
        (px, py), (ax, ay), (bx, by) = p, a, b
        if abs(ay - by) < tol and abs(py - ay) < tol:
            return min(ax, bx) + tol < px < max(ax, bx) - tol
        if abs(ax - bx) < tol and abs(px - ax) < tol:
            return min(ay, by) + tol < py < max(ay, by) - tol
        return False

    def _on_pad(self, x, y):
        for p in self.pads.values():
            if p["x0"] - 0.05 <= x <= p["x1"] + 0.05 and p["y0"] - 0.05 <= y <= p["y1"] + 0.05:
                return True
        return False

    def silk_grounds(self):
        """A ground symbol at every ground via (continuing the stub's direction)
        and under every ground connector post."""
        for (net, x, y) in self.vias:
            if net != "GND":
                continue
            ux, uy = self.stub_dir.get((round(x, 3), round(y, 3)), (0, 1))
            self.ground_symbol(x, y, ux, uy)
        for (x, y) in L.GND_MARKS:
            self.ground_symbol(x, y, 0, 1, start=1.3 + 0.4)

    def ground_symbol(self, x, y, ux, uy, start=0.55):
        """Three shortening bars across the direction (ux, uy), beyond `start`
        from the point: the schematic's ground, drawn the way the wire runs."""
        px, py = -uy, ux                 # across
        s0 = start + 0.5
        self._line((x + ux * start, y + uy * start), (x + ux * s0, y + uy * s0))
        for i, w in enumerate((1.4, 0.9, 0.4)):
            s = s0 + i * 0.45
            cx, cy = x + ux * s, y + uy * s
            self._line((cx - px * w / 2, cy - py * w / 2), (cx + px * w / 2, cy + py * w / 2), width=0.25)

    def silk_transistors(self):
        """The textbook symbol drawn round each SOT-23, inside a circle: the base
        bar on the side the base wire arrives from, a slanted collector lead up
        to the collector wire, a slanted emitter lead with the arrow on it (out
        of the bar for an NPN, into it for a PNP), and B, C, E beside the three
        wires where they leave the circle.  The package sits between the leads;
        the copper wires enter the circle exactly where the symbol's leads end."""
        R = L.Q_RADIUS
        for ref, (kind, side) in L.TRANSISTORS.items():
            fp = self.fps[ref]
            cx, cy = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
            # the package's own outline would clutter the symbol: drop it
            for item in list(fp.GraphicalItems()):
                if item.GetLayer() == pcbnew.F_SilkS:
                    fp.Remove(item)
            self._circle(cx, cy, R)
            b = self.pads[(ref, "1")]; e = self.pads[(ref, "2")]; c = self.pads[(ref, "3")]
            sx = -1 if side == "left" else 1          # the bar's side
            cu = -1 if kind == "NPN" else 1            # collector direction: NPN up, PNP down
            bx = cx + sx * 2.05
            # the bar, and the two legs the book draws: collector from one end to
            # the collector wire (x = cx), emitter from the other end to the emitter
            # wire, which the layout brings out at x = cx + sx * 0.4.  The legs leave
            # the bar near its ends so they clear the base pad under them.
            self._line((bx, cy - 1.9), (bx, cy + 1.9), width=0.4)
            self._line((bx, cy + cu * 1.6), (cx - sx * 0.2, cy + cu * 2.9), width=0.3)
            p0 = (bx, cy - cu * 1.9)
            p1 = (cx + sx * 0.4, cy - cu * 2.9)
            self._line(p0, p1, width=0.3)
            # the arrow is always on the emitter: at the leg's far end pointing out
            # for an NPN, at the bar pointing in for a PNP
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            n = math.hypot(dx, dy); ux, uy = dx / n, dy / n
            px, py = -uy, ux
            if kind == "NPN":
                tip = p1
                tail = (p1[0] - ux * 1.3, p1[1] - uy * 1.3)
            else:
                tip = (p0[0] + ux * 0.1, p0[1] + uy * 0.1)
                tail = (tip[0] + ux * 1.3, tip[1] + uy * 1.3)
            self._poly([tip, (tail[0] + px * 0.55, tail[1] + py * 0.55), (tail[0] - px * 0.55, tail[1] - py * 0.55)])
            # B, C, E where the wires leave the circle (or where the layout says)
            letters = {"B": (cx + sx * (R + 0.9), b["y"] - 0.9),
                       "C": (cx + sx * 1.1, cy + cu * (R + 0.7)),
                       "E": (cx + sx * 1.5, cy - cu * (R + 0.7))}
            letters.update(getattr(L, "Q_LETTER", {}).get(ref, {}))
            for name, (lx, ly) in letters.items():
                self._text(lx, ly, name, 0.8, 0.15, justify="center")
            # caption: reference and type, where the layout says
            fp.Value().SetVisible(False)
            fp.Reference().SetVisible(False)
            cap = L.Q_CAPTION[ref]
            tx, ty, just = cap[:3]
            size = cap[3] if len(cap) > 3 else 0.9
            ang = cap[4] if len(cap) > 4 else 0
            self._text(tx, ty, ref, size, 0.15, justify=just, angle=ang)
            if ref in L.HIDE_VALUE:
                pass
            elif ang:
                self._text(tx + 1.4 * size, ty, fp.Value().GetText(), size, 0.15, justify=just, angle=ang)
            else:
                self._text(tx, ty + 1.5 * size, fp.Value().GetText(), size, 0.15, justify=just)

    def silk_fields(self):
        """Reference and value beside each part, where layout.FIELD_AT says."""
        for ref, fp in self.fps.items():
            if ref in L.TRANSISTORS or ref[:2] == "MH":
                continue
            cx, cy = tomm(fp.GetPosition().x), tomm(fp.GetPosition().y)
            at = L.FIELD_AT.get(ref)
            r = fp.Reference()
            r.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); r.SetTextThickness(mm(0.15))
            r.SetTextAngleDegrees(0); r.SetLayer(pcbnew.F_SilkS)
            v = fp.Value()
            v.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); v.SetTextThickness(mm(0.15))
            v.SetTextAngleDegrees(0); v.SetLayer(pcbnew.F_SilkS)
            if ref.startswith("TP"):
                # probe pins: the name only, beside the pin
                r.SetVisible(False)
                v.SetVisible(True)
                v.SetTextSize(pcbnew.VECTOR2I(mm(0.9), mm(0.9))); v.SetTextThickness(mm(0.15))
                where = L.TP_LABEL.get(ref, (1.6, 0.0, "left"))
                if where is None:                      # a loop on a labelled rail needs no name
                    v.SetVisible(False)
                    continue
                dx, dy, j = where
                v.SetPosition(pt(cx + dx, cy + dy))
                v.SetHorizJustify({"left": pcbnew.GR_TEXT_H_ALIGN_LEFT, "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT,
                                   "center": pcbnew.GR_TEXT_H_ALIGN_CENTER}[j])
                continue
            if ref in L.HIDE_REF:
                r.SetVisible(False)
            elif at and at[0]:
                r.SetPosition(pt(cx + at[0][0], cy + at[0][1]))
                r.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT if at[0][0] > 0.5 else
                                  pcbnew.GR_TEXT_H_ALIGN_RIGHT if at[0][0] < -0.5 else pcbnew.GR_TEXT_H_ALIGN_CENTER)
            if ref in L.HIDE_VALUE:
                v.SetVisible(False)
            elif at and at[1]:
                v.SetPosition(pt(cx + at[1][0], cy + at[1][1]))
                v.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT if at[1][0] > 0.5 else
                                  pcbnew.GR_TEXT_H_ALIGN_RIGHT if at[1][0] < -0.5 else pcbnew.GR_TEXT_H_ALIGN_CENTER)

    def silk_boxes(self):
        """A dashed box round each stage, named as the book names it."""
        for (x0, y0, x1, y1, titles) in L.BOXES:
            for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                for (p, q) in self.clip(a, b):
                    self._dashed(p, q)
            for t in titles:
                title, tx, ty = t[:3]
                self._text(tx, ty, title, t[3] if len(t) > 3 else 0.95, 0.18, justify="left")

    def silk_texts(self):
        for (x, y, txt, size, thick, just, ang) in L.TEXTS:
            if size <= 0:
                continue
            self._text(x, y, txt, size, thick, justify=just, angle=ang)
        for ((x, y), size, lines) in L.LEGENDS:
            for i, line in enumerate(lines):
                self._text(x, y + i * size * 1.6, line, size, 0.15, justify="left")

    def silk_back(self):
        """The back: the title, how to use the board and a QR code to the
        project, mirrored so they read from the back; nothing is printed over
        the through-hole pads."""
        self._text(50, 14.0, parts.BOARD_NAME.upper(), 3.0, 0.5, layer=pcbnew.B_SilkS)
        self._text(50, 18.5, "Jason Gallicchio and Claude, rev " + parts.REV + ", " + parts.BOARD_DATE,
                   1.1, 0.15, layer=pcbnew.B_SilkS)
        for i, line in enumerate(L.BACK_TEXT):
            self._text(85.0, L.BACK_Y + i * L.BACK_PITCH, line, 1.1, 0.15, justify="left", layer=pcbnew.B_SilkS)
        qx, qy = L.QR_AT
        n, rects = self.add_qr("https://" + parts.PROJECT_URL, qx, qy, L.QR_MODULE)
        half = n * L.QR_MODULE / 2
        self._text(qx, qy + half + 2.4, parts.PROJECT_URL, 1.1, 0.15, layer=pcbnew.B_SilkS)
        self._text(qx, qy + half + 4.6, "circuit, scripts, schematic, this board", 1.0, 0.15, layer=pcbnew.B_SilkS)
        self.qr = (n, rects)

    def add_qr(self, url, cx, cy, module):
        """One QR code on the back as merged runs of filled rectangles, mirrored
        in board coordinates so it reads right from the back (the Lorenz
        board's add_qr).  Then every module is sampled back out of what was
        drawn and compared with the matrix."""
        import qrcode_gen
        m = qrcode_gen.encode(url, "M")
        n = len(m)
        x0, y0 = cx - n * module / 2.0, cy - n * module / 2.0
        rects = []
        for r in range(n):
            c = 0
            while c < n:
                if not m[r][c]:
                    c += 1
                    continue
                a = c
                while c < n and m[r][c]:
                    c += 1
                sh = pcbnew.PCB_SHAPE(self.board)
                sh.SetShape(pcbnew.SHAPE_T_RECT)
                sh.SetStart(pt(x0 + (n - c) * module, y0 + r * module))
                sh.SetEnd(pt(x0 + (n - a) * module, y0 + (r + 1) * module))
                sh.SetFilled(True); sh.SetWidth(0); sh.SetLayer(pcbnew.B_SilkS)
                self.board.Add(sh)
                rects.append((x0 + (n - c) * module, y0 + r * module, x0 + (n - a) * module, y0 + (r + 1) * module))
        ok = 0
        for r in range(n):
            for c in range(n):
                x = x0 + (n - 1 - c) * module + module / 2.0
                y = y0 + r * module + module / 2.0
                hit = any(rx0 <= x <= rx1 and ry0 <= y <= ry1 for (rx0, ry0, rx1, ry1) in rects)
                if hit == bool(m[r][c]):
                    ok += 1
        if ok != n * n:
            self.problems.append(f"QR: {n * n - ok} module(s) drawn wrong")
        # nothing drilled may sit under it
        for key, p in self.pads.items():
            if p["through"] and x0 - 1 < p["x"] < x0 + n * module + 1 and y0 - 1 < p["y"] < y0 + n * module + 1:
                self.problems.append(f"QR: through-hole pad {key} is under the code")
        for (net, vx, vy) in self.vias:
            if x0 - 1 < vx < x0 + n * module + 1 and y0 - 1 < vy < y0 + n * module + 1:
                self.problems.append(f"QR: via at ({vx}, {vy}) is under the code")
        return n, len(rects)

    # ------------------------------------------------------- the whole ---
    def build(self):
        self.place()
        self.wires()
        self.plane()
        self.silk_wires()
        self.silk_grounds()
        self.silk_transistors()
        self.silk_fields()
        self.silk_boxes()
        self.silk_texts()
        self.silk_back()
        self.fiducials()
        stabilise_uuids(self.board)
        pcbnew.SaveBoard(self.out_path, self.board)
        self.export_geometry()
        return self

    def fiducials(self):
        """Bare copper dots the assembler's camera finds the board by."""
        for (x, y) in L.FIDUCIALS:
            for layer, r in ((pcbnew.F_Cu, 0.5), (pcbnew.F_Mask, 1.0)):
                c = pcbnew.PCB_SHAPE(self.board)
                c.SetShape(pcbnew.SHAPE_T_CIRCLE)
                c.SetLayer(layer)
                c.SetStart(pt(x, y))
                c.SetEnd(pt(x + r, y))
                c.SetFilled(True)
                c.SetWidth(0)
                self.board.Add(c)

    def export_geometry(self):
        """Pad geometry for the cost estimate and the documents."""
        import json
        pads = [dict(ref=k[0], pad=k[1], net=p["net"], x=p["x"], y=p["y"],
                     w=p["x1"] - p["x0"], h=p["y1"] - p["y0"], through=p["through"]) for k, p in self.pads.items()]
        path = os.path.join(os.path.dirname(self.out_path), "..", "out", "pcb_geom.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump({"board_w": L.BOARD_W, "board_h": L.BOARD_H, "pads": pads,
                   "tracks": len(self.segments), "vias": len(self.vias), "hops": len(self.hops)},
                  open(path, "w"), indent=1)


def stabilise_uuids(board):
    """Give every board item a UUID derived from what it is, so rebuilds diff
    only where the design changed (the Lorenz board's trick)."""
    import uuid as _uuid

    def kiid(key):
        return pcbnew.KIID(str(_uuid.uuid5(_uuid.NAMESPACE_URL, "laoe-opamp-pcb://" + key)))

    def mm2(pos):
        return f"{tomm(pos.x):.4f},{tomm(pos.y):.4f}"

    n = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        fp.SetUuid(kiid(f"fp/{ref}"))
        for pad in fp.Pads():
            n += 1
            pad.SetUuid(kiid(f"fp/{ref}/pad/{pad.GetNumber()}/{mm2(pad.GetPosition())}/{n}"))
        for i, it in enumerate(fp.GraphicalItems()):
            it.SetUuid(kiid(f"fp/{ref}/gfx/{i}/{it.GetClass()}"))
        for f in fp.GetFields():
            f.SetUuid(kiid(f"fp/{ref}/field/{f.GetName()}"))
    for i, t in enumerate(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            t.SetUuid(kiid(f"via/{mm2(t.GetPosition())}/{t.GetNetname()}/{i}"))
        else:
            t.SetUuid(kiid(f"trk/{t.GetLayerName()}/{mm2(t.GetStart())}/{mm2(t.GetEnd())}/{t.GetNetname()}/{i}"))
    for i, z in enumerate(board.Zones()):
        z.SetUuid(kiid(f"zone/{z.GetLayerName()}/{z.GetNetname()}/{i}"))
    for i, d in enumerate(board.GetDrawings()):
        txt = d.GetText() if hasattr(d, "GetText") else ""
        d.SetUuid(kiid(f"gfx/{d.GetLayerName()}/{d.GetClass()}/{mm2(d.GetPosition())}/{txt[:40]}/{i}"))


if __name__ == "__main__":
    netlist = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HW, "..", "out", "opamp.net")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HW, "opamp.kicad_pcb")
    b = Board(netlist, out).build()
    ntr = sum(1 for t in b.board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))
    print(f"  wrote {os.path.relpath(out)}: {len(b.fps)} footprints, {ntr} tracks, {len(b.vias)} vias, "
          f"{len(b.hops)} hops")
    if b.problems:
        print(f"  !! {len(b.problems)} wiring problem(s):")
        for p in b.problems:
            print(f"     {p}")
        raise SystemExit(1)
