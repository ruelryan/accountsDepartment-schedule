#!/usr/bin/env python3
"""Restructure schedule: 6 shifts per day."""

import re

with open('index.html') as f:
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

def find_shift_section(text, header):
    """Find (start, end) of shift-card containing given header."""
    h = f'<span class="shift-time">{header}</span>'
    idx = text.find(h)
    if idx == -1:
        return None
    card_start = text.rfind('<div class="shift-card">', 0, idx)
    if card_start == -1:
        return None
    pos = card_start + len('<div class="shift-card">')
    depth = 1
    while pos < len(text) and depth > 0:
        next_open = text.find('<div', pos)
        next_close = text.find('</div>', pos)
        if next_close != -1 and (next_open == -1 or next_close < next_open):
            depth -= 1
            if depth == 0:
                return (card_start, next_close + 6)
            pos = next_close + 6
        elif next_open != -1:
            close = text.find('>', next_open)
            if close != -1 and close - next_open < 200:
                pos = close + 1
                depth += 1
            else:
                pos = next_open + 4
        else:
            break
    return None

# Insert in reverse order so earlier positions don't shift
insertions = [
    ('sun', 'afternoon', '12:55pm - Opening Song (Afternoon)'),
    ('sun', 'morning', '8:20am - Opening Song (Morning)'),
    ('sat', 'afternoon', '12:55pm - Opening Song (Afternoon)'),
    ('sat', 'morning', '8:20am - Opening Song (Morning)'),
    ('fri', 'afternoon', '12:55pm - Opening Song (Afternoon)'),
    ('fri', 'morning', '8:20am - Opening Song (Morning)'),
]

for day_key, stype, after_header in insertions:
    label = 'Morning Session' if stype == 'morning' else 'Afternoon Session'
    block = make_block(label, session_data[day_key][stype])
    result = find_shift_section(html, after_header)
    if result is None:
        print(f"ERROR: '{after_header}' for {day_key}")
        continue
    start, end = result
    while end < len(html) and html[end] == '\n':
        end += 1
    html = html[:end] + '\n' + block + '\n' + html[end:]
    print(f"OK: {day_key} {label}")

with open('index.html', 'w') as f:
    f.write(html)

print("=" * 50)
days = ['fri', 'sat', 'sun']
for day_key in days:
    day_id = f'day-{day_key}'
    ds = html.find(f'<div id="{day_id}"')
    if day_key == 'sun':
        de = html.find('<div class="counters-section"', ds)
    else:
        de = html.find(f'<div id="day-{days[days.index(day_key)+1]}"', ds)
    if de == -1: de = len(html)
    dc = html[ds:de]
    count = dc.count('<div class="shift-card">')
    headers = re.findall(r'<span class="shift-time">(.*?)</span>', dc)
    print(f"{day_key}: {count} shifts — {' | '.join(headers)}")
