#!/usr/bin/env python3
"""
Generate Accounts Department volunteer schedule HTML with conflict checking.
Reads volunteer list and conflict data from CSVs, maps messenger names to real names,
and produces the schedule HTML with conflicts properly enforced.

6 shifts per day x 3 days = 18 shifts:
  shift1, shift2, shift3, shift4  -- 10 boxes (1-10) + 2 key brothers
  morningsession, afternoonsession -- 3 boxes (8,9,10) + 2 key brothers
"""

import csv
import random

random.seed(42)

# ── Load volunteers ──────────────────────────────────────────────────────────
volunteers = []
with open('/opt/data/volunteers.csv', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip blank header
    for row in reader:
        if len(row) < 5:
            continue
        num = row[1].strip()
        messenger_name = row[2].strip()
        real_name = row[3].strip()
        role = row[4].strip()
        if not num or not real_name:
            continue
        volunteers.append({
            'messenger': messenger_name,
            'real_name': real_name,
            'role': role,
        })

# Remove duplicates by real_name (keep first)
seen = set()
unique = []
for v in volunteers:
    if v['real_name'] not in seen:
        seen.add(v['real_name'])
        unique.append(v)
volunteers = unique

# ── OVERRIDE: Jona Mae Case Palero is actually a Sister, not a Brother ─────
for v in volunteers:
    if v['real_name'] == 'Jona Mae Case Palero':
        v['role'] = 'Sister'
        print(f"OVERRIDE: {v['real_name']}: changed role from Brother to Sister")

brothers = [v for v in volunteers if v['role'] == 'Brother']
sisters = [v for v in volunteers if v['role'] == 'Sister']

print(f"Volunteers: {len(volunteers)} total, {len(brothers)} brothers, {len(sisters)} sisters")

messenger_to_real = {v['messenger']: v['real_name'] for v in volunteers}

# ── Load conflict data ───────────────────────────────────────────────────────
# Column index -> (day_key, shift_key)
# Columns 0-8 from original CSV, plus 3 new for morningsession
COL_NAMES = [
    ('fri', 'shift1'),
    ('fri', 'shift23'),
    ('fri', 'shift4counters'),
    ('sat', 'shift1'),
    ('sat', 'shift23'),
    ('sat', 'shift4counters'),
    ('jedloyd', 'all'),
    ('sun', 'shift23'),
    ('sun', 'shift4counters'),
    # NEW: morning session columns (after the original 9)
    ('fri', 'morningsession'),
    ('sat', 'morningsession'),
    ('sun', 'morningsession'),
]

conflicts = {}  # (day, conflict_key) -> set of real_names who CANNOT work

with open('/opt/data/conflicts.csv', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        for col_idx, name in enumerate(row):
            name = name.strip()
            if not name:
                continue
            if col_idx >= len(COL_NAMES):
                continue  # extra columns ignored

            day, shift_key = COL_NAMES[col_idx]
            real = messenger_to_real.get(name, name)

            if day == 'jedloyd':
                # Special column: names here can't work ANY shift where Jedloyd is scheduled
                for d in ['fri', 'sat', 'sun']:
                    for s in ['shift1', 'shift23', 'shift4counters', 'morningsession']:
                        k = (d, s)
                        if k not in conflicts:
                            conflicts[k] = set()
                        conflicts[k].add(real)
            else:
                k = (day, shift_key)
                if k not in conflicts:
                    conflicts[k] = set()
                conflicts[k].add(real)

print(f"\nConflict sets:")
for k, names in sorted(conflicts.items()):
    n_sisters = sum(1 for s in sisters if s['real_name'] in names)
    n_brothers = sum(1 for b in brothers if b['real_name'] in names)
    print(f"  {k}: {len(names)} total ({n_sisters} sisters, {n_brothers} brothers)")

# Check available sisters per shift after conflicts
print(f"\nAvailable sisters per shift (out of {len(sisters)} total):")
for day in ['fri', 'sat', 'sun']:
    for ck in ['shift1', 'shift23', 'shift4counters', 'morningsession']:
        k = (day, ck)
        conflicted = conflicts.get(k, set())
        available = [s['real_name'] for s in sisters if s['real_name'] not in conflicted]
        print(f"  {day}/{ck}: {len(available)} available")

# Check available brothers per shift
print(f"\nAvailable brothers per shift (out of {len(brothers)} total):")
for day in ['fri', 'sat', 'sun']:
    for ck in ['shift1', 'shift23', 'shift4counters', 'morningsession']:
        k = (day, ck)
        conflicted = conflicts.get(k, set())
        available = [b['real_name'] for b in brothers if b['real_name'] not in conflicted]
        print(f"  {day}/{ck}: {len(available)} available")

# ── Schedule structure ───────────────────────────────────────────────────────
DAYS = ['fri', 'sat', 'sun']
DAY_LABEL = {'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday'}
DAY_DATE = {'fri': 'July 10, 2026', 'sat': 'July 11, 2026', 'sun': 'July 12, 2026'}
DAY_PANEL = {'fri': 'day-fri', 'sat': 'day-sat', 'sun': 'day-sun'}

# 6 shifts per day
# Shift order for display
SHIFT_ORDER = ['shift1', 'shift2', 'shift3', 'shift4', 'morningsession', 'afternoonsession']

# Conflict key mapping for each shift
SHIFT_CONFLICT = {
    'shift1': 'shift1',
    'shift2': 'shift23',
    'shift3': 'shift23',
    'shift4': 'shift4counters',
    'morningsession': 'morningsession',
    'afternoonsession': 'shift4counters',  # afternoon slot uses same conflict key as shift4
}

SHIFT_LABEL = {
    'shift1': '8:20am - Opening Song (Morning)',
    'shift2': 'Closing Song (Morning) - 12:55pm',
    'shift3': '12:55pm - Opening Song (Afternoon)',
    'shift4': 'Closing Song (Afternoon) - End',
    'morningsession': 'Morning Session',
    'afternoonsession': 'Afternoon Session',
}

# Day-block grouping: a volunteer cannot serve more than one shift per block per day
# Morning block: Shift1, MorningSession, Shift2
# Afternoon block: Shift3, AfternoonSession, Shift4
SHIFT_BLOCK = {
    'shift1': 'morning',
    'shift2': 'morning',
    'morningsession': 'morning',
    'shift3': 'afternoon',
    'shift4': 'afternoon',
    'afternoonsession': 'afternoon',
}

NUM_BOX = 10
NUM_BROTHERS = 2
NUM_COUNTERS = 8
NUM_BOX_FULL = 10      # shifts 1-4: boxes 1-10
NUM_BOX_SESSION = 3     # morning/afternoon session: boxes 8,9,10
NUM_BROTHERS = 2

NUM_COUNTERS = 8

# ── People excluded from ALL duties ──────────────────────────────────────────
EXCLUDED = {'Ruel Ryan Rosal'}  # Account Overseer — no duties

# ── People with restricted assignments ───────────────────────────────────────
RESTRICTED_TO_COUNTERS = {'Jaye Kayla Rosal'}

# ── Special roles (no shift duties, just displayed) ──────────────────────────
SPECIAL_ROLES = {
    'Dale Lao Flores': 'Transport & Messenger',
    'Gomer Dohiling': 'Transport & Messenger',
}

# ── Assignment tracking ──────────────────────────────────────────────────────
all_assignments = {}  # real_name -> [(day, shift_label, role)]


def can_work(real_name, day, conflict_key):
    if real_name in EXCLUDED:
        return False
    if real_name in SPECIAL_ROLES:
        return False  # special role people don't get shift duties
    k = (day, conflict_key)
    if k in conflicts and real_name in conflicts[k]:
        return False
    return True


def assign_shift(day, shift_key, conflict_key, shift_label, pool, count, role, assigned_in_block=None):
    """Assign people from pool not conflicted for this slot.
    Tries multiple random shuffles to find a valid assignment.
    assigned_in_block: set of people already assigned to another shift in the same block today.
    Returns list of chosen real_names."""

    block = SHIFT_BLOCK[shift_key]

    # Build candidate list
    all_candidates = [p for p in pool if can_work(p['real_name'], day, conflict_key)]

    # Exclude restricted people (Jaye Kayla Rosal only goes to counters)
    all_candidates = [p for p in all_candidates if p['real_name'] not in RESTRICTED_TO_COUNTERS]

    # Exclude people already assigned in this block today (no-double-booking)
    if assigned_in_block is not None:
        already_blocked = {rn for rn in assigned_in_block.get((day, block), set())}
        all_candidates = [p for p in all_candidates if p['real_name'] not in already_blocked]

    # Try multiple shuffles to find a good assignment
    best_chosen = []
    for attempt in range(50):
        random.shuffle(all_candidates)
        chosen = []
        for p in all_candidates:
            if len(chosen) >= count:
                break
            rn = p['real_name']
            if rn in chosen:
                continue
            chosen.append(rn)

        if len(chosen) > len(best_chosen):
            best_chosen = chosen

        if len(chosen) == count:
            break

    chosen = best_chosen[:count]

    for rn in chosen:
        all_assignments.setdefault(rn, [])
        all_assignments[rn].append((day, shift_label, role))

    if len(chosen) < count:
        print(f"  WARNING: Only found {len(chosen)}/{count} {role}s for {DAY_LABEL[day]} - {shift_label}")

    return chosen


def assign_counters():
    """Assign 8 counters for Sunday. At least 2 brothers. Jaye Kayla Rosal goes here."""
    # Filter out excluded people
    available = [v for v in volunteers if v['real_name'] not in EXCLUDED and v['real_name'] not in SPECIAL_ROLES]
    
    # Separate brothers and sisters available
    avail_bros = [p for p in available if p['role'] == 'Brother']
    avail_sis = [p for p in available if p['role'] == 'Sister']
    
    selected = []
    
    # Make sure Jaye Kayla Rosal is included
    jaye = [v for v in avail_sis if v['real_name'] == 'Jaye Kayla Rosal']
    if jaye:
        selected.append(jaye[0])
        avail_sis = [v for v in avail_sis if v['real_name'] != 'Jaye Kayla Rosal']
    
    # Pick at least 2 brothers (not more than 4)
    random.shuffle(avail_bros)
    num_bros = min(4, max(2, len(avail_bros)))
    selected.extend(avail_bros[:num_bros])
    
    # Fill the rest with sisters
    remaining = NUM_COUNTERS - len(selected)
    random.shuffle(avail_sis)
    selected.extend(avail_sis[:remaining])
    
    # Trim if we somehow got too many
    selected = selected[:NUM_COUNTERS]
    
    result = [p['real_name'] for p in selected]
    
    for rn in result:
        all_assignments.setdefault(rn, [])
        all_assignments[rn].append(('sun', 'counter', ''))
    
    return result


# ── Run schedule ─────────────────────────────────────────────────────────────
schedule_data = {}

# Track who's already been assigned a shift in each day-block to enforce no-double-booking
assigned_in_block = {}  # (day, 'morning'|'afternoon') -> set of real_names

for day in DAYS:
    for shift in SHIFT_ORDER:
        conflict_key = SHIFT_CONFLICT[shift]
        sl = SHIFT_LABEL[shift]

        bros = assign_shift(day, shift, conflict_key, sl, brothers, NUM_BROTHERS, 'brother', assigned_in_block)

        # Determine box count for this shift
        if shift in ('morningsession', 'afternoonsession'):
            box_count = NUM_BOX_SESSION
        else:
            box_count = NUM_BOX_FULL

        sisses = assign_shift(day, shift, conflict_key, sl, sisters, box_count, 'sister', assigned_in_block)

        # Record assignments in the block tracker to prevent double-booking
        block = SHIFT_BLOCK[shift]
        block_key = (day, block)
        if block_key not in assigned_in_block:
            assigned_in_block[block_key] = set()
        for rn in bros:
            assigned_in_block[block_key].add(rn)
        for rn in sisses:
            assigned_in_block[block_key].add(rn)
        
        schedule_data[(day, sl)] = {
            'brothers': bros,
            'sisters': sisses,
            'is_session': shift in ('morningsession', 'afternoonsession'),
        }
        
        session_label = " [Session - Boxes 8,9,10]" if shift in ('morningsession', 'afternoonsession') else ""
        print(f"\n{DAY_LABEL[day]} - {sl}{session_label}")
        print(f"  Brothers ({len(bros)}): {bros}")
        print(f"  Sisters ({len(sisses)}): {sisses}")

counters = assign_counters()
print(f"\nCounters (Sunday): {counters}")

# Stats
all_person_set = set()
for rn, tasks in all_assignments.items():
    all_person_set.add(rn)
for rn in counters:
    all_person_set.add(rn)

final_brothers = sum(1 for rn in all_person_set if any(b['real_name'] == rn for b in brothers))
final_sisters = sum(1 for rn in all_person_set if any(s['real_name'] == rn for s in sisters))

print(f"\nTotal unique people scheduled: {len(all_person_set)}")
print(f"  Brothers: {final_brothers}, Sisters: {final_sisters}")

# ── Conflict validation ──────────────────────────────────────────────────────
print("\nConflict Validation:")
violations = 0
for rn, tasks in all_assignments.items():
    for day, time, role in tasks:
        if time == 'counter':
            continue
        conflict_key = SHIFT_CONFLICT.get(time, time)
        if time in SHIFT_LABEL.values():
            # Map back from label to key
            for sk, sl in SHIFT_LABEL.items():
                if sl == time:
                    conflict_key = SHIFT_CONFLICT[sk]
                    break
        
        if not can_work(rn, day, conflict_key):
            violations += 1
            print(f"  VIOLATION: {rn} assigned to {DAY_LABEL[day]} - {time} but is conflicted!")

if violations == 0:
    print("  No conflict violations!")
else:
    print(f"  {violations} violations found")

# ── Validate shift requirements ───────────────────────────────────────────────
print("\nShift Requirement Validation:")
req_violations = 0
for (day, time), data in schedule_data.items():
    if len(data['brothers']) != NUM_BROTHERS:
        req_violations += 1
        print(f"  FAIL: {DAY_LABEL[day]} - {time}: {len(data['brothers'])}/{NUM_BROTHERS} Key Brothers")
    expected_boxes = NUM_BOX_SESSION if data['is_session'] else NUM_BOX_FULL
    if len(data['sisters']) != expected_boxes:
        req_violations += 1
        print(f"  FAIL: {DAY_LABEL[day]} - {time}: {len(data['sisters'])}/{expected_boxes} Box Attendants")

if req_violations == 0:
    print("  All shifts have correct staff counts!")
else:
    print(f"  {req_violations} requirement violations found")

# ── Generate HTML ────────────────────────────────────────────────────────────
def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def tag(name, role):
    cls = 'brother-tag' if role == 'Brother' else 'sister-tag'
    return '<span class="name-tag ' + cls + '">' + esc(name) + '</span>'

def box_row(n, name):
    return '<div class="box-row"><span class="box-num">Box ' + str(n) + '</span><span class="box-name">' + esc(name) + '</span></div>'

def shift_card(time, bros, sisses, is_session=False):
    h = '<div class="shift-card">\n'
    h += '<div class="shift-header"><span class="shift-time">' + esc(time) + '</span></div>\n'
    h += '<div class="shift-body">\n'
    h += '<div class="section-mini"><h4>Key Brothers</h4>\n<div class="name-list">'
    for n in bros:
        h += tag(n, 'Brother')
    h += '</div></div>\n'
    h += '<div class="section-mini"><h4>Box Attendants</h4>\n<div class="box-grid">\n'
    if is_session:
        # Session shifts: only boxes 8,9,10
        for i, n in enumerate(sisses):
            h += box_row(i + 8, n)  # Box 8, 9, 10
    else:
        # Regular shifts: boxes 1-10
        for i, n in enumerate(sisses):
            h += box_row(i + 1, n)
    h += '</div></div>\n</div>\n</div>\n'
    return h

def counters_block(names):
    h = '<div class="counters-section">\n'
    h += '<h2 class="section-title">Counters — Sunday, July 12</h2>\n'
    h += '<p class="section-desc">Count after afternoon session ends</p>\n'
    h += '<div class="name-list">'
    for n in names:
        role = 'Brother' if any(b['real_name'] == n for b in brothers) else 'Sister'
        h += tag(n, role)
    h += '</div>\n</div>\n'
    return h

def special_roles_block():
    """Render the special roles section (Dale Lao Flores, Gomer Dohiling)."""
    h = '<div class="special-roles-section">\n'
    h += '<h2 class="section-title">Special Roles</h2>\n'
    h += '<p class="section-desc">These volunteers serve in non-shift capacities</p>\n'
    h += '<div class="special-roles-grid">\n'
    for name, role_desc in SPECIAL_ROLES.items():
        # Determine if they're in volunteers list for role tag color
        v = next((x for x in volunteers if x['real_name'] == name), None)
        role = v['role'] if v else 'Brother'
        h += '<div class="special-role-item">'
        h += tag(name, role)
        h += ' <span class="special-role-desc">— ' + esc(role_desc) + '</span>'
        h += '</div>\n'
    h += '</div>\n</div>\n'
    return h

def search_rows():
    rows = []
    person_tasks = dict(all_assignments)
    for rn in counters:
        if rn not in person_tasks:
            person_tasks[rn] = []
        person_tasks[rn].append(('sun', 'counter', ''))
    
    sorted_people = sorted(person_tasks.items(),
        key=lambda x: (0 if any(b['real_name'] == x[0] for b in brothers) else 1, x[0]))
    
    for rn, tasks in sorted_people:
        role = 'Brother' if any(b['real_name'] == rn for b in brothers) else 'Sister'
        parts = []
        for day, time, _ in tasks:
            if time == 'counter':
                parts.append('Sunday - Counter')
            else:
                dl = {'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday'}[day]
                r = 'Key Brother' if role == 'Brother' else 'Box'
                parts.append(dl + ' - ' + r + ' (' + time + ')')
        rows.append('<tr class="search-row"><td class="search-name">' + esc(rn) +
                    '</td><td class="search-role">' + role +
                    '</td><td class="search-assign">' + esc('; '.join(parts)) + '</td></tr>')
    return '\n'.join(rows)


# Keep existing CSS from the file
with open('/tmp/accountsDepartment-schedule/index.html', 'r', encoding='utf-8') as f:
    existing = f.read()

s = existing.find('<style>')
e = existing.find('</style>') + len('</style>')
css = existing[s:e]

# Inject special roles CSS
extra_css = """
.special-roles-section {
    background: #fff; border-radius: 10px; padding: 18px 20px;
    margin-top: 10px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.special-roles-grid { display: flex; flex-wrap: wrap; gap: 10px; }
.special-role-item { display: flex; align-items: center; gap: 6px; }
.special-role-desc { color: #888; font-size: 0.85em; font-style: italic; }
"""
css = css.replace('</style>', extra_css + '</style>')

# Build HTML
parts = []
parts.append('<!DOCTYPE html>')
parts.append('<html lang="en">')
parts.append('<head>')
parts.append('<meta charset="UTF-8">')
parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
parts.append('<title>Accounts Department Volunteers — July 10-12, 2026</title>')
parts.append(css)
parts.append('</head>')
parts.append('<body>')
parts.append('<div class="container">')

parts.append('<header>')
parts.append('    <h1>Accounts Department Volunteers</h1>')
parts.append('    <div class="subtitle">July 10\u201312, 2026 \u2022 Three-Day Program</div>')
parts.append('    <div class="badge">' + str(final_brothers) + ' Brothers \u2022 ' + str(final_sisters) + ' Sisters</div>')
parts.append('</header>')

parts.append('<nav class="nav-bar" role="tablist">')
parts.append('<button class="tab-btn tab-active" role="tab" aria-selected="true" onclick="showDay(\'fri\')">Friday<br><small>July 10, 2026</small></button>')
parts.append('<button class="tab-btn " role="tab" aria-selected="false" onclick="showDay(\'sat\')">Saturday<br><small>July 11, 2026</small></button>')
parts.append('<button class="tab-btn " role="tab" aria-selected="false" onclick="showDay(\'sun\')">Sunday<br><small>July 12, 2026</small></button>')
parts.append('</nav>')

for day in DAYS:
    disp = 'block' if day == 'fri' else 'none'
    parts.append('<div id="' + DAY_PANEL[day] + '" class="day-panel" role="tabpanel" style="display: ' + disp + '">')
    parts.append('<h2 class="day-title">' + DAY_LABEL[day] + ' — ' + DAY_DATE[day] + '</h2>')
    for shift in SHIFT_ORDER:
        sl = SHIFT_LABEL[shift]
        key = (day, sl)
        if key in schedule_data:
            data = schedule_data[key]
            parts.append(shift_card(sl, data['brothers'], data['sisters'], data['is_session']))
    parts.append('</div>')

parts.append(counters_block(counters))

parts.append(special_roles_block())

parts.append('<div class="search-section">')
parts.append('    <h2 class="section-title">Search Volunteer Schedule</h2>')
parts.append('    <input type="text" id="searchInput" onkeyup="searchNames()" placeholder="Type a name to search..." autocomplete="off">')
parts.append('    <div style="max-height: 400px; overflow-y: auto;">')
parts.append('    <table class="search-table" id="searchTable">')
parts.append('        <thead><tr><th>Name</th><th>Role</th><th>Assignments</th></tr></thead>')
parts.append('        <tbody>')
parts.append(search_rows())
parts.append('        </tbody>')
parts.append('    </table>')
parts.append('    </div>')
parts.append('</div>')

parts.append('<footer>Generated with conflict checking enabled</footer>')
parts.append('</div>')
parts.append('<script>')
parts.append('function showDay(day) {')
parts.append('    document.querySelectorAll(".day-panel").forEach(p => p.style.display = "none");')
parts.append('    document.querySelectorAll(".tab-btn").forEach(b => {')
parts.append('        b.classList.remove("tab-active");')
parts.append('        b.setAttribute("aria-selected", "false");')
parts.append('    });')
parts.append('    document.getElementById("day-" + day).style.display = "block";')
parts.append('    event.currentTarget.classList.add("tab-active");')
parts.append('    event.currentTarget.setAttribute("aria-selected", "true");')
parts.append('}')
parts.append('function searchNames() {')
parts.append('    const input = document.getElementById("searchInput");')
parts.append('    const filter = input.value.toUpperCase();')
parts.append('    const rows = document.querySelectorAll(".search-row");')
parts.append('    rows.forEach(row => {')
parts.append('        const name = row.querySelector(".search-name").textContent.toUpperCase();')
parts.append('        row.style.display = name.includes(filter) ? "" : "none";')
parts.append('    });')
parts.append('}')
parts.append('</script>')
parts.append('</body>')
parts.append('</html>')

final_html = '\n'.join(parts)

with open('/tmp/accountsDepartment-schedule/index.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("\nDone! HTML saved to /tmp/accountsDepartment-schedule/index.html")
print("Size: " + str(len(final_html)) + " bytes")
