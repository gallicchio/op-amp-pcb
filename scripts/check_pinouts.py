#!/usr/bin/env python3
"""Does each chip's symbol name its pins as the maker does?  For every part with an LCSC code and three or more pins,
compare the pin names on our schematic symbol (the one embedded in hardware/<stem>.kicad_sch) with the names on
EasyEDA's symbol for the same code (scripts/easyeda.py: the drawing JLCPCB's catalogue shows, usually copied from the
datasheet), pin number by pin number.  Ported from AMOD-and-RFMOD (its Prompt 19).

    python3 scripts/check_pinouts.py              (the opamp board)

Names are compared after normalising (case, punctuation, the usual synonyms: VCC/VDD/V+, GND/VSS/V-, IN+/+IN/INP ...);
a part whose names disagree is printed side by side for a person to read against the datasheet.  AMOD-and-RFMOD wrote it
after AMOD-C's DMMT3904W turned out to carry the BCM857BS's pinout (1 E1 ... 6 C1) where Diodes' drawing has 1 B2, 2
B1, 3 C1, 4 E1, 5 E2, 6 C2: a pin-number fit (check_rotations.py) cannot see that.
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parts, easyeda
from sexp_parse import parse_file

PASSIVE = ("Device:R", "Device:C", "Device:L", "Device:LED", "Device:D", "Device:Ferrite", "Connector:Conn_Coaxial", "Connector:TestPoint")
SYN = [("VCC", "VDD", "V+", "VS+", "+VS", "VIN+", "AVDD", "VPOS", "VP"),
       ("GND", "VSS", "V-", "VS-", "-VS", "VEE", "AGND", "PGND", "EP", "PAD", "VNEG", "GNDPAD", "EPAD", "THERMALPAD"),
       ("+IN", "IN+", "INP", "+INPUT", "NONINV", "IN_P", "VIN+", "INPUT+"), ("-IN", "IN-", "INN", "-INPUT", "INV", "IN_N", "VIN-", "INPUT-"),
       ("OUT", "OUTPUT", "VOUT", "Y"), ("NC", "DNC", "N/C"), ("CLK", "C", "CK", "CP", "SCLK"), ("IN", "INPUT", "I"),
       ("COM", "COMMON", "K1A2", "A2K1", "K1/A2")]


def norm(name):
    n = re.sub(r"[~{}\s_/^#]", "", (name or "").upper()).replace("OVERLINE", "")
    for group in SYN:
        if n in [re.sub(r"[\s_/]", "", g) for g in group]:
            return group[0]
    return n


def our_symbols(stem):
    """{lib_id: {number: name}} from the schematic's embedded library."""
    root = parse_file(os.path.join(ROOT, "hardware", stem + ".kicad_sch"))
    out = {}
    lib = root.first("lib_symbols")
    for sym in lib.kids("symbol"):
        pins = {}
        stack = [sym]
        while stack:
            n = stack.pop()
            for k in n.kids():
                if k.tag == "pin":
                    name = k.first("name").atom(0) if k.first("name") else ""
                    num = k.first("number").atom(0) if k.first("number") else ""
                    pins[num] = name
                else:
                    stack.append(k)
        out[sym.atom(0)] = pins
    return out


def their_pins(code):
    """{number: name} from EasyEDA's symbol: its pin-number and pin-name texts, paired by the pin each belongs to."""
    res, _ = easyeda.svgs(code)
    sym = next((r for r in (res or []) if isinstance(r, dict) and r.get("docType") == 2), None)
    if not sym:
        return {}
    svg = sym["svg"]
    # each pin is a <g c_partid="part_pin"> group: its number in c_spicepin (and as a text), its name as the other text
    out = {}
    for g in re.finditer(r'<g c_partid="part_pin"([^>]*)>(.*?)</g>', svg, re.S):
        num = re.search(r'c_spicepin="([^"]*)"', g.group(1))
        texts = [t.strip() for t in re.findall(r'<text[^>]*>([^<]*)</text>', g.group(2))]
        if not num:
            continue
        names = [t for t in texts if t and t != num.group(1)]
        out[num.group(1)] = names[0] if names else ""
    return out


def main(stems):
    seen, bad = set(), 0
    for stem in stems:
        path = os.path.join(ROOT, "hardware", stem + ".kicad_sch")
        if not os.path.exists(path):
            continue
        ours = our_symbols(stem)
        for key, p in parts.PARTS.items():
            lcsc, sym = p.get("lcsc"), p.get("symbol", "")
            if not lcsc or sym.startswith(PASSIVE) or (lcsc, sym) in seen:
                continue
            mine = next((v for k, v in ours.items() if k == sym or k.endswith(":" + sym.split(":")[-1])), None)
            if mine is None or len(mine) < 3:
                continue
            seen.add((lcsc, sym))
            try:
                theirs = their_pins(lcsc)
            except Exception as e:  # noqa
                print("  ?       %-10s %-14s %s" % (lcsc, key, e))
                continue
            if not theirs:
                print("  ?       %-10s %-14s EasyEDA's symbol has no readable pin names" % (lcsc, key))
                continue
            if not any(theirs.values()):
                continue                                      # a connector: EasyEDA's pins carry numbers only
            if not any(mine.values()):                        # op-amp: KiCad's SW_DIP_x02 names no pins
                print("  -       %-10s %-14s %s  ours unnamed, theirs %s: read the pairs" % (
                    lcsc, key, stem, " ".join("%s=%s" % (n, theirs[n]) for n in sorted(theirs))))
                continue
            diff = [n for n in sorted(mine, key=lambda s: (len(s), s)) if n in theirs and norm(mine[n]) != norm(theirs[n])]
            share = len([n for n in mine if n in theirs])
            flag = "ok" if not diff else "DIFFERS"
            if diff:
                bad += 1
            print("  %-7s %-10s %-14s %s  (%d of %d pins compared)" % (flag, lcsc, key, stem, share, len(mine)))
            if diff:
                for n in sorted(mine, key=lambda s: (len(s), s)):
                    print("            pin %-3s ours %-12s theirs %-12s %s" % (n, mine[n], theirs.get(n, "-"), "<<" if n in diff else ""))
    print("\n%d part(s) whose pin names differ from EasyEDA's: read each against its datasheet" % bad)
    return 1 if bad else 0                                    # op-amp: a difference fails the build


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(main(args or ["opamp"]))
