"""
Extract sections from the CAF Google Doc export into individual markdown files.
"""
import json
import re
import os
import sys

SOURCE_FILE = r"C:\Users\JonathanNelson\.claude\projects\C--Users-JonathanNelson-OneDrive---Hackers-Founders-src-caf\d19187cd-f5cb-4d8a-bd7d-a3e459113308\tool-results\mcp-c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75-google_drive_fetch-1776111540625.txt"
OUTPUT_DIR = r"C:\Users\JonathanNelson\OneDrive - Hackers Founders\src\caf\content_data\sections"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the JSON and extract text
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
inner = json.loads(data[0]['text'])
text = inner['text']

# Cut off deprecated/strikethrough content
cutoff_marker = "**~~CAF"
cutoff_pos = text.find(cutoff_marker)
if cutoff_pos > 0:
    text = text[:cutoff_pos].rstrip()
    print(f"Cut deprecated content at position {cutoff_pos}. Active text length: {len(text)}")


def clean_markdown(content):
    """Clean up Google Docs export artifacts."""
    # Fix escaped characters
    content = content.replace('\\&', '&')
    content = content.replace('\\.', '.')
    content = content.replace('\\#', '#')
    # Remove image placeholders - replace with figure notes
    content = re.sub(r'!\[.*?\]\(.*?\)', '[Figure: see original document]', content)
    # Clean up excessive blank lines
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    # Strip trailing whitespace on lines
    content = '\n'.join(line.rstrip() for line in content.split('\n'))
    return content.strip()


def make_header(section_type, order, title, country_code=""):
    """Create the YAML-like header comment."""
    return f"""<!-- section_type: {section_type} -->
<!-- order: {order} -->
<!-- country_code: {country_code} -->
<!-- title: {title} -->

"""


def extract_between(start_pattern, end_pattern, source_text):
    """Extract text between two patterns."""
    start_match = re.search(start_pattern, source_text, re.MULTILINE)
    if not start_match:
        print(f"  WARNING: Could not find start pattern: {start_pattern}")
        return ""
    start_pos = start_match.start()

    if end_pattern:
        end_match = re.search(end_pattern, source_text[start_pos + 1:], re.MULTILINE)
        if end_match:
            end_pos = start_pos + 1 + end_match.start()
        else:
            end_pos = len(source_text)
    else:
        end_pos = len(source_text)

    return source_text[start_pos:end_pos].strip()


# Define section extractions using heading positions
# We'll find positions of key headings and slice between them
heading_positions = []
for m in re.finditer(r'^#+\s+.*', text, re.MULTILINE):
    heading_positions.append((m.start(), m.group().strip()))

# Build a position lookup
def find_heading_pos(search_text):
    for pos, h in heading_positions:
        if search_text in h:
            return pos
    return None

def text_between_headings(start_search, end_search):
    """Get text from heading containing start_search to heading containing end_search."""
    start = find_heading_pos(start_search)
    if start is None:
        print(f"  WARNING: Could not find heading containing: {start_search}")
        return ""
    if end_search:
        end = find_heading_pos(end_search)
        if end is None:
            print(f"  WARNING: Could not find end heading: {end_search}")
            return text[start:].strip()
        return text[start:end].strip()
    return text[start:].strip()


# --- SECTION DEFINITIONS ---

sections = [
    {
        "filename": "01_introduction.md",
        "section_type": "introduction",
        "order": 1,
        "title": "Introduction and Background",
        "start": "1\\. Introduction and Background",
        "end": "2\\. Executive Summary",
    },
    {
        "filename": "02_executive_summary.md",
        "section_type": "executive_summary",
        "order": 2,
        "title": "Executive Summary",
        "start": "2\\. Executive Summary",
        "end": "3\\. Four Macro Recommendations",
    },
    {
        "filename": "03_recommendation_public_resources.md",
        "section_type": "recommendation",
        "order": 3,
        "title": "Public Resources",
        "start": "3.1a Public Resources",
        "end": "3.1b Pension Fund",
    },
    {
        "filename": "03_recommendation_pension_reform.md",
        "section_type": "recommendation",
        "order": 4,
        "title": "Pension Fund Allocation Reform",
        "start": "3.1b Pension Fund",
        "end": "3.2a Exits and Secondary",
    },
    {
        "filename": "03_recommendation_exits_secondary.md",
        "section_type": "recommendation",
        "order": 5,
        "title": "Exits and Secondary Markets",
        "start": "3.2a Exits and Secondary",
        "end": "3.3a Regional Funds",
    },
    {
        "filename": "03_recommendation_fund_of_funds.md",
        "section_type": "recommendation",
        "order": 6,
        "title": "Regional Funds of Funds",
        "start": "3.3a Regional Funds",
        "end": "3.4a Bridge to Silicon Valley",
    },
    {
        "filename": "03_recommendation_sv_bridge.md",
        "section_type": "recommendation",
        "order": 7,
        "title": "Bridge to Silicon Valley",
        "start": "3.4a Bridge to Silicon Valley",
        "end": "4\\. Overall Insights",
    },
    {
        "filename": "04_insights_framing.md",
        "section_type": "insights",
        "order": 8,
        "title": "Introduction and Framing",
        "start": "4\\. Overall Insights",
        "end": "4.3 Themes Across",
    },
    {
        "filename": "04_insights_themes.md",
        "section_type": "insights",
        "order": 9,
        "title": "Themes Across the Four Countries",
        "start": "4.3 Themes Across",
        "end": "4.4 Context and Comparator",
    },
    {
        "filename": "04_insights_comparators.md",
        "section_type": "insights",
        "order": 10,
        "title": "Context, Comparators, and Ecosystem Models",
        "start": "4.4 Context and Comparator",
        "end": "4.7 Comparative Analysis",
    },
    {
        "filename": "04_insights_scorecards.md",
        "section_type": "insights",
        "order": 11,
        "title": "Comparative Analysis - Ecosystem Scorecard and Gap Matrix",
        "start": "4.7 Comparative Analysis",
        "end": "5\\. Small Ideas",
    },
    {
        "filename": "05_small_ideas.md",
        "section_type": "small_ideas",
        "order": 12,
        "title": "Small Ideas",
        "start": "5\\. Small Ideas",
        "end": "6\\. Country Summary",
    },
    {
        "filename": "06_country_guatemala.md",
        "section_type": "country_profile",
        "order": 13,
        "title": "Guatemala",
        "country_code": "GT",
        "start": "6.1 Guatemala",
        "end": "6.2 Costa Rica",
    },
    {
        "filename": "06_country_costa_rica.md",
        "section_type": "country_profile",
        "order": 14,
        "title": "Costa Rica",
        "country_code": "CR",
        "start": "6.2 Costa Rica",
        "end": "6.3 Dominican Republic",
    },
    {
        "filename": "06_country_dominican_republic.md",
        "section_type": "country_profile",
        "order": 15,
        "title": "Dominican Republic",
        "country_code": "DO",
        "start": "6.3 Dominican Republic",
        "end": "6.4 Honduras",
    },
    {
        "filename": "06_country_honduras.md",
        "section_type": "country_profile",
        "order": 16,
        "title": "Honduras",
        "country_code": "HN",
        "start": "6.4 Honduras",
        "end": "7\\. Annexes",
    },
    {
        "filename": "07_annexes.md",
        "section_type": "annexes",
        "order": 17,
        "title": "Annexes",
        "start": "7\\. Annexes",
        "end": "8\\. Orphan Insights",
    },
    {
        "filename": "08_references.md",
        "section_type": "references",
        "order": 18,
        "title": "References",
        "start": "9\\. References",
        "end": None,
    },
]

# Special handling: we also need to capture Orphan Insights (between Annexes and References)
# and the "3. Four Macro Recommendations" intro line
# Also need to handle the "Absence of Institutional Investor Participation" subsection
# which falls between Pension Reform and Exits - include it in pension reform section

# Process sections
for sec in sections:
    print(f"Extracting: {sec['filename']}")
    content = text_between_headings(sec["start"], sec.get("end"))

    if not content:
        print(f"  EMPTY - skipping")
        continue

    content = clean_markdown(content)

    # Build header
    header = make_header(
        sec["section_type"],
        sec["order"],
        sec["title"],
        sec.get("country_code", "")
    )

    # Write file
    filepath = os.path.join(OUTPUT_DIR, sec["filename"])
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + content + '\n')
    print(f"  Written: {filepath} ({len(content)} chars)")

# Special: handle the pension reform file to include the "Absence of Institutional" subsection
# Already handled by the range 3.1b -> 3.2a which includes 3.1c

# Special: handle Orphan Insights - append to references or small ideas?
# Let's just note it's captured in the annexes range if present
orphan_content = text_between_headings("8\\. Orphan Insights", "9\\. References")
if orphan_content:
    # Append orphan insights to the annexes file
    orphan_content = clean_markdown(orphan_content)
    annexes_path = os.path.join(OUTPUT_DIR, "07_annexes.md")
    with open(annexes_path, 'a', encoding='utf-8') as f:
        f.write('\n\n---\n\n' + orphan_content + '\n')
    print(f"  Appended Orphan Insights to 07_annexes.md ({len(orphan_content)} chars)")

# Handle the "Four Macro Recommendations" intro (between heading 3 and 3.1a)
rec_intro = text_between_headings("3\\. Four Macro Recommendations", "3.1a Public Resources")
if rec_intro:
    rec_intro = clean_markdown(rec_intro)
    # Prepend to the public resources file
    pub_path = os.path.join(OUTPUT_DIR, "03_recommendation_public_resources.md")
    with open(pub_path, 'r', encoding='utf-8') as f:
        existing = f.read()
    with open(pub_path, 'w', encoding='utf-8') as f:
        # Insert rec intro after the header
        header_end = existing.find('\n\n', existing.rfind('-->'))
        if header_end > 0:
            f.write(existing[:header_end + 2] + rec_intro + '\n\n---\n\n' + existing[header_end + 2:])
        else:
            f.write(existing + '\n\n' + rec_intro)
    print(f"  Prepended Macro Recommendations intro to 03_recommendation_public_resources.md")

# Handle the Costa Rica "SMALL IDEAS" subsection that appears mid-country profile
# Check if it got included in Costa Rica profile
cr_path = os.path.join(OUTPUT_DIR, "06_country_costa_rica.md")
with open(cr_path, 'r', encoding='utf-8') as f:
    cr_content = f.read()
# Check for SMALL IDEAS heading in Costa Rica
if 'SMALL IDEAS' in cr_content:
    # Split at the SMALL IDEAS heading and trim it from Costa Rica
    small_idx = cr_content.find('# **SMALL IDEAS**')
    if small_idx < 0:
        small_idx = cr_content.find('SMALL IDEAS')
    if small_idx > 0:
        # Find the next country heading after SMALL IDEAS
        after_small = cr_content[small_idx:]
        dr_idx = after_small.find('## **6.3')
        if dr_idx < 0:
            dr_idx = after_small.find('6.3 Dominican')
        if dr_idx > 0:
            small_ideas_extra = after_small[:dr_idx].strip()
            # Trim Costa Rica to before SMALL IDEAS
            cr_trimmed = cr_content[:small_idx].rstrip()
            with open(cr_path, 'w', encoding='utf-8') as f:
                f.write(cr_trimmed + '\n')
            # Append the extra small ideas to the small ideas file
            si_path = os.path.join(OUTPUT_DIR, "05_small_ideas.md")
            with open(si_path, 'a', encoding='utf-8') as f:
                f.write('\n\n---\n\n' + clean_markdown(small_ideas_extra) + '\n')
            print(f"  Moved SMALL IDEAS from Costa Rica to 05_small_ideas.md")

print("\n=== DONE ===")
print(f"Files written to: {OUTPUT_DIR}")
for fn in sorted(os.listdir(OUTPUT_DIR)):
    if fn.endswith('.md'):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, fn))
        print(f"  {fn} ({size:,} bytes)")
