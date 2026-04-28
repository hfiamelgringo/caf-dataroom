"""Compare the before/after sensitivity scans for the edited files."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AUDIT = REPO / "audit"

before = json.loads((AUDIT / "pass1_findings.before.json").read_text(encoding="utf-8"))
after = json.loads((AUDIT / "pass1_findings.json").read_text(encoding="utf-8"))

EDITED = [
    "2026-02-03-jorge-vargas-venture-do",
    "2026-02-05-jos-kont-cuantico",
    "2026-02-13-ady-beitler-nilus",
    "2026-02-13-santiago-zavala-500",
    "2026-02-27-nelson-ir-as-n-ez-costa-rica-tech-week",
    "2026-02-27-samuel-hernandez-colmex",
    "2026-03-05-francisco-meneses-corfo",
    "2026-03-06-patrick-menendez-femsa",
    "2026-03-12-lisalud",
    "2026-03-17-central-american-vc-roundtable",
]

# Phrases the user explicitly removed/softened — should NOT appear in the after scan
RED_FLAGS = [
    "everything must be destroyed",
    "almost like a cartel",
    "lives on the edge of being removed",
    "extract value any way possible",
    "Marcus Dantus",
    "Parque Tec",
    "former IDB executive",
    "a total shame",
    "1 out of 10",
    "closer to 1",
    "rent-seeking layer",
    "no genuine impact discipline",
    "no real impact discipline",
    "Salvadoran accelerator",
    "triangular logo",
    "Secretary of Economics protecting legislative turf",
    "killed by",  # in CORFO context
]

def severity_counts(data, slug):
    entry = data.get(slug, {})
    findings = entry.get("findings", [])
    counts = {"sharp": 0, "moderate": 0, "mild": 0}
    for f in findings:
        s = f.get("severity", "?")
        if s in counts:
            counts[s] += 1
    return counts, findings

print(f"{'slug':<55} {'before s/m/m':<14} {'after s/m/m':<14}  red-flag hits")
print("-" * 110)

still_present = {}
for slug in EDITED:
    bc, _ = severity_counts(before, slug)
    ac, after_findings = severity_counts(after, slug)
    flagged = []
    for phrase in RED_FLAGS:
        for f in after_findings:
            if phrase.lower() in (f.get("quote") or "").lower():
                flagged.append(phrase)
                break
    if flagged:
        still_present[slug] = flagged
    bf = f"{bc['sharp']}/{bc['moderate']}/{bc['mild']}"
    af = f"{ac['sharp']}/{ac['moderate']}/{ac['mild']}"
    flag_summary = ", ".join(flagged) if flagged else "—"
    print(f"{slug:<55} {bf:<14} {af:<14}  {flag_summary}")

print()
print("=" * 110)
print(f"Total before: sharp={sum(severity_counts(before,s)[0]['sharp'] for s in EDITED)}, "
      f"moderate={sum(severity_counts(before,s)[0]['moderate'] for s in EDITED)}")
print(f"Total after:  sharp={sum(severity_counts(after,s)[0]['sharp'] for s in EDITED)}, "
      f"moderate={sum(severity_counts(after,s)[0]['moderate'] for s in EDITED)}")
if still_present:
    print()
    print("RED-FLAG PHRASES STILL PRESENT:")
    for slug, phrases in still_present.items():
        print(f"  {slug}: {phrases}")
else:
    print()
    print("All red-flag phrases successfully removed.")
