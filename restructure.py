#!/usr/bin/env python3
"""Restructure the Accounts Department Schedule: 6 shifts per day."""

import re

with open('/tmp/accountsDepartment-schedule/index.html', 'r') as f:
    html = f.read()

session_data = {
    'fri': {
        'morning_session': {
            'key_brothers': ['Charles Russel Sanico', 'Cyros Rexes Madura'],
            'boxes': {8: 'Jona Mae Case Palero', 9: 'Jerlie Mae Morandante', 10: 'Mary Grace Dasal'}
        },
        'afternoon_session': {
            'key_brothers': ['Jemrel Besere', 'Ethan Razon'],
            'boxes': {8: 'Haidee Bulanon', 9: 'Cyra Mae', 10: 'Anja Raye Casicas'}
        }
    },
    'sat': {
        'morning_session': {
            'key_brothers': ['Daveryl Quiban', 'Jemrel Besere'],
            'boxes': {8: 'Ellah Tangog De Paz', 9: 'Kyla Marie Pagaran', 10: 'Faith Talavera'}
        },
        'afternoon_session': {
            'key_brothers': ['Vince Syriel Sanico', 'Jemrel Besere'],
            'boxes': {8: 'Johna Mae Eme', 9: 'Cyra Mae', 10: 'Lady Jane Gay'}
        }
    },
    'sun': {
        'morning_session': {
            'key_brothers': ['Joshe Miguel Panonce', 'Cyros Rexes Madura'],
            'boxes': {8: 'Elah Manto', 9: 'Ellah Tangog De Paz', 10: 'Jera Butalon'}
        },
        'afternoon_session': {
            'key_brothers': ['Daveryl Quiban', 'Charles Russel Sanico'],
            'boxes': {8: 'Quenette Jean De Paz', 9: 'Zared Mae Laran', 10: 'Jercel Butalon'}
        }
    }
}

def make_shift(day_key, stype):
    data = session_data[day_key][stype]
    kb = ''.join(f'<span class="name-tag brother-tag">{n}</span>' for n in data['key_brothers'])
    label = 'Morning Session' if stype == 'morning_session' else 'Afternoon Session'
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

def end_of_shift(text, start):
    """Find position after the 3rd </div> closing tag from start (shift-card's </div>)."""
    pos = start
    for _ in range(3):
        pos = text.find('</div>', pos)
        if pos == -1:
            return -1
        pos += 6
    return pos

days = ['fri', 'sat', 'sun']

for day_key in days:
    day_id = f'day-{day_key}'
    day_start = html.find(f'<div id="{day_id}"')
    if day_start == -1:
        print(f"ERROR: {day_id} not found"); continue
    
    # Find 4 original shift positions
    search_from = day_start
    positions = []
    for _ in range(10):
        p = html.find('<div class="shift-card">', search_from)
        if p == -1: break
        if day_key == 'sun':
            cp = html.find('<div class="counters-section"')
            if cp != -1 and p > cp: break
        else:
            np = html.find(f'<div id="day-{days[days.index(day_key)+1]}"')
            if np != -1 and p > np: break
        positions.append(p)
        search_from = p + len('<div class="shift-card">')
    
    print(f"{day_key}: {len(positions)} shifts before")
    if len(positions) < 4: continue
    
    # Morning Session after shift 1 (index 0)
    e1 = end_of_shift(html, positions[0])
    if e1 == -1: continue
    html = html[:e1] + '\n' + make_shift(day_key, 'morning_session') + '\n' + html[e1:]
    
    # Re-find for afternoon
    search_from = day_start
    positions = []
    for _ in range(10):
        p = html.find('<div class="shift-card">', search_from)
        if p == -1: break
        if day_key == 'sun':
            cp = html.find('<div class="counters-section"')
            if cp != -1 and p > cp: break
        else:
            np = html.find(f'<div id="day-{days[days.index(day_key)+1]}"')
            if np != -1 and p > np: break
        positions.append(p)
        search_from = p + len('<div class="shift-card">')
    
    print(f"{day_key}: {len(positions)} shifts after morning insert")
    if len(positions) < 5: continue
    
    # Afternoon Session after shift 4 (index 3)
    e4 = end_of_shift(html, positions[3])
    if e4 == -1: continue
    html = html[:e4] + '\n' + make_shift(day_key, 'afternoon_session') + '\n' + html[e4:]

with open('/tmp/accountsDepartment-schedule/index.html', 'w') as f:
    f.write(html)

print("=" * 50)
print("Done! Verifying...")

for day_key in days:
    day_id = f'day-{day_key}'
    ds = html.find(f'<div id="{day_id}"')
    de = html.find(f'<div id="day-', ds + 10) if day_key != 'sun' else html.find('<div class="counters-section"', ds)
    if de == -1: de = len(html)
    dc = html[ds:de]
    count = dc.count('<div class="shift-card">')
    headers = re.findall(r'<span class="shift-time">(.*?)</span>', dc)
    print(f"{day_key}: {count} shifts — {headers}")
