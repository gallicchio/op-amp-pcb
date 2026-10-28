import sys, collections
sys.path.insert(0, "scripts")
import pcbnew
b = pcbnew.LoadBoard("hardware/opamp.kicad_pcb")
smt = tht = 0
per = collections.Counter()
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("MH"):
        continue
    for pad in fp.Pads():
        if pad.GetNetname() in ("", None):
            continue
        if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            tht += 1
            per[ref] += 1
        else:
            smt += 1
print("SMT joints:", smt)
print("THT joints:", tht, dict(per))
