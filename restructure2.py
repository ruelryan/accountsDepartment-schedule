#!/usr/bin/env python3
"""Restructure schedule: insert Morning/Afternoon Session between existing shifts."""

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

def make_session_block(label, data):
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

def find_shift_end(text, header):
    """Find position after the matching </div> of the shift-card containing given header."""
    idx = text.find(f'<span class="shift-time">{header}</span>')
    if idx == -1:
        return -1
    card_start = text.rfind('<div class="shift-card">', 0, idx)
    if card_start == -1:
        return -1
    pos = card_start + len('<div class="shift-card">')
    depth = 1
    while pos < len(text) and depth > 0:
        if text[pos:pos+4] == '<div' and text[pos:pos+5] != '</div':
            close = text.find('>', pos)
            if close != -1:
                pos = close + 1
                depth += 1
                continue
        elif text[pos:pos+6] == '</div>':
            depth -= 1
            if depth == 0:
                return pos + 6
            pos += 6
            continue
        else:
            pos += 1
    return -1

days = ['fri', 'sat', 'sun']
day_keys = {'fri': 0, 'sat': 1, 'sun': 2}

for day_key in days:
    for stype, after_header in [('morning', '8:20am - Opening Song (Morning)'),
                                 ('afternoon', '12:55pm - Opening Song (Afternoon)')]:
        label = 'Morning Session' if stype == 'morning' else 'Afternoon Session'
        block = make_session_block(label, session_data[day_key][stype])
        shift_end = find_shift_end(html, after_header)
        if shift_end == -1:
            print(f"ERROR: '{after_header}' for {day_key}")
            continue
        # Skip any trailing newlines
        while shift_end < len(html) and html[shift_end] == '\n':
            shift_end += 1
        html = html[:shift_end] + '\n' + block + '\n' + html[shift_end:]
        print(f"OK: {day_key} {label}")

with open('/tmp/accountsDepartment-schedule/index.html', 'w') as f:
    f.write(html)

print("=" * 50)
for day_key in days:
    day_id = f'day-{day_key}'
    ds = html.find(f'<div id="{day_id}"')
    if day_key == 'sun':
        de = html.find('<div class="counters-section"', ds)
    else:
        de = html.find(f'<div id="day-{days[day_keys[day_key]+1]}"', ds)
    if de == -1: de = len(html)
    dc = html[ds:de]
    count = dc.count('<div class="shift-card">')
    headers = re.findall(r'<span class="shift-time">(.*?)</span>', dc)
    print(f"{day_key}: {count} shifts — {' | '.join(headers)}")
