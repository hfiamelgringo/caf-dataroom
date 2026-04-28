"""One-off: count people with multiple interview sessions in mailmerge_contacts.csv."""
import csv
from collections import defaultdict

emails = defaultdict(list)
names_no_email = defaultdict(list)
with open("audit/mailmerge_contacts.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["name"].startswith("("):
            continue
        if r["email"]:
            emails[r["email"]].append((r["name"], r["interview_slug"]))
        else:
            names_no_email[r["name"]].append(r["interview_slug"])

print("Multi-interview people (by email):")
multi_email = [(e, rows) for e, rows in emails.items() if len(rows) > 1]
for e, rows in multi_email:
    print(f"  {e} ({rows[0][0]}): {len(rows)}")
    for _, slug in rows:
        print(f"    - {slug}")

print()
print("Multi-interview people (no email):")
multi_no = [(n, s) for n, s in names_no_email.items() if len(s) > 1]
for n, s in multi_no:
    print(f"  {n}: {len(s)}")

print()
print(f"Total people: {len(emails) + len(names_no_email)}")
print(f"Multi-interview: {len(multi_email) + len(multi_no)}")
