import sys
sys.path.insert(0, "scripts")
import kienv
# run under the AppImage's python via kienv if available
try:
    import pcbnew
except ImportError:
    print("needs pcbnew; run with the AppImage python")
    raise
b = pcbnew.LoadBoard("hardware/opamp.kicad_pcb")
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith(("D", "Q", "LED", "SW", "RV")):
        pads = {p.GetNumber(): p for p in fp.Pads()}
        c = fp.GetPosition()
        info = []
        for n, p in sorted(pads.items()):
            d = p.GetPosition() - c
            info.append(f"pad{n}@({pcbnew.ToMM(d.x):+.2f},{pcbnew.ToMM(d.y):+.2f})[{p.GetNetname()}]")
        print(f"{ref:5s} rot={fp.GetOrientationDegrees():5.1f}  " + "  ".join(info))
