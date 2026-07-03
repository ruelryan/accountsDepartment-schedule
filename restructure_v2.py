#!/usr/bin/env python3
"""Restructure schedule: 6 shifts per day. Properly day-scoped."""

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

def get_day_bounds(text, day_id):
    """Get (start, end) of a day panel."""
    ds = text.find(f'<div id="{day_id}"')
    if ds == -1:
        return None
    days = ['day-fri', 'day-sat', 'day-sun']
    idx = days.index(day_id)
    if idx == len(days) - 1:  # sun
        de = text.find('<div class="counters-section"', ds)
    else:
        de = text.find(f'<div id="{days[idx+1]}"', ds)
    if de == -1:
        de = len(text)
    return (ds, de)

def find_shift_end_in_range(text, header, range_start, range_end):
    """Find the end position of shift-card with header within range."""
    h = f'<span class="shift-time">{header}</span>'
    idx = text.find(h, range_start, range_end)
    if idx == -1:
        return None
    
    card_start = text.rfind('<div class="shift-card">', range_start, idx)
    if card_start == -1:
        return None
    
    pos = card_start + len('<div class="shift-card">')
    depth = 1
    while pos < range_end and depth > 0:
        next_open = text.find('<div', pos, range_end)
        next_close = text.find('</div>', pos, range_end)
        if next_close != -1 and (next_open == -1 or next_close < next_open):
            depth -= 1
            if depth == 0:
                return next_close + 6
            pos = next_close + 6
        elif next_open != -1:
            close = text.find('>', next_open, range_end)
            if close != -1 and close - next_open < 200:
                pos = close + 1
                depth += 1
            else:
                pos = next_open + 4
        else:
            break
    return None

# Do ALL insertions — process each day independently by working with day-range
days = ['day-fri', 'day-sat', 'day-sun']
day_short = {'day-fri': 'fri', 'day-sat': 'sat', 'day-sun': 'sun'}

for day_id in days:
    bounds = get_day_bounds(html, day_id)
    if bounds is None:
        print(f"ERROR: {day_id} not found")
        continue
    ds, de = bounds
    short = day_short[day_id]
    
    # Insert Morning Session after the first shift (8:20am...)
    end1 = find_shift_end_in_range(html, '8:20am - Opening Song (Morning)', ds, de)
    if end1 is None:
        print(f"ERROR: {day_id} first shift not found")
        continue
    
    morning_block = make_block('Morning Session', session_data[short]['morning'])
    # Skip trailing newlines
    while end1 < de and html[end1] == '\n':
        end1 += 1
    html = html[:end1] + '\n' + morning_block + '\n' + html[end1:]
    
    # Adjust de since we inserted text
    de += len(morning_block) + 2  # +2 for newlines
    
    # Insert Afternoon Session after the 4th shift (12:55pm...)
    end4 = find_shift_end_in_range(html, '12:55pm - Opening Song (Afternoon)', ds, de)
    if end4 is None:
        print(f"ERROR: {day_id} fourth shift not found")
        continue
    
    afternoon_block = make_block('Afternoon Session', session_data[short]['afternoon'])
    while end4 < de and html[end4] == '\n':
        end4 += 1
    html = html[:end4] + '\n' + afternoon_block + '\n' + html[end4:]

with open('index.html', 'w') as f:
    f.write(html)

print("=" * 50)
for day_id in days:
    bounds = get_day_bounds(html, day_id)
    if bounds is None: continue
    dc = html[bounds[0]:bounds[1]]
    count = dc.count('<div class="shift-card">')
    headers = re.findall(r'<span class="shift-time">(.*?)</span>', dc)
    print(f"{day_id}: {count} shifts — {' | '.join(headers)}")
