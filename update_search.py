#!/usr/bin/env python3
"""Update the search table with new session shift assignments."""
import re

with open('index.html') as f:
    html = f.read()

days_map = {'day-fri': ('Friday', 'July 10, 2026'), 'day-sat': ('Saturday', 'July 11, 2026'), 'day-sun': ('Sunday', 'July 12, 2026')}
short_days = {'day-fri': 'fri', 'day-sat': 'sat', 'day-sun': 'sun'}

# Extract all assignments from the schedule
assignments = {}  # name -> [assignment strings]

for day_id, (day_label, _) in days_map.items():
    ds = html.find(f'<div id="{day_id}"')
    if day_id == 'day-sun':
        de = html.find('<div class="counters-section"', ds)
    else:
        next_id = 'day-sat' if day_id == 'day-fri' else 'day-sun'
        de = html.find(f'<div id="{next_id}"', ds)
    if de == -1: de = len(html)
    
    day_content = html[ds:de]
    
    # Find each shift-card in this day
    shift_pattern = re.compile(
        r'<div class="shift-card">\s*<div class="shift-header"><span class="shift-time">(.*?)</span></div>\s*'
        r'<div class="shift-body">(.*?)</div>\s*</div>', re.DOTALL
    )
    
    for match in shift_pattern.finditer(day_content):
        shift_label = match.group(1)
        body = match.group(2)
        
        # Key Brothers
        kb = re.findall(r'<span class="name-tag brother-tag">(.*?)</span>', body)
        for name in kb:
            name = name.strip()
            if name not in assignments:
                assignments[name] = []
            assignments[name].append(f"{day_label} - Key Brother ({shift_label})")
        
        # Box Attendants
        boxes = re.findall(r'<div class="box-row"><span class="box-num">Box \d+</span><span class="box-name">(.*?)</span></div>', body)
        for name in boxes:
            name = name.strip()
            if name not in assignments:
                assignments[name] = []
            assignments[name].append(f"{day_label} - Box ({shift_label})")

# Counters (Sunday)
counters_match = re.search(
    r'<div class="counters-section">.*?<div class="name-list">(.*?)</div>',
    html, re.DOTALL
)
if counters_match:
    counter_list = counters_match.group(1)
    counter_names = re.findall(r'<span class="name-tag (?:brother-tag|sister-tag)">(.*?)</span>', counter_list)
    for name in counter_names:
        name = name.strip()
        if name not in assignments:
            assignments[name] = []
        assignments[name].append("Sunday - Counter")

# Determine brother/sister by checking existing data
# Known brothers
brothers = [
    "Charles Russel Sanico", "Cyros Rexes Madura", "Daveryl Quiban",
    "Ethan Razon", "Jeddan Jusay", "Jemrel Besere",
    "Joshe Miguel Panonce", "Remdrant Mepania", "Rinard Fandiño",
    "Vince Syriel Sanico"
]

def is_brother(name):
    return name in brothers

# Build search table rows
rows = []
for name in sorted(assignments.keys()):
    role = "Brother" if is_brother(name) else "Sister"
    assigs = "; ".join(assignments[name])
    rows.append(f'<tr class="search-row"><td class="search-name">{name}</td><td class="search-role">{role}</td><td class="search-assign">{assigs}</td></tr>')

search_table_html = '\n'.join(rows)

# Find and replace the search table body
old_pattern = r'<tbody>.*?</tbody>'
new_tbody = f'<tbody>\n{search_table_html}\n        </tbody>'
html = re.sub(old_pattern, new_tbody, html, count=1, flags=re.DOTALL)

with open('index.html', 'w') as f:
    f.write(html)

print("Search table updated!")
print(f"Total volunteers in search: {len(assignments)}")
for name in sorted(assignments.keys()):
    print(f"  {name}: {'; '.join(assignments[name])}")
