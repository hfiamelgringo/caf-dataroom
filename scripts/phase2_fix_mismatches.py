"""Fix the misassigned moves from phase2_move_downloads.py."""
import os
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DST = REPO / "content_data" / "raw_transcripts"
SRC = Path(os.path.expandvars("%USERPROFILE%")) / "Downloads"

# 1) Rename existing misassigned files
RENAMES = [
    ("2026-04-21-jos-kont.txt", "2026-02-05-jos-kont-cuantico.txt"),
    ("2026-03-16-dave-mcclure-practical-vc.txt", "2026-03-05-dave-mcclure-practical-vc.txt"),
    ("2026-03-17-central-american-vc-roundtable-with-partnership-for-the-amer.txt", "2026-03-24-speratum-biopharma.txt"),
]

# 2) Move from Downloads with corrected names
MOVES = [
    ("Transcript Meeting with Jose Kont Quantico VP, 21-4-26.txt", "2026-04-21-jos-kont.txt"),
    ("03.16.2026. Dave McClure Practica VC.txt", "2026-03-16-dave-mcclure-practical-vc.txt"),
    ("meeting2_central_america_roundtable.md.txt", "2026-03-17-central-american-vc-roundtable.txt"),
    ("Transcript Meeting with CNBS from Honduras, 22-4-26.txt", "2026-04-22-cnbs-honduras.txt"),
    ("02.23.2026. Agostina Martino.txt", "2026-02-23-climatech-agostina-martino.txt"),
]

CLEANUP_DUPES_IN_DOWNLOADS = [
    "Transcript Meeting with CNBS from Honduras, 22-4-26 (1).txt",
    "Transcript Meeting with CNBS from Honduras, 22-4-26 (2).txt",
    "Transcript Meeting with CNBS from Honduras, 22-4-26 (3).txt",
]


def main():
    actions = []

    for old, new in RENAMES:
        op = DST / old
        np = DST / new
        if op.exists() and not np.exists():
            op.rename(np)
            actions.append(f"renamed {old} -> {new}")
        elif np.exists():
            actions.append(f"target already exists: {new}")
        else:
            actions.append(f"missing source: {old}")

    for src_name, dst_name in MOVES:
        sp = SRC / src_name
        dp = DST / dst_name
        if dp.exists():
            actions.append(f"target exists: {dst_name}")
            continue
        if not sp.exists():
            actions.append(f"missing in Downloads: {src_name}")
            continue
        shutil.move(str(sp), str(dp))
        actions.append(f"moved {src_name} -> {dst_name}")

    # Remove dupes from Downloads
    for d in CLEANUP_DUPES_IN_DOWNLOADS:
        sp = SRC / d
        if sp.exists():
            sp.unlink()
            actions.append(f"deleted dupe: {d}")

    for a in actions:
        print(a)

    # Final tally
    saved = sorted(p.name for p in DST.glob("*.txt"))
    print(f"\nFinal count in raw_transcripts/: {len(saved)}")


if __name__ == "__main__":
    main()
