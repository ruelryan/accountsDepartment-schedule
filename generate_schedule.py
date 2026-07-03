#!/usr/bin/env python3
"""
Generate Accounts Department volunteer schedule HTML with conflict checking.
Reads volunteer list and conflict data from CSVs, maps messenger names to real names,
and produces the schedule HTML with conflicts properly enforced.

6 shifts per day x 3 days = 18 shifts:
  shift1, shift2, shift3, shift4  -- 10 boxes (1-10) + 2 key brothers
  morningsession, afternoonsession -- 3 boxes (8,9,10) + 2 key brothers

Constraint: no person serves back-to-back overlapping shifts in a single day.
Shift timeline: shift1 -> morningsession -> shift2 -> shift3 -> afternoonsession -> shift4
Consecutive shifts in this order OVERLAP and cannot be done by the same person.
Ideal: 1 shift per day. Fallback: 2 non-overlapping shifts (any two non-consecutive).
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
    # Morning session columns
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
                continue

            day, shift_key = COL_NAMES[col_idx]
            real = messenger_to_real.get(name, name)

            if day == 'jedloyd':
                # Jedloyd column: these names can't work ANY shift where Jedloyd is scheduled
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

# Timeline order for overlap detection
# Consecutive entries in this list OVERLAP (back-to-back)
SHIFT_TIMELINE = ['shift1', 'morningsession', 'shift2', 'shift3', 'afternoonsession', 'shift4']

# Timeline index for each shift — used for overlap detection
TIMELINE_INDEX = {s: i for i, s in enumerate(SHIFT_TIMELINE)}

SHIFT_CONFLICT = {
    'shift1': 'shift1',
    'shift2': 'shift23',
    'shift3': 'shift23',
    'shift4': 'shift4counters',
    'morningsession': 'morningsession',
    'afternoonsession': 'morningsession',  # afternoon session uses morning session conflict key
}

SHIFT_LABEL = {
    'shift1': '8:20am - Opening Song (Morning)',
    'shift2': 'Closing Song (Morning) - 12:55pm',
    'shift3': '12:55pm - Opening Song (Afternoon)',
    'shift4': 'Closing Song (Afternoon) - End',
    'morningsession': 'Morning Session',
    'afternoonsession': 'Afternoon Session',
}

NUM_BOX = 10
NUM_BROTHERS = 2
NUM_COUNTERS = 8
NUM_BOX_FULL = 10      # shifts 1-4: boxes 1-10
NUM_BOX_SESSION = 3     # morning/afternoon session: boxes 8,9,10

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
all_assignments = {}  # real_name -> [(day, shift_label, role, role_category)]

# Track what role_category each person has had each day, for role rotation
# role_history[real_name] = {day: set_of_role_categories}
role_history = {}


def get_role_category(shift_key, pool_role):
    """Return the role category for a shift assignment.
    
    Sisters fill 'box' roles in shifts and 'counter' for counters.
    Brothers fill 'brother' roles in shifts and 'counter' for counters.
    This lets us rotate: box -> brother -> counter across days.
    """
    if pool_role == 'brother':
        return 'brother'
    elif pool_role == 'sister':
        if shift_key in ('morningsession', 'afternoonsession'):
            return 'sister'
        return 'sister'
    return pool_role


def can_work(real_name, day, conflict_key):
    if real_name in EXCLUDED:
        return False
    if real_name in SPECIAL_ROLES:
        return False
    k = (day, conflict_key)
    if k in conflicts and real_name in conflicts[k]:
        return False
    return True


def shifts_overlap(shift_key_a, shift_key_b):
    """Check if two shifts are consecutive in the timeline (and thus overlap)."""
    if shift_key_a not in TIMELINE_INDEX or shift_key_b not in TIMELINE_INDEX:
        return False
    return abs(TIMELINE_INDEX[shift_key_a] - TIMELINE_INDEX[shift_key_b]) <= 1


def role_variety_score(rn, day, new_role_cat, role_history):
    """Score how much variety a candidate would get by taking this role.
    
    Returns higher scores for roles the person hasn't done yet across all days.
    If they've never done this role: +2 (good variety).
    If they've done this role on this day already: -2 (bad variety).
    If they've done this role on another day: -1 (some variety but repeat).
    """
    hist = role_history.get(rn, {})
    score = 0
    
    # How many different roles has this person had so far?
    roles_done = set()
    for d, cats in hist.items():
        roles_done.update(cats)
    
    if new_role_cat not in roles_done:
        score += 2  # New role type = excellent variety
    elif hist.get(day) and new_role_cat in hist[day]:
        score -= 2  # Already doing this role today = bad
    else:
        score -= 1  # Done this role on another day = some variety
    
    return score


def assign_shift(day, shift_key, conflict_key, shift_label, pool, count, role,
                 assigned_per_day=None, prefer_saving_key=None):
    """Assign people from pool not conflicted for this slot.
    
    assigned_per_day: dict mapping day -> {real_name: [shift_keys]} tracking
                      all assignments per person per day.
    A person can be in at most 1 shift per day (ideal), but if we can't fill all
    slots, a 2nd non-overlapping shift is allowed.
    
    prefer_saving_key: if set, prefer candidates NOT in this conflict key
                       (to save them for another shift).
    
    ROLE ROTATION: prefer candidates whose previous role categories differ from
    this one, giving volunteers variety across days.
    
    Returns list of chosen real_names.
    """
    # Build candidate list from all eligible pool members
    all_candidates = [p for p in pool if can_work(p['real_name'], day, conflict_key)]

    # Exclude restricted people (Jaye Kayla Rosal only goes to counters)
    all_candidates = [p for p in all_candidates if p['real_name'] not in RESTRICTED_TO_COUNTERS]

    # ── Per-day assignment check ─────────────────────────────────────────────
    # A person can only serve in shifts that don't overlap with their existing
    # same-day assignments.
    filtered = []
    for p in all_candidates:
        rn = p['real_name']
        existing = assigned_per_day.get((day, rn), []) if assigned_per_day else []
        if not existing:
            # No assignments yet today — always eligible
            filtered.append(p)
        elif len(existing) == 1:
            # Has 1 shift — allow only if this new shift doesn't overlap
            if not shifts_overlap(existing[0], shift_key):
                filtered.append(p)
        # 2+ shifts already today — not eligible (max 2)
    
    all_candidates = filtered

    # ── Role rotation category for this shift ────────────────────────────────
    # Sisters in shifts = Box Attendants. Brothers in shifts = Key Brothers.
    # Both can be Counters on Sunday.
    if role == 'brother':
        this_role_cat = 'brother'  # Key Brother
    else:
        this_role_cat = 'box'  # Box Attendant

    # Try multiple shuffles to find a good assignment
    best_chosen = []
    best_variety = -999
    for attempt in range(300):
        random.shuffle(all_candidates)
        
        candidates = list(all_candidates)
        if prefer_saving_key:
            saved_key = (day, prefer_saving_key)
            saved_set = conflicts.get(saved_key, set())
            # Sort: people NOT in saved_key first
            candidates.sort(key=lambda p: p['real_name'] in saved_set)
        
        chosen = []
        for p in candidates:
            if len(chosen) >= count:
                break
            rn = p['real_name']
            if rn in chosen:
                continue
            chosen.append(rn)

        # Score this assignment for role variety
        variety = 0
        for rn in chosen:
            variety += role_variety_score(rn, day, this_role_cat, role_history)
        
        if len(chosen) > len(best_chosen) or (
            len(chosen) == len(best_chosen) and variety > best_variety
        ):
            best_chosen = chosen
            best_variety = variety

        if len(chosen) == count and variety >= 0:
            # Found a full assignment with good variety
            break

    chosen = best_chosen[:count]

    # Record in role_history
    for rn in chosen:
        if rn not in role_history:
            role_history[rn] = {}
        if day not in role_history[rn]:
            role_history[rn][day] = set()
        role_history[rn][day].add(this_role_cat)

    for rn in chosen:
        all_assignments.setdefault(rn, [])
        all_assignments[rn].append((day, shift_label, role, this_role_cat))

    if len(chosen) < count:
        print(f"  WARNING: Only found {len(chosen)}/{count} {role}s for {DAY_LABEL[day]} - {shift_label}")

    return chosen


def assign_counters(day, assigned_per_day):
    """Assign 8 counters for Sunday. At least 2 brothers. Jaye Kayla Rosal goes here.
    Respects per-day assignment limits (excludes overlap via the 2-shift rule).
    
    ROLE ROTATION: Prefer volunteers whose previous roles differ from 'counter',
    so people who have been Box Attendants or Key Brothers get a chance to count.
    """
    available = [v for v in volunteers if v['real_name'] not in EXCLUDED and v['real_name'] not in SPECIAL_ROLES]
    
    # Filter by per-day non-overlap rule
    filtered = []
    for p in available:
        rn = p['real_name']
        existing = assigned_per_day.get((day, rn), [])
        # Counters don't have a shift_key in the same timeline, but they're
        # in the afternoon block. They overlap with shift3, afternoonsession, shift4.
        # So: if someone is already in shift3, afternoonsession, or shift4, they can't be a counter.
        overlapping_shifts = {'shift3', 'afternoonsession', 'shift4'}
        if existing:
            has_overlap = any(s in overlapping_shifts for s in existing)
            if len(existing) >= 2 or has_overlap:
                # Already has 2 shifts OR already in an overlapping afternoon shift
                continue
        filtered.append(p)
    available = filtered

    # Separate brothers and sisters
    avail_bros = [p for p in available if p['role'] == 'Brother']
    avail_sis = [p for p in available if p['role'] == 'Sister']
    
    # ── Role variety scoring for counters ─────────────────────────────────────
    # 'counter' is a role category distinct from 'box' and 'brother'
    # Score each candidate by how much variety being a counter gives them
    
    def counter_variety_score(person):
        rn = person['real_name']
        hist = role_history.get(rn, {})
        roles_done = set()
        for d, cats in hist.items():
            roles_done.update(cats)
        if 'counter' not in roles_done:
            return 2  # New role type!
        elif hist.get(day) and 'counter' in hist[day]:
            return -2  # Already a counter today
        else:
            return -1  # Been a counter before on another day
    
    selected = []
    
    # Make sure Jaye Kayla Rosal is included
    jaye = [v for v in avail_sis if v['real_name'] == 'Jaye Kayla Rosal']
    if jaye:
        selected.append(jaye[0])
        avail_sis = [v for v in avail_sis if v['real_name'] != 'Jaye Kayla Rosal']
    
    # Pick at least 2 brothers — prefer those with variety (not already counters)
    avail_bros.sort(key=counter_variety_score, reverse=True)
    num_bros = min(4, max(2, len(avail_bros)))
    selected.extend(avail_bros[:num_bros])
    
    # Fill the rest with sisters — prefer those with variety
    avail_sis.sort(key=counter_variety_score, reverse=True)
    remaining = NUM_COUNTERS - len(selected)
    selected.extend(avail_sis[:remaining])
    
    # Trim if we somehow got too many
    selected = selected[:NUM_COUNTERS]
    
    result = [p['real_name'] for p in selected]
    
    # Record in role_history
    for rn in result:
        if rn not in role_history:
            role_history[rn] = {}
        if day not in role_history[rn]:
            role_history[rn][day] = set()
        role_history[rn][day].add('counter')
    
    for rn in result:
        all_assignments.setdefault(rn, [])
        all_assignments[rn].append(('sun', 'counter', '', 'counter'))
    
    # Track counters in assigned_per_day
    for rn in result:
        key = (day, rn)
        if key not in assigned_per_day:
            assigned_per_day[key] = []
        assigned_per_day[key].append('counter')
    
    return result


# ── Helper: compute pool availability per shift ──────────────────────────────
def compute_pool_sizes():
    """Compute how many sisters are available for each shift (after conflicts)."""
    sizes = {}
    for day in DAYS:
        for shift in SHIFT_TIMELINE:
            conflict_key = SHIFT_CONFLICT[shift]
            k = (day, conflict_key)
            conflicted = conflicts.get(k, set())
            available = [s['real_name'] for s in sisters if s['real_name'] not in conflicted]
            sizes[(day, shift)] = len(available)
    return sizes

pool_sizes = compute_pool_sizes()

# ── Run schedule ─────────────────────────────────────────────────────────────
schedule_data = {}
counters = []

# Track per-person per-day assignments: (day, real_name) -> [shift_key1, shift_key2]
assigned_per_day = {}

for day in DAYS:
    # Determine assignment order: scarce shifts first (smaller pool = more constrained)
    shift_order = sorted(SHIFT_TIMELINE, key=lambda s: pool_sizes.get((day, s), 999))
    
    # For Sunday, ensure shift4 (which uses scarce shift4counters pool) goes very early
    # But keep timeline order for priority hints within same scarcity
    print(f"\n=== {DAY_LABEL[day]} — assignment order by scarcity: {shift_order} ===")
    
    for shift in shift_order:
        conflict_key = SHIFT_CONFLICT[shift]
        sl = SHIFT_LABEL[shift]

        # Preference hint: save people for other scarce shifts
        save_hint = None
        # When assigning shift3 on Sunday, try to save shift4counters-available people
        if shift == 'shift3':
            # Find which shifts are most scarce to save for
            scares = [(s, pool_sizes.get((day, s), 999)) for s in SHIFT_TIMELINE if s != shift]
            scares.sort(key=lambda x: x[1])
            if scares:
                most_scarce = scares[0][0]
                save_hint = SHIFT_CONFLICT[most_scarce]

        bros = assign_shift(day, shift, conflict_key, sl, brothers, NUM_BROTHERS,
                            'brother', assigned_per_day, prefer_saving_key=save_hint)

        if shift in ('morningsession', 'afternoonsession'):
            box_count = NUM_BOX_SESSION
        else:
            box_count = NUM_BOX_FULL

        # For sisters, also provide saving hints
        sisters_save_hint = save_hint
        sisses = assign_shift(day, shift, conflict_key, sl, sisters, box_count,
                              'sister', assigned_per_day, prefer_saving_key=sisters_save_hint)

        # Record assignments in per-day tracker
        for rn in bros:
            key = (day, rn)
            if key not in assigned_per_day:
                assigned_per_day[key] = []
            assigned_per_day[key].append(shift)
        for rn in sisses:
            key = (day, rn)
            if key not in assigned_per_day:
                assigned_per_day[key] = []
            assigned_per_day[key].append(shift)
        
        schedule_data[(day, sl)] = {
            'brothers': bros,
            'sisters': sisses,
            'is_session': shift in ('morningsession', 'afternoonsession'),
        }
        
        session_label = " [Session - Boxes 8,9,10]" if shift in ('morningsession', 'afternoonsession') else ""
        print(f"\n{DAY_LABEL[day]} - {sl}{session_label}")
        print(f"  Brothers ({len(bros)}): {bros}")
        print(f"  Sisters ({len(sisses)}): {sisses}")

    if day == 'sun':
        counters = assign_counters(day, assigned_per_day)
        print(f"\nCounters (Sunday): {counters}")

# Stats
all_person_set = set()
for rn, tasks in all_assignments.items():
    all_person_set.add(rn)
for rn in counters:
    all_person_set.add(rn)

final_brothers = sum(1 for rn in all_person_set if any(b['real_name'] == rn for b in brothers))
final_sisters = sum(1 for rn in all_person_set if any(s['real_name'] == rn for s in sisters))

print(f"Total unique people scheduled: {len(all_person_set)}")
print(f"  Brothers: {final_brothers}, Sisters: {final_sisters}")

# ── Role variety report ──────────────────────────────────────────────────────
print(f"\nRole Variety Report:")
# Build an aggregate view: person -> {(day, role_category)}
person_roles = {}
for rn, tasks in all_assignments.items():
    for entry in tasks:
        if len(entry) >= 4:
            day, shift_label, role, role_cat = entry
        else:
            day, shift_label, role = entry
            role_cat = role  # fallback
        if rn not in person_roles:
            person_roles[rn] = {}
        if day not in person_roles[rn]:
            person_roles[rn][day] = set()
        person_roles[rn][day].add(role_cat)

# Check role_history includes counters
for rn in counters:
    if rn not in person_roles:
        person_roles[rn] = {}
    if 'sun' not in person_roles[rn]:
        person_roles[rn]['sun'] = set()
    person_roles[rn]['sun'].add('counter')

multi_role = 0
single_role = 0
for rn, days in sorted(person_roles.items()):
    all_roles = set()
    for d, cats in days.items():
        all_roles.update(cats)
    role_list = ', '.join(sorted(all_roles))
    if len(all_roles) >= 2:
        multi_role += 1
        print(f"  ✓ {rn}: {len(all_roles)} roles [{role_list}]")
    else:
        single_role += 1
        print(f"  · {rn}: 1 role [{role_list}]")

total_with_roles = multi_role + single_role
if total_with_roles:
    print(f"  Variety: {multi_role}/{total_with_roles} people have 2+ roles ({100*multi_role//total_with_roles}%)")

# ── Conflict validation ──────────────────────────────────────────────────────
print("\nConflict Validation:")
violations = 0
for rn, tasks in all_assignments.items():
    for entry in tasks:
        if len(entry) == 4:
            day, time, role, role_cat = entry
        else:
            day, time, role = entry
        if time == 'counter':
            continue
        conflict_key = SHIFT_CONFLICT.get(time, time)
        if time in SHIFT_LABEL.values():
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

# ── Overlap validation (per-day, no consecutive shifts) ────────────────────
print("\nOverlap Validation (no back-to-back shifts per day):")
overlap_violations = 0
# Build per-person per-day shift list
day_assignments = {}  # (day, rn) -> [(shift_key, shift_label)]
for rn, tasks in all_assignments.items():
    for entry in tasks:
        if len(entry) == 4:
            day, time, role, role_cat = entry
        else:
            day, time, role = entry
        if time == 'counter':
            continue
        # Map label back to shift key
        shift_key = None
        for sk, sl in SHIFT_LABEL.items():
            if sl == time:
                shift_key = sk
                break
        if shift_key is None:
            continue
        key = (day, rn)
        if key not in day_assignments:
            day_assignments[key] = []
        day_assignments[key].append((shift_key, time))

for (day, rn), shifts in sorted(day_assignments.items()):
    if len(shifts) <= 1:
        continue
    # Check all pairs for overlap
    sorted_shifts = sorted(shifts, key=lambda x: TIMELINE_INDEX.get(x[0], 999))
    for i in range(len(sorted_shifts) - 1):
        sk_a, sl_a = sorted_shifts[i]
        sk_b, sl_b = sorted_shifts[i + 1]
        if shifts_overlap(sk_a, sk_b):
            overlap_violations += 1
            print(f"  VIOLATION: {rn} has overlapping shifts in {DAY_LABEL[day]}: "
                  f"'{sl_a}' and '{sl_b}' are consecutive")
    if len(shifts) > 2:
        overlap_violations += 1
        print(f"  VIOLATION: {rn} has {len(shifts)} shifts in {DAY_LABEL[day]}: {[s[1] for s in shifts]}")

if overlap_violations == 0:
    print("  No overlap violations!")
else:
    print(f"  {overlap_violations} overlap violations found")

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

def box_row(n, name, role):
    cls = 'brother-tag' if role == 'Brother' else 'sister-tag'
    return '<div class="box-row"><span class="box-num">Box ' + str(n) + '</span><span class="box-name name-tag ' + cls + '">' + esc(name) + '</span></div>'

def shift_card(time, bros, sisses, is_session=False):
    """Generate a shift card with all names as data attributes for filtering."""
    # Collect all names in this shift for searching
    all_names = list(bros) + list(sisses)
    data_names = ' '.join(esc(n).lower() for n in all_names)
    
    h = '<div class="shift-card" data-names="' + data_names + '">\n'
    h += '<div class="shift-header"><span class="shift-time">' + esc(time) + '</span></div>\n'
    h += '<div class="shift-body">\n'
    h += '<div class="section-mini"><h4>Key Brothers</h4>\n<div class="name-list">'
    for n in bros:
        h += tag(n, 'Brother')
    h += '</div></div>\n'
    h += '<div class="section-mini"><h4>Box Attendants</h4>\n<div class="box-grid">\n'
    if is_session:
        for i, n in enumerate(sisses):
            h += box_row(i + 8, n)  # Box 8, 9, 10
    else:
        for i, n in enumerate(sisses):
            h += box_row(i + 1, n)
    h += '</div></div>\n</div>\n</div>\n'
    return h

def counters_block(names):
    """Counters section with data attributes for searching."""
    all_names = ' '.join(esc(n).lower() for n in names)
    h = '<div class="counters-section" data-names="' + all_names + '">\n'
    h += '<h2 class="section-title">Counters \u2014 Sunday, July 12</h2>\n'
    h += '<p class="section-desc">Count after afternoon session ends</p>\n'
    h += '<div class="name-list">'
    for n in names:
        role = 'Brother' if any(b['real_name'] == n for b in brothers) else 'Sister'
        h += tag(n, role)
    h += '</div>\n</div>\n'
    return h

def special_roles_block():
    all_names = ' '.join(esc(n).lower() for n in SPECIAL_ROLES)
    h = '<div class="special-roles-section" data-names="' + all_names + '">\n'
    h += '<h2 class="section-title">Special Roles</h2>\n'
    h += '<p class="section-desc">These volunteers serve in non-shift capacities</p>\n'
    h += '<div class="special-roles-grid">\n'
    for name, role_desc in SPECIAL_ROLES.items():
        v = next((x for x in volunteers if x['real_name'] == name), None)
        role = v['role'] if v else 'Brother'
        h += '<div class="special-role-item">'
        h += tag(name, role)
        h += ' <span class="special-role-desc">\u2014 ' + esc(role_desc) + '</span>'
        h += '</div>\n'
    h += '</div>\n</div>\n'
    return h


# ── Modern, mobile-first CSS ─────────────────────────────────────────────────
CSS = """<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html { font-size: 16px; -webkit-text-size-adjust: 100%; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #f0f2f5;
    color: #1a1a2e;
    line-height: 1.5;
}
.container { max-width: 960px; margin: 0 auto; padding: 12px; }

/* ── Header ── */
header {
    background: linear-gradient(135deg, #0f1b2d 0%, #1b2a4a 50%, #0d1a33 100%);
    color: #fff; padding: 24px 16px; text-align: center;
    border-radius: 14px; margin-bottom: 20px;
    box-shadow: 0 4px 24px rgba(15,27,45,0.25);
}
header h1 { font-size: clamp(1.25rem, 5vw, 1.75rem); font-weight: 700; letter-spacing: 0.5px; margin-bottom: 4px; }
header .subtitle { color: #d4a843; font-size: clamp(0.8rem, 3vw, 0.95rem); font-weight: 300; }
header .badge {
    display: inline-block; background: #d4a843; color: #0f1b2d;
    padding: 3px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; margin-top: 8px;
}

/* ── Search Bar ── */
.search-bar {
    background: #fff; border-radius: 14px; padding: 16px 20px;
    margin-bottom: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.search-bar label {
    display: block; font-size: 0.78rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.8px; color: #888; margin-bottom: 8px;
}
.search-input-wrap {
    display: flex; align-items: center; gap: 10px;
    background: #f5f6f8; border: 2px solid #e0e2e6; border-radius: 12px;
    padding: 0 16px; transition: border-color 0.2s, box-shadow 0.2s;
}
.search-input-wrap:focus-within {
    border-color: #1b2a4a; box-shadow: 0 0 0 3px rgba(27,42,74,0.12);
}
.search-input-wrap .icon {
    font-size: 1.1rem; color: #999; flex-shrink: 0;
}
.search-input-wrap input {
    flex: 1; border: none; background: transparent; padding: 14px 0;
    font-size: 1rem; outline: none; color: #1a1a2e;
}
.search-input-wrap input::placeholder { color: #bbb; }
.search-clear {
    display: none; background: none; border: none; color: #999;
    font-size: 1.2rem; cursor: pointer; padding: 4px; line-height: 1;
}
.search-clear.visible { display: block; }
.search-status {
    font-size: 0.82rem; color: #888; margin-top: 8px; min-height: 1.2em;
}
.search-status strong { color: #1b2a4a; }
.search-status .clear-link {
    color: #1b2a4a; text-decoration: underline; cursor: pointer; font-weight: 500; margin-left: 6px;
}

/* ── Tabs ── */
.nav-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.tab-btn {
    flex: 1; padding: 12px 8px;
    background: #e8ecf1; border: none; border-radius: 12px;
    cursor: pointer; font-size: 0.88rem; font-weight: 600;
    color: #666; transition: all 0.2s; text-align: center; line-height: 1.3;
}
.tab-btn small { font-weight: 400; font-size: 0.78rem; color: #999; }
.tab-btn.tab-active { background: #0f1b2d; color: #fff; box-shadow: 0 3px 12px rgba(15,27,45,0.25); }
.tab-btn.tab-active small { color: #d4a843; }
.tab-btn:hover:not(.tab-active) { background: #d5dae3; }

/* ── Day Panels ── */
.day-panel { display: none; }
.day-panel.active { display: block; }
.day-title {
    color: #0f1b2d; font-size: clamp(1.05rem, 4vw, 1.25rem); margin-bottom: 12px;
    padding-bottom: 8px; border-bottom: 3px solid #d4a843;
}

/* ── Shift Cards ── */
.shift-card {
    background: #fff; border-radius: 12px; margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden;
    transition: opacity 0.25s ease, transform 0.25s ease, max-height 0.4s ease;
}
.shift-card.filtered-out {
    opacity: 0; transform: scale(0.95); max-height: 0 !important;
    margin-bottom: 0; overflow: hidden; pointer-events: none;
}
.shift-card.highlighted {
    box-shadow: 0 0 0 3px #d4a843, 0 4px 16px rgba(212,168,67,0.25);
}
.shift-header {
    background: #0f1b2d; color: #fff; padding: 10px 14px;
    font-weight: 600; font-size: 0.9rem;
}
.shift-body {
    padding: 12px 14px;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 12px;
}
@media (max-width: 500px) {
    .shift-body { grid-template-columns: 1fr; gap: 10px; }
}
.section-mini h4 {
    color: #666; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.8px; margin-bottom: 6px; border-bottom: 1px solid #eee; padding-bottom: 4px;
}
.name-list { display: flex; flex-wrap: wrap; gap: 5px; }
.name-tag {
    display: inline-block; padding: 4px 11px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 500; white-space: nowrap;
}
.brother-tag { background: #dce8f5; color: #1a4972; }
.sister-tag { background: #fce8e8; color: #a04040; }

/* ── Box Grid ── */
.box-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 3px; }
@media (max-width: 400px) {
    .box-grid { grid-template-columns: repeat(2, 1fr); }
}
.box-row { display: flex; align-items: center; gap: 6px; padding: 2px 0; font-size: 0.82rem; }
.box-num {
    display: inline-block; background: #d4a843; color: #0f1b2d;
    font-weight: 700; font-size: 0.7rem; padding: 1px 7px;
    border-radius: 8px; min-width: 44px; text-align: center; flex-shrink: 0;
}
.box-name { color: #444; }

/* ── Counters & Special Roles ── */
.counters-section,
.special-roles-section {
    background: #fff; border-radius: 12px; padding: 16px 18px;
    margin-top: 8px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: opacity 0.25s ease, transform 0.25s ease, max-height 0.4s ease;
}
.counters-section.filtered-out,
.special-roles-section.filtered-out {
    opacity: 0; transform: scale(0.95); max-height: 0 !important;
    margin-top: 0; margin-bottom: 0; overflow: hidden; pointer-events: none;
    padding: 0 18px;
}
.counters-section.highlighted,
.special-roles-section.highlighted {
    box-shadow: 0 0 0 3px #d4a843, 0 4px 16px rgba(212,168,67,0.25);
}
.section-title { color: #0f1b2d; font-size: 1.1rem; margin-bottom: 3px; }
.section-desc { color: #999; font-size: 0.8rem; margin-bottom: 10px; }
.special-roles-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.special-role-item { display: flex; align-items: center; gap: 5px; }
.special-role-desc { color: #888; font-size: 0.82rem; font-style: italic; }

/* ── Footer ── */
footer { text-align: center; padding: 16px; color: #bbb; font-size: 0.75rem; }

/* ── Print ── */
@media print {
    body { background: #fff; }
    .container { max-width: 100%; padding: 0; }
    header { background: #0f1b2d !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .tab-btn, .nav-bar, .search-bar, .search-status { display: none; }
    .day-panel { display: block !important; }
    .shift-card { break-inside: avoid; }
    .counters-section, .special-roles-section { break-inside: avoid; }
    .shift-card.filtered-out, .counters-section.filtered-out, .special-roles-section.filtered-out {
        opacity: 1 !important; transform: none !important; max-height: none !important;
        margin: inherit !important; overflow: visible !important; pointer-events: auto !important;
        padding: inherit !important;
    }
}
</style>"""

# ── Generate JS ──────────────────────────────────────────────────────────────
JS = """<script>
function showDay(day) {
    document.querySelectorAll(".day-panel").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(b => {
        b.classList.remove("tab-active");
        b.setAttribute("aria-selected", "false");
    });
    document.getElementById("day-" + day).classList.add("active");
    event.currentTarget.classList.add("tab-active");
    event.currentTarget.setAttribute("aria-selected", "true");
    // Re-run search on day switch to keep filtered state
    searchNames();
}

// Show first day panel by default
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("day-fri").classList.add("active");
});

function searchNames() {
    const input = document.getElementById("searchInput");
    const filter = input.value.trim().toLowerCase();
    const status = document.getElementById("searchStatus");
    const clearBtn = document.getElementById("searchClear");

    // Show/hide clear button
    clearBtn.classList.toggle("visible", filter.length > 0);

    // Target all filterable sections
    const sections = document.querySelectorAll(
        ".shift-card, .counters-section, .special-roles-section"
    );

    if (!filter) {
        // Show everything
        sections.forEach(el => {
            el.classList.remove("filtered-out", "highlighted");
        });
        status.innerHTML = '';
        return;
    }

    let matchCount = 0;
    sections.forEach(el => {
        const names = (el.getAttribute("data-names") || "").toLowerCase();
        if (names.includes(filter)) {
            el.classList.remove("filtered-out");
            el.classList.add("highlighted");
            matchCount++;
        } else {
            el.classList.add("filtered-out");
            el.classList.remove("highlighted");
        }
    });

    if (matchCount > 0) {
        status.innerHTML = 'Showing <strong>' + matchCount + '</strong> section(s) for "<strong>' +
            escHtml(filter) + '</strong>" <span class="clear-link" onclick="clearSearch()">Show all</span>';
    } else {
        status.innerHTML = 'No sections found for "<strong>' +
            escHtml(filter) + '</strong>" <span class="clear-link" onclick="clearSearch()">Clear</span>';
    }
}

function clearSearch() {
    document.getElementById("searchInput").value = '';
    searchNames();
    document.getElementById("searchInput").focus();
}

function escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
</script>"""


# ── Build HTML ────────────────────────────────────────────────────────────────
parts = []
parts.append('<!DOCTYPE html>')
parts.append('<html lang="en">')
parts.append('<head>')
parts.append('<meta charset="UTF-8">')
parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
parts.append('<title>Accounts Department Volunteers &mdash; July 10-12, 2026</title>')
parts.append(CSS)
parts.append('</head>')
parts.append('<body>')
parts.append('<div class="container">')

# ── Header ──
parts.append('<header>')
parts.append('    <h1>Accounts Department Volunteers</h1>')
parts.append('    <div class="subtitle">July 10&ndash;12, 2026 &bull; Three-Day Program</div>')
parts.append('    <div class="badge">' + str(final_brothers) + ' Brothers &bull; ' + str(final_sisters) + ' Sisters</div>')
parts.append('</header>')

# ── Search Bar (prominent, at the top) ──
parts.append('<div class="search-bar">')
parts.append('    <label for="searchInput">Find Your Schedule</label>')
parts.append('    <div class="search-input-wrap">')
parts.append('        <span class="icon">&#x1F50D;</span>')
parts.append('        <input type="text" id="searchInput" oninput="searchNames()" placeholder="Type your name&hellip;" autocomplete="off">')
parts.append('        <button class="search-clear" id="searchClear" onclick="clearSearch()">&times;</button>')
parts.append('    </div>')
parts.append('    <div class="search-status" id="searchStatus"></div>')
parts.append('</div>')

# ── Tab Navigation ──
parts.append('<nav class="nav-bar" role="tablist">')
parts.append('<button class="tab-btn" role="tab" aria-selected="false" onclick="showDay(\'fri\')">Friday<br><small>July 10, 2026</small></button>')
parts.append('<button class="tab-btn" role="tab" aria-selected="false" onclick="showDay(\'sat\')">Saturday<br><small>July 11, 2026</small></button>')
parts.append('<button class="tab-btn" role="tab" aria-selected="false" onclick="showDay(\'sun\')">Sunday<br><small>July 12, 2026</small></button>')
parts.append('</nav>')

# ── Day Panels ──
for day in DAYS:
    parts.append('<div id="' + DAY_PANEL[day] + '" class="day-panel" role="tabpanel">')
    parts.append('<h2 class="day-title">' + DAY_LABEL[day] + ' &mdash; ' + DAY_DATE[day] + '</h2>')
    for shift in SHIFT_TIMELINE:
        sl = SHIFT_LABEL[shift]
        key = (day, sl)
        if key in schedule_data:
            data = schedule_data[key]
            parts.append(shift_card(sl, data['brothers'], data['sisters'], data['is_session']))
    parts.append('</div>')

# ── Counters ──
parts.append(counters_block(counters))

# ── Special Roles ──
parts.append(special_roles_block())

# ── Footer ──
parts.append('<footer>Generated with conflict checking &mdash; Accounts Department</footer>')
parts.append('</div>')
parts.append(JS)
parts.append('</body>')
parts.append('</html>')

final_html = '\n'.join(parts)

with open('/tmp/accountsDepartment-schedule/index.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("\nDone! HTML saved to /tmp/accountsDepartment-schedule/index.html")
print("Size: " + str(len(final_html)) + " bytes")
