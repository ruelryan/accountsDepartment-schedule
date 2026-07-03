#!/usr/bin/env python3
"""Update the search table with all assignments from the 6-shift schedule."""
import re

with open('index.html') as f:
    html = f.read()

days_map = {'day-fri': 'Friday', 'day-sat': 'Saturday', 'day-sun': 'Sunday'}

# Build assignments by scanning the HTML for name-tag spans within each day
assignments = {}

# Known brothers
brothers = [
    "Charles Russel Sanico", "Cyros Rexes Madura", "Daveryl Quiban",
    "Ethan Razon", "Jeddan Jusay", "Jemrel Besere",
    "Joshe Miguel Panonce", "Remdrant Mepania", "Rinard Fandiño",
    "Vince Syriel Sanico"
]

def is_brother(name):
    return name in brothers

# Process each day
for day_id, day_label in days_map.items():
    ds = html.find(f'<div id="{day_id}"')
    if day_id == 'day-sun':
        de = html.find('<div class="counters-section"', ds)
    else:
        next_day = 'day-sat' if day_id == 'day-fri' else 'day-sun'
        de = html.find(f'<div id="{next_day}"', ds)
    if de == -1: de = len(html)
    
    day_content = html[ds:de]
    
    # Find shift-cards by locating their headers
    pos = 0
    while True:
        card_start = day_content.find('<div class="shift-card">', pos)
        if card_start == -1: break
        
        # Find the header
        hdr_start = day_content.find('<span class="shift-time">', card_start)
        hdr_end = day_content.find('</span>', hdr_start)
        if hdr_start == -1 or hdr_end == -1:
            pos = card_start + 1
            continue
        shift_label = day_content[hdr_start + len('<span class="shift-time">'):hdr_end]
        
        # Find shift-body
        body_start = day_content.find('<div class="shift-body">', card_start)
        if body_start == -1:
            pos = card_start + 1
            continue
        
        # Find end of shift-body (4th </div> after body_start)
        # <div class="shift-body"> ... </div> (for section-mini) ... </div> (for name-list/box-grid) ... </div> (for section-mini) ... </div> (for shift-body)
        # Actually the body has nested divs, but the 4th </div> from body_start is the shift-body closing
        # No that's wrong. Let me just find any </div> that's the end of the shift-card
        # Find the next shift-card or end of day
        next_card = day_content.find('<div class="shift-card">', card_start + 1)
        if next_card == -1:
            body_end = de - ds  # relative offset within day_content
        else:
            body_end = next_card
        
        body_section = day_content[body_start:body_end]
        
        # Extract all name-tags
        # Key Brothers
        kb = re.findall(r'<span class="name-tag brother-tag">(.*?)</span>', body_section)
        for name in kb:
            name = name.strip()
            if name not in assignments:
                assignments[name] = []
            assignments[name].append(f"{day_label} - Key Brother ({shift_label})")
        
        # Sisters (box attendants)
        sis = re.findall(r'<span class="name-tag sister-tag">(.*?)</span>', body_section)
        # Actually box attendants aren't in sister-tag spans, they're in box-name spans
        box_names = re.findall(r'<span class="box-name">(.*?)</span>', body_section)
        for name in box_names:
            name = name.strip()
            if name == '': continue
            if name not in assignments:
                assignments[name] = []
            assignments[name].append(f"{day_label} - Box ({shift_label})")
        
        pos = card_start + 1

# Counters (Sunday)
# Find counters section and extract names
counters_section = html[html.find('<div class="counters-section"'):html.find('<div class="search-section"')]
counter_spans = re.findall(r'<span class="name-tag (?:brother-tag|sister-tag)">(.*?)</span>', counters_section)
for name in counter_spans:
    name = name.strip()
    if name not in assignments:
        assignments[name] = []
    # Remove duplicates
    if "Sunday - Counter" not in assignments[name]:
        assignments[name].append("Sunday - Counter")

# Also check for people in old search that might have been missed (excluded names)
# Ruel Ryan Rosal should be excluded
# Add Jaye Kayla Rosal if not present
if "Jaye Kayla Rosal" not in assignments:
    assignments["Jaye Kayla Rosal"] = ["Sunday - Counter"]
elif "Sunday - Counter" not in assignments["Jaye Kayla Rosal"]:
    assignments["Jaye Kayla Rosal"].append("Sunday - Counter")

# Build search table sorted by role then name
brother_rows = []
sister_rows = []
for name in sorted(assignments.keys()):
    role = "Brother" if is_brother(name) else "Sister"
    assigs = "; ".join(assignments[name])
    row = f'<tr class="search-row"><td class="search-name">{name}</td><td class="search-role">{role}</td><td class="search-assign">{assigs}</td></tr>'
    if role == "Brother":
        brother_rows.append(row)
    else:
        sister_rows.append(row)

all_rows = brother_rows + sister_rows
search_table_html = '\n'.join(all_rows)

# Replace the tbody
old_tbody_match = re.search(r'<tbody>.*?</tbody>', html, re.DOTALL)
if old_tbody_match:
    new_tbody = f'<tbody>\n{search_table_html}\n        </tbody>'
    html = html[:old_tbody_match.start()] + new_tbody + html[old_tbody_match.end():]
    print("Search table replaced!")
else:
    print("ERROR: Could not find tbody")

with open('index.html', 'w') as f:
    f.write(html)

print(f"\nTotal volunteers: {len(assignments)}")
for name in sorted(assignments.keys()):
    role = "B" if is_brother(name) else "S"
    print(f"  [{role}] {name}: {'; '.join(assignments[name])}")
