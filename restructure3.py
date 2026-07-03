#!/usr/bin/env python3
"""Restructure by finding shift-cards and their proper ends using the footer pattern."""

import re

with open('/tmp/accountsDepartment-schedule/index.html', 'r') as f:
    html = f.read()

session_data = {
    'fri': {
        'morning': {'kb': ['Charles Russel Sanico', 'Cyros Rexes Madura'],
                     'boxes': {8: 'Jona Mae Case Palero', 9: 'Jerlie Mae Morandante', 10: 'Mary Grace Dasal'}},
        'afternoon': {'kb': ['Jemrel Besere', 'Ethan Razon'],
                      'boxes': {8: 'Haidee Bulanon', 9: 'Cyra Mae', 10: 'Anja Raye Casicas'}}
    },
    'sat': {
        'morning': {'kb': ['Daveryl Quiban', 'Jemrel Besere'],
                     'boxes': {8: 'Ellah Tangog De Paz', 9: 'Kyla Marie Pagaran', 10: 'Faith Talavera'}},
        'afternoon': {'kb': ['Vince Syriel Sanico', 'Jemrel Besere'],
                      'boxes': {8: 'Johna Mae Eme', 9: 'Cyra Mae', 10: 'Lady Jane Gay'}}
    },
    'sun': {
        'morning': {'kb': ['Joshe Miguel Panonce', 'Cyros Rexes Madura'],
                     'boxes': {8: 'Elah Manto', 9: 'Ellah Tangog De Paz', 10: 'Jera Butalon'}},
        'afternoon': {'kb': ['Daveryl Quiban', 'Charles Russel Sanico'],
                      'boxes': {8: 'Quenette Jean De Paz', 9: 'Zared Mae Laran', 10: 'Jercel Butalon'}}
    }
}

def make_block(label, data):
    kb = ''.join(f'<span class="name-tag brother-tag">{n}</span>' for n in data['kb'])
    b = data['boxes']
    return f'''<div class="shift-card">
<div class="shift-header"><span class="shift-time">{label}</span></div>
<div class="shift-body">
<div class="section-mini"><h4>Key Brothers</h4>
<div class="name-list">{kb}</div></div>
<div class="section-mini"><h4>Box Attendants</h4>
<div class="box-grid">
<div class="box-row"><span class="box-num">Box 8</span><span class="box-name">{b[8]}</span></div><div class="box-row"><span class="box-num">Box 9</span><span class="box-name">{b[9]}</span></div><div class="box-row"><span class="box-num">Box 10</span><span class="box-name">{b[10]}</span></div></div></div>
</div>
</div>'''

# Key insight: each shift-card in the HTML looks like:
# <div class="shift-card">\n<div class="shift-header">...10 boxes...\n</div>\n</div>\n
# The shift-card ends with:
#   </div>\n</div>\n
#   OR
#   </div>\n</div>\n\n  (blank line before next shift)

# Better approach: find the shift-card by its header, then find its end by
# counting to the 4th </div> after a specific marker (the last box-row).

# Or even simpler: Find the specific marker pattern at the end of each shift.
# All shifts end with: ...</div></div>\n</div>\n</div>
# After which comes either \n<div (next shift-card) or \n\n (blank line before next section)

# Let me use a regex that finds complete shift-card sections.
# Pattern: <div class="shift-card"> ... </div>\n</div>\n(?:\n|$|</div>|<div)

# Even simpler: I'll find each shift by its header span and find the matching end
# by looking for the third </div> after the last box-10 entry.

# Let me just find each shift and compute its end properly.

def find_shift_section(text, header):
    """Find (start, end) of the shift-card section containing given header."""
    h = f'<span class="shift-time">{header}</span>'
    idx = text.find(h)
    if idx == -1:
        return None
    # Find containing shift-card start
    card_start = text.rfind('<div class="shift-card">', 0, idx)
    if card_start == -1:
        return None
    
    # Parse nesting from card_start to find matching close
    pos = card_start + len('<div class="shift-card">')
    depth = 1
    while pos < len(text) and depth > 0:
        # Check for opening <div
        if text[pos:pos+4] == '<div':
            # Could be closing </div>
            if text[pos:pos+6] == '</div>':
                depth -= 1
                if depth == 0:
                    return (card_start, pos + 6)
                pos += 6
            else:
                # Opening tag - find the end >
                close = text.find('>', pos)
                if close == -1 or close - pos > 200:  # sanity check
                    pos += 4
                else:
                    pos = close + 1
                    depth += 1
        else:
            pos += 1
    
    return None

# Do insertions in reverse order so positions don't shift
# Order: Sunday afternoon, Sunday morning, Saturday afternoon, Saturday morning, Friday afternoon, Friday morning
insertion_order = [
    ('sun', 'afternoon', '12:55pm - Opening Song (Afternoon)'),
    ('sun', 'morning', '8:20am - Opening Song (Morning)'),
    ('sat', 'afternoon', '12:55pm - Opening Song (Afternoon)'),
    ('sat', 'morning', '8:20am - Opening Song (Morning)'),
    ('fri', 'afternoon', '12:55pm - Opening Song (Afternoon)'),
    ('fri', 'morning', '8:20am - Opening Song (Morning)'),
]

for day_key, stype, after_header in insertion_order:
    label = 'Morning Session' if stype == 'morning' else 'Afternoon Session'
    block = make_block(label, session_data[day_key][stype])
    
    result = find_shift_section(html, after_header)
    if result is None:
        print(f"ERROR: '{after_header}' for {day_key}")
        continue
    
    start, end = result
    # Insert after the shift end
    while end < len(html) and html[end] == '\n':
        end += 1
    html = html[:end] + '\n' + block + '\n' + html[end:]
    print(f"OK: {day_key} {label}")

with open('/tmp/accountsDepartment-schedule/index.html', 'w') as f:
    f.write(html)

print("=" * 50)
days = ['fri', 'sat', 'sun']
for day_key in days:
    day_id = f'day-{day_key}'
    ds = html.find(f'<div id="{day_id}"')
    if day_key == 'sun':
        de = html.find('<div class="counters-section"', ds)
    else:
        next_day = days[days.index(day_key)+1]
        de = html.find(f'<div id="day-{next_day}"', ds)
    if de == -1: de = len(html)
    dc = html[ds:de]
    count = dc.count('<div class="shift-card">')
    headers = re.findall(r'<span class="shift-time">(.*?)</span>', dc)
    print(f"{day_key}: {count} shifts — {' | '.join(headers)}")
