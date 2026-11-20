"""CampusFlow Polished — Python + Streamlit, custom interface.
Install: python -m pip install streamlit==1.66.0
Run: python -m streamlit run campusflow_polished.py
Data lives in the current Streamlit session. No database is used.
The custom component uses HTML/CSS/JavaScript; data operations run in Python.
"""
from copy import deepcopy
from datetime import datetime
from collections import Counter
import math
import uuid

SAMPLE = [
    dict(student_id='S101', name='Amina Rahman', major='Computer Science', cgpa=3.75),
    dict(student_id='S102', name='Daniel Smith', major='Cybersecurity', cgpa=3.40),
    dict(student_id='S103', name='Maria Lopez', major='Computer Science', cgpa=3.90),
    dict(student_id='S104', name='John Carter', major='Information Systems', cgpa=3.10),
    dict(student_id='S105', name='Carol', major='Data Science', cgpa=3.65),
]


def find_student(students, student_id):
    # Required linear search: examine the dictionaries one by one, O(n).
    target = str(student_id).strip().upper()
    for student in students:
        if student['student_id'] == target:
            return student
    return None


def validate_record(record):
    clean = {}
    for field in ('student_id', 'name', 'major'):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{field.replace("_", " ").title()} is required.')
        clean[field] = value.strip()
    clean['student_id'] = clean['student_id'].upper()
    value = record.get('cgpa')
    if isinstance(value, bool) or value is None or str(value).strip() == '':
        raise ValueError('CGPA must be a number from 0.00 to 4.00.')
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError('CGPA must be numeric.') from None
    if not math.isfinite(value) or not 0 <= value <= 4:
        raise ValueError('CGPA must be between 0.00 and 4.00.')
    clean['cgpa'] = value
    return clean


def add_student(students, record):
    clean = validate_record(record)
    if find_student(students, clean['student_id']) is not None:
        raise ValueError('This Student ID already exists.')
    students.append(clean)
    return clean


def update_student(students, student_id, record):
    old = find_student(students, student_id)
    if old is None:
        raise ValueError('Student not found.')
    clean = validate_record(record)
    if clean['student_id'] != old['student_id']:
        raise ValueError('Student ID cannot be changed.')
    old.update(clean)
    return old


def delete_student(students, student_id, confirmed=False):
    old = find_student(students, student_id)
    if old is None:
        raise ValueError('Student not found.')
    if confirmed is not True:
        raise ValueError('Confirm deletion first.')
    students.remove(old)
    return old


def new_state():
    return dict(students=deepcopy(SAMPLE), undo=None, history=[], last_event=None,
                message='', error='', toast_id='', ui={
                    'view': 'overview', 'collapsed': False, 'theme': 'light',
                    'id': '', 'name': '', 'major': '', 'minimum': 0,
                    'sort': 'id', 'editor': None, 'draft': {}, 'focus': ''})


def handle_event(state, event):
    """Apply one component request. Failed validation preserves data and Undo."""
    if not isinstance(event, dict) or not isinstance(event.get('id'), str):
        return
    if event['id'] == state['last_event']:
        return
    state['last_event'] = event['id']
    ui = event.get('ui', {})
    if isinstance(ui, dict):
        for field in state['ui']:
            if field in ui:
                state['ui'][field] = deepcopy(ui[field])
    if state['ui']['view'] not in ('overview', 'students', 'analytics'):
        state['ui']['view'] = 'overview'
    if state['ui']['theme'] not in ('light', 'dark'):
        state['ui']['theme'] = 'light'
    state['error'] = ''
    action = event.get('type')
    if action == 'ui':
        return
    try:
        if action == 'undo':
            if state['undo'] is None:
                return
            state['students'] = deepcopy(state['undo'])
            state['undo'] = None
            message = 'Last change undone'
        else:
            candidate = deepcopy(state['students'])
            if action == 'save':
                record = event.get('record', {})
                if not isinstance(record, dict):
                    raise ValueError('Invalid student record.')
                editor = state['ui']['editor']
                if editor == '__new__':
                    student = add_student(candidate, record)
                    message = 'Added ' + student['name']
                elif editor:
                    student = update_student(candidate, editor, record)
                    message = 'Updated ' + student['name']
                else:
                    raise ValueError('Open a student profile first.')
            elif action == 'delete':
                student = delete_student(candidate, event.get('student_id', ''),
                                         event.get('confirmed') is True)
                message = 'Deleted ' + student['name']
            else:
                raise ValueError('Unknown action.')
            state['undo'] = deepcopy(state['students'])
            state['students'] = candidate
        state['ui'].update(editor=None, draft={}, focus='')
        if action == 'save':
            # Ensure that a newly added/edited record is immediately visible.
            state['ui'].update(view='students', id='', name='', major='', minimum=0)
        state['message'] = message
        state['toast_id'] = event['id']
        state['history'].insert(0, f'{datetime.now():%H:%M:%S} · {message}')
        state['history'] = state['history'][:15]
    except (ValueError, TypeError, AttributeError) as error:
        state['error'] = str(error)


def build_payload(state):
    ui = state['ui']
    students = state['students']
    exact = str(ui.get('id', '')).strip()
    match = find_student(students, exact) if exact else None
    source = ([match] if match else []) if exact else students
    try:
        minimum = float(ui.get('minimum', 0))
    except (ValueError, TypeError):
        minimum = 0
    name = str(ui.get('name', '')).strip().casefold()
    major = ui.get('major', '')
    rows = [s.copy() for s in source if name in s['name'].casefold()
            and (not major or s['major'] == major) and s['cgpa'] >= minimum]
    field = {'id': 'student_id', 'name': 'name', 'cgpa': 'cgpa'}.get(ui.get('sort'), 'student_id')
    rows.sort(key=lambda s: s[field].casefold() if field == 'name' else s[field],
              reverse=field == 'cgpa')
    grouped = {}
    for student in rows:
        grouped.setdefault(student['major'], []).append(student['cgpa'])
    groups = [dict(major=m, count=len(v), mean=sum(v)/len(v),
                   minimum=min(v), maximum=max(v), share=len(v)/len(rows)*100)
              for m, v in sorted(grouped.items())]
    counts = Counter(min(int(s['cgpa']), 3) for s in rows)
    selected = find_student(students, ui['editor']) if ui.get('editor') not in (None, '__new__') else None
    return dict(ui=deepcopy(ui), rows=rows, groups=groups,
                total=len(students), count=len(rows),
                average=sum(s['cgpa'] for s in rows)/len(rows) if rows else None,
                majors=sorted({s['major'] for s in students}),
                bins=[counts[i] for i in range(4)], selected=deepcopy(selected),
                undo=state['undo'] is not None, history=state['history'],
                message=state['message'], error=state['error'], toast_id=state['toast_id'])


CSS = r"""

#cf-studio{color-scheme:light dark;--bg:light-dark(#f4f6fb,#101724);--surface:light-dark(#ffffff,#192333);--text:light-dark(#1c2b45,#e9eef8);--muted:light-dark(#62718a,#afbdd1);--border:light-dark(#e0e6ef,#344156);--accent:light-dark(#4c59cf,#a7b1ff);--tint:light-dark(#eef0ff,#2a3353);font:14px/1.5 system-ui;color:var(--text);background:var(--bg);border:1px solid var(--border);border-radius:16px;display:grid;grid-template-columns:224px minmax(0,1fr);position:relative;overflow:hidden}#cf-studio *{box-sizing:border-box}#cf-studio [hidden]{display:none!important}#cf-studio button,#cf-studio input,#cf-studio select{font:inherit;color:var(--text);border:1px solid var(--border);background:var(--surface);border-radius:8px;padding:9px 11px;max-width:100%}#cf-studio button{display:inline-flex;align-items:center;justify-content:center;gap:8px}#cf-studio button:hover{background:var(--tint)}#cf-studio button:disabled{opacity:.45}#cf-studio .primary{background:var(--accent);color:light-dark(#fff,#101724);border-color:var(--accent)}#cf-studio .primary:hover{filter:brightness(.95)}#cf-studio aside{background:var(--surface);border-right:1px solid var(--border);padding:20px 15px;min-width:0}#cf-studio .brand{display:flex;align-items:center;gap:9px;font-size:20px;font-weight:500;margin-bottom:25px}#cf-studio .brand-icon,#cf-studio .avatar{display:inline-flex;align-items:center;justify-content:center;background:var(--tint);color:var(--accent);border-radius:10px;width:34px;height:34px;flex:none}#cf-studio .avatar{border-radius:50%;font-size:12px}#cf-studio .snav{display:flex;flex-direction:column;gap:7px}#cf-studio .snav button{justify-content:flex-start;background:transparent;border:0;width:100%}#cf-studio .snav button.active,#cf-studio .tabs button.active{background:var(--tint);color:var(--accent)}#cf-studio .sfilters{margin-top:28px;border-top:1px solid var(--border);padding-top:18px}#cf-studio .eyebrow,#cf-studio .small{color:var(--muted);font-size:12px}#cf-studio .eyebrow{letter-spacing:1px;font-size:11px}#cf-studio label{display:block;color:var(--muted);font-size:12px;margin:13px 0}#cf-studio label input,#cf-studio label select{display:block;width:100%;margin-top:6px;color:var(--text);font-size:14px;min-width:0}#cf-studio input[type=range]{accent-color:var(--accent);padding:0}#cf-studio main{min-width:0}#cf-studio .topbar{padding:16px 23px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}#cf-studio .top-left,#cf-studio .top-right{display:flex;gap:10px;align-items:center}#cf-studio .topbar button{padding:7px}#cf-studio .content{padding:25px}#cf-studio .heading{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}#cf-studio h2{font-size:26px;letter-spacing:-.8px;margin:0 0 5px;font-weight:500}#cf-studio h3{font-size:14px;margin:0 0 16px;font-weight:500}#cf-studio .tabs{display:flex;gap:7px;border-bottom:1px solid var(--border);padding:18px 0 12px;margin-bottom:20px;flex-wrap:wrap}#cf-studio .tabs button{border:0;background:transparent}#cf-studio .metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:13px;margin-bottom:16px}#cf-studio .panel{border:1px solid var(--border);background:var(--surface);border-radius:12px;padding:18px;min-width:0}#cf-studio .metric strong{display:block;font-size:29px;font-weight:500;margin:9px 0 0;font-variant-numeric:tabular-nums}#cf-studio .charts{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px}#cf-studio .chart-row{margin:13px 0}#cf-studio .chart-label{display:flex;justify-content:space-between;font-size:12px;gap:8px;margin-bottom:6px}#cf-studio .track{height:10px;border-radius:3px;background:var(--tint);overflow:hidden}#cf-studio .fill{height:100%;background:var(--accent);border-radius:3px}#cf-studio .scale{display:flex;justify-content:space-between;margin-top:16px;font-size:11px;color:var(--muted)}#cf-studio .tablehead{display:flex;justify-content:space-between;align-items:center;margin:9px 0 13px}#cf-studio .tablewrap{overflow:auto;border:1px solid var(--border);border-radius:12px;background:var(--surface)}#cf-studio table{width:100%;border-collapse:collapse;min-width:520px;text-align:left}#cf-studio th,#cf-studio td{padding:13px 15px;border-bottom:1px solid var(--border)}#cf-studio th{font-weight:400;color:var(--muted);font-size:12px;background:var(--bg)}#cf-studio tbody tr:last-child td{border-bottom:0}#cf-studio tbody tr:hover{background:var(--tint)}#cf-studio .person{display:flex;align-items:center;gap:9px}#cf-studio .person button{border:0;background:transparent;padding:0;text-align:left;justify-content:flex-start}#cf-studio .badge{background:var(--tint);border-radius:5px;padding:4px 7px;font-size:11px;white-space:nowrap}#cf-studio .foot{margin-top:12px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}#cf-studio .empty{text-align:center;padding:32px 10px}#cf-studio .empty .brand-icon{margin-bottom:10px}#cf-studio .rail-only{display:none}#cf-studio.compact{grid-template-columns:64px minmax(0,1fr)}#cf-studio.compact aside{padding:20px 10px}#cf-studio.compact .side-label,#cf-studio.compact .sfilters{display:none}#cf-studio.compact .brand{justify-content:center}#cf-studio.compact .rail-only{display:flex;margin-top:15px}#cf-studio.compact .snav button{justify-content:center;padding:10px}#cf-studio .drawer{position:absolute;z-index:5;right:0;top:0;width:min(360px,100%);background:var(--surface);border-left:1px solid var(--border);box-shadow:-12px 0 30px #0002;padding:23px;animation:cf-slide .18s ease-out}#cf-studio .drawer-top{display:flex;justify-content:space-between;align-items:center}#cf-studio .profile{display:flex;align-items:center;gap:12px;margin:22px 0}#cf-studio .profile .avatar{width:48px;height:48px;font-size:17px}#cf-studio .drawer-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}#cf-studio .danger{color:light-dark(#ae2841,#ffadb9)}#cf-studio .toast{position:absolute;right:18px;top:76px;z-index:8;background:var(--surface);border:1px solid var(--accent);border-radius:10px;padding:12px 16px;box-shadow:0 6px 20px #0002;max-width:calc(100% - 36px)}#cf-studio .activity{margin-top:16px}#cf-studio .activity li{margin:8px 0;color:var(--muted);font-size:12px}#cf-studio button{transition:background .15s ease}#cf-studio .confirm{padding-top:12px;margin-top:15px;border-top:1px solid var(--border)}@keyframes cf-slide{from{transform:translateX(25px);opacity:.5}to{transform:translateX(0);opacity:1}}@media(prefers-reduced-motion:reduce){#cf-studio *{animation:none!important;transition:none!important}}@media(max-width:780px){#cf-studio{grid-template-columns:180px minmax(0,1fr)}#cf-studio .charts{grid-template-columns:1fr}#cf-studio .content{padding:17px}#cf-studio .metrics{gap:8px}#cf-studio .metric{padding:12px}}@media(max-width:560px){#cf-studio{grid-template-columns:1fr}#cf-studio aside{border-right:0;border-bottom:1px solid var(--border)}#cf-studio .sfilters{display:grid;grid-template-columns:1fr 1fr;gap:8px}#cf-studio .snav{flex-direction:row;flex-wrap:wrap}#cf-studio .snav button{width:auto}#cf-studio .metrics{grid-template-columns:1fr}#cf-studio .topbar{padding:12px}#cf-studio.compact .snav{flex-direction:column}#cf-studio .account-name{display:none}}

#cf-studio button{cursor:pointer}#cf-studio button:disabled{cursor:wait}
#cf-studio #cs-mean-panel{grid-column:1/-1;order:2}#cf-studio #cs-count-panel{order:0}#cf-studio #cs-distribution{order:1}
#cf-studio .histogram{height:150px;display:flex;align-items:flex-end;gap:14px;border-bottom:1px solid var(--border);padding:0 8px}
#cf-studio .hist-col{flex:1;height:100%;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;font-size:12px}
#cf-studio .hist-bar{width:100%;max-width:65px;background:var(--accent);border-radius:4px 4px 0 0}
#cf-studio .hist-labels{display:flex;gap:14px;padding:8px;color:var(--muted);font-size:11px;text-align:center}#cf-studio .hist-labels span{flex:1}
#cf-studio.editing{min-height:760px}#cf-studio .drawer{z-index:10}#cf-studio input:read-only{background:var(--bg)}
#cf-studio .chart-row{cursor:help}#cf-studio .cf-tooltip{position:absolute;z-index:20;pointer-events:none;background:var(--surface);border:1px solid var(--border);padding:8px 10px;border-radius:7px;font-size:12px;max-width:230px;box-shadow:0 4px 15px #0002}
#cf-studio .tablehead{flex-wrap:wrap;gap:10px}#cf-studio .avatar{font-variant-numeric:tabular-nums}
#cf-studio .analysis-info{color:var(--muted);font-size:12px;margin:0 0 16px}#cf-studio .person button:hover{color:var(--accent);text-decoration:underline}

"""


HTML = r"""
<div id="cf-studio">

<aside><div class="brand"><span class="brand-icon"><i data-lucide="graduation-cap" aria-hidden="true"></i></span><span class="side-label">CampusFlow</span></div><div class="snav"><button data-view="overview" class="active cursor-interaction" aria-label="Overview"><i data-lucide="layout-dashboard" aria-hidden="true"></i><span class="side-label">Overview</span></button><button data-view="students" class="cursor-interaction" aria-label="Students"><i data-lucide="users" aria-hidden="true"></i><span class="side-label">Students</span></button><button data-view="analytics" class="cursor-interaction" aria-label="Analytics"><i data-lucide="chart-no-axes-combined" aria-hidden="true"></i><span class="side-label">Analytics</span></button></div><button id="cs-rail-search" class="rail-only cursor-interaction" aria-label="Open search filters"><i data-lucide="search" aria-hidden="true"></i></button><div class="sfilters" id="cs-filters"><div class="eyebrow">SEARCH & FILTERS</div><label>Student ID<input id="cs-id" placeholder="e.g. S101"></label><label>Student name<input id="cs-name" placeholder="Search a name…"></label><label>Major<select id="cs-major"><option value="">All majors</option><option>Computer Science</option><option>Cybersecurity</option><option>Information Systems</option><option>Data Science</option></select></label><label>Minimum CGPA · <output id="cs-min-value">0.00</output><input type="range" id="cs-min" min="0" max="4" step="0.1" value="0"></label><label>Sort by<select id="cs-sort"><option value="id">Student ID</option><option value="name">Name A–Z</option><option value="cgpa">Highest CGPA</option></select></label><button id="cs-reset" class="cursor-interaction">Reset filters</button><div id="cs-filter-count" class="small" aria-live="polite"></div></div></aside>
<main><div class="topbar"><div class="top-left"><button id="cs-toggle" aria-label="Collapse sidebar" aria-expanded="true" aria-controls="cs-filters" class="cursor-interaction"><i data-lucide="panel-left" aria-hidden="true"></i></button><span class="small">Workspace / <span id="cs-breadcrumb">Overview</span></span></div><div class="top-right"><button id="cs-theme" aria-label="Toggle color theme" class="cursor-interaction"><i data-lucide="sun-moon" aria-hidden="true"></i></button><span class="avatar">FB</span><span class="small account-name">Babalola<br>Project demo</span></div></div><div class="content"><div class="heading"><div><h2 id="cs-title">Academic overview</h2><div class="small" id="cs-scope">All students · Sample data</div></div><button id="cs-add" class="primary cursor-interaction"><i data-lucide="plus" aria-hidden="true"></i>Add student</button></div><div class="tabs" aria-label="Dashboard views"><button data-view="overview" aria-pressed="true" class="active cursor-interaction">Overview</button><button data-view="students" aria-pressed="false" class="cursor-interaction">Students</button><button data-view="analytics" aria-pressed="false" class="cursor-interaction">Analytics</button></div><div class="metrics"><div class="panel metric"><span class="small">Students</span><strong id="cs-total">5</strong></div><div class="panel metric"><span class="small">Average CGPA / 4.00</span><strong id="cs-avg">3.56</strong></div><div class="panel metric"><span class="small">Majors represented</span><strong id="cs-majors">4</strong></div></div><div id="cs-empty" class="panel empty" hidden><span class="brand-icon"><i data-lucide="search-x" aria-hidden="true"></i></span><h3>No matching students</h3><p class="small">Try another search or clear your filters.</p><button id="cs-clear" class="cursor-interaction">Clear filters</button></div><div class="charts" id="cs-charts"><section class="panel" id="cs-count-panel"><h3>Students by major</h3><div id="cs-count-chart"></div><div class="scale"><span>0</span><span id="cs-count-max">5 students</span></div></section><section class="panel" id="cs-mean-panel"><h3>Average CGPA by major</h3><div id="cs-mean-chart"></div><div class="scale"><span>0.00</span><span>CGPA / 4.00</span><span>4.00</span></div></section><section class="panel" id="cs-distribution"><h3>CGPA distribution</h3><div id="cs-bins"></div><div class="small">Number of students per CGPA interval</div></section></div><section id="cs-analysis" hidden><h3>Detailed major comparison</h3><p class="analysis-info">Enrollment, share of the filtered group and CGPA range by major.</p><div class="tablewrap"><table><thead><tr><th>Major</th><th>Students</th><th>Share</th><th>Mean CGPA</th><th>Minimum</th><th>Maximum</th></tr></thead><tbody id="cs-analysis-rows"></tbody></table></div></section><section id="cs-records"><div class="tablehead"><h3 style="margin:0">Student directory</h3><button id="cs-undo" disabled class="cursor-interaction"><i data-lucide="undo-2" aria-hidden="true"></i>Undo</button></div><div class="tablewrap"><table><thead><tr><th>Student</th><th>ID</th><th>Major</th><th>CGPA</th></tr></thead><tbody id="cs-rows"></tbody></table></div></section><div class="foot small"><span id="cs-result" aria-live="polite"></span><span>Python + Streamlit · Session data</span></div><details class="panel activity"><summary>Recent activity</summary><ul id="cs-log"><li>No changes yet.</li></ul></details></div></main>
<section class="drawer" id="cs-drawer" aria-label="Student details" hidden><div class="drawer-top"><span class="eyebrow" id="cs-drawer-label">STUDENT PROFILE</span><button id="cs-close" aria-label="Close student profile" class="cursor-interaction"><i data-lucide="x" aria-hidden="true"></i></button></div><div class="profile"><span class="avatar" id="cs-profile-avatar">AR</span><div><h3 id="cs-profile-name" style="margin:0">Amina Rahman</h3><span class="small" id="cs-profile-id">S101</span></div></div><form id="cs-form"><label>Student ID<input name="sid" required></label><label>Full name<input name="fullName" required></label><label>Major<input name="major" required placeholder="Computer Science"></label><label>CGPA<input name="gpa" type="number" min="0" max="4" step="0.01" required></label><div id="cs-error" role="alert" class="danger"></div><div class="drawer-actions"><button type="submit" class="primary cursor-interaction">Save changes</button><button type="button" id="cs-delete" class="danger cursor-interaction">Delete student</button></div></form><div id="cs-confirm" class="confirm" hidden><p id="cs-confirm-message"></p><div class="drawer-actions"><button id="cs-confirm-delete" class="danger cursor-interaction">Confirm deletion</button><button id="cs-keep" class="cursor-interaction">Cancel</button></div></div></section><div id="cs-toast" class="toast" role="status" aria-live="polite" hidden></div>
<div id="cs-tip" class="cf-tooltip" hidden></div></div>
"""


JAVASCRIPT = r"""
export default function(component) {
  const {parentElement, data, setTriggerValue} = component;
  const root = parentElement.querySelector('#cf-studio');
  const q = s => root.querySelector(s);
  const all = s => root.querySelectorAll(s);
  const ui = {...data.ui};
  let timer;
  const initials = s => s.trim().split(/\s+/).map(w=>w[0]).slice(0,2).join('').toUpperCase();
  const icons = {
    'graduation-cap':'<path d="m22 10-10-5L2 10l10 5 10-5v6"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
    'layout-dashboard':'<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    'users':'<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5"/>',
    'chart-no-axes-combined':'<path d="M3 3v18h18M7 14l4-4 4 3 6-8M7 18v-2M11 18v-4M15 18v-2M19 18v-6"/>',
    'search':'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
    'panel-left':'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/>',
    'sun-moon':'<path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9Z"/><path d="M19 3v4M17 5h4"/>',
    'plus':'<path d="M12 5v14M5 12h14"/>',
    'search-x':'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6M8 8l4 4M12 8l-4 4"/>',
    'undo-2':'<path d="M9 14 4 9l5-5M4 9h10a7 7 0 0 1 0 14"/>',
    'x':'<path d="m6 6 12 12M18 6 6 18"/>'
  };
  all('[data-lucide]').forEach(el=>{
    el.innerHTML='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'+(icons[el.dataset.lucide]||'')+'</svg>';
  });
  function readUI() {
    ui.id=q('#cs-id').value;ui.name=q('#cs-name').value;
    ui.major=q('#cs-major').value;ui.minimum=Number(q('#cs-min').value);
    ui.sort=q('#cs-sort').value;
    if(!q('#cs-drawer').hidden) {
      ui.draft={student_id:q('[name=sid]').value,name:q('[name=fullName]').value,
                major:q('[name=major]').value,cgpa:q('[name=gpa]').value};
    }
    return {...ui};
  }
  function send(type, extra={}) {
    clearTimeout(timer);
    const id=Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
    setTriggerValue('action',{id,type,ui:readUI(),...extra});
  }
  function options(select, values, first) {
    select.replaceChildren();
    if(first) {const o=document.createElement('option');o.value='';o.textContent=first;select.append(o);}
    values.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;select.append(o);});
  }
  options(q('#cs-major'), data.majors, 'All majors');
  q('#cs-id').value=ui.id;q('#cs-name').value=ui.name;
  q('#cs-major').value=ui.major;q('#cs-min').value=ui.minimum;
  q('#cs-sort').value=ui.sort;q('#cs-min-value').textContent=Number(ui.minimum).toFixed(2);
  root.style.colorScheme=ui.theme;
  root.classList.toggle('compact',Boolean(ui.collapsed));
  q('#cs-toggle').setAttribute('aria-expanded',String(!ui.collapsed));
  q('#cs-toggle').setAttribute('aria-label',ui.collapsed?'Expand sidebar':'Collapse sidebar');
  q('#cs-theme').setAttribute('aria-label',ui.theme==='light'?'Switch to dark theme':'Switch to light theme');
  function applyView() {
    const view=ui.view;
    q('#cs-title').textContent={overview:'Academic overview',students:'Student directory',analytics:'Academic analytics'}[view];
    q('#cs-breadcrumb').textContent=view[0].toUpperCase()+view.slice(1);
    all('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);b.setAttribute('aria-pressed',String(b.dataset.view===view));});
    q('#cs-charts').hidden=view!=='overview'||!data.count;
    q('#cs-records').hidden=view!=='students'||!data.count;
    q('#cs-analysis').hidden=view!=='analytics'||!data.count;
  }
  applyView();
  q('#cs-empty').hidden=Boolean(data.count);
  q('#cs-total').textContent=data.count;
  q('#cs-avg').textContent=data.average===null?'—':data.average.toFixed(2);
  q('#cs-majors').textContent=data.groups.length;
  q('#cs-filter-count').textContent=data.count+' of '+data.total+' students';
  q('#cs-result').textContent=data.count+' of '+data.total+' students';
  q('#cs-count-max').textContent=data.total+' students';
  q('#cs-scope').textContent=(ui.id||ui.name||ui.major||ui.minimum?'Filtered results':'All students')+' · Session data';
  function bar(target, label, value, fraction, detail) {
    const row=document.createElement('div');row.className='chart-row';
    const caption=document.createElement('div');caption.className='chart-label';
    const a=document.createElement('span'),b=document.createElement('span');
    a.textContent=label;b.textContent=value;caption.append(a,b);
    const track=document.createElement('div');track.className='track';
    const fill=document.createElement('div');fill.className='fill';
    fill.style.width=(fraction*100)+'%';track.append(fill);row.append(caption,track);
    row.addEventListener('pointerenter',e=>showTip(detail,e));
    row.addEventListener('pointermove',e=>showTip(detail,e));
    row.addEventListener('pointerleave',hideTip);
    target.append(row);
  }
  const tip=q('#cs-tip');tip.hidden=true;
  function showTip(text,e){tip.hidden=false;tip.textContent=text;const r=root.getBoundingClientRect();tip.style.left=Math.min(e.clientX-r.left+12,Math.max(0,r.width-235))+'px';tip.style.top=e.clientY-r.top+14+'px';}
  function hideTip(){tip.hidden=true;}
  q('#cs-count-chart').replaceChildren();q('#cs-mean-chart').replaceChildren();
  data.groups.forEach(g=>{
    bar(q('#cs-count-chart'),g.major,String(g.count),g.count/Math.max(1,data.total),g.major+' · '+g.count+' students');
    bar(q('#cs-mean-chart'),g.major,g.mean.toFixed(2),g.mean/4,g.major+' · Mean '+g.mean.toFixed(2)+' / 4 · n='+g.count);
  });
  const hist=q('#cs-bins');hist.replaceChildren();
  const chart=document.createElement('div');chart.className='histogram';
  const max=Math.max(1,...data.bins), binLabels=['0–<1','1–<2','2–<3','3–4'];
  data.bins.forEach((n,i)=>{
    const col=document.createElement('div');col.className='hist-col';
    const value=document.createElement('span');value.textContent=n;
    const fill=document.createElement('div');fill.className='hist-bar';fill.style.height=n/max*120+'px';
    col.append(value,fill);col.addEventListener('pointerenter',e=>showTip(binLabels[i]+' CGPA · '+n+' students',e));col.addEventListener('pointerleave',hideTip);chart.append(col);
  });
  const labels=document.createElement('div');labels.className='hist-labels';
  binLabels.forEach(s=>{const l=document.createElement('span');l.textContent=s;labels.append(l);});
  hist.append(chart,labels);
  q('#cs-analysis-rows').replaceChildren();
  data.groups.forEach(g=>{
    const tr=document.createElement('tr');
    [g.major,g.count,g.share.toFixed(1)+'%',g.mean.toFixed(2),g.minimum.toFixed(2),g.maximum.toFixed(2)].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td);});q('#cs-analysis-rows').append(tr);
  });
  q('#cs-rows').replaceChildren();
  data.rows.forEach(s=>{
    const tr=document.createElement('tr'),td=document.createElement('td'),person=document.createElement('div');person.className='person';
    const avatar=document.createElement('span');avatar.className='avatar';avatar.textContent=initials(s.name);
    const button=document.createElement('button');button.type='button';button.textContent=s.name;button.onclick=()=>openEditor(s);
    person.append(avatar,button);td.append(person);tr.append(td);
    [s.student_id,s.major,s.cgpa.toFixed(2)].forEach((v,i)=>{const cell=document.createElement('td');if(i===1){const badge=document.createElement('span');badge.className='badge';badge.textContent=v;cell.append(badge);}else cell.textContent=v;tr.append(cell);});q('#cs-rows').append(tr);
  });
  q('#cs-log').replaceChildren();
  (data.history.length?data.history:['No changes yet.']).forEach(text=>{const li=document.createElement('li');li.textContent=text;q('#cs-log').append(li);});
  q('#cs-undo').disabled=!data.undo;
  q('#cs-undo').onclick=()=>send('undo');
  function openEditor(student, restored=false){
    ui.editor=student?student.student_id:'__new__';
    const draft=restored&&ui.draft&&Object.keys(ui.draft).length?ui.draft:(student||{student_id:'',name:'',major:'Computer Science',cgpa:''});
    q('#cs-drawer').hidden=false;q('#cs-confirm').hidden=true;q('#cs-error').textContent=restored?data.error:'';
    root.classList.add('editing');
    q('#cs-drawer-label').textContent=student?'STUDENT PROFILE':'NEW STUDENT';
    q('#cs-profile-name').textContent=student?student.name:'Add a student';
    q('#cs-profile-id').textContent=student?student.student_id:'Academic record';
    q('#cs-profile-avatar').textContent=student?initials(student.name):'+';
    q('[name=sid]').value=draft.student_id;q('[name=sid]').readOnly=Boolean(student);
    q('[name=fullName]').value=draft.name;q('[name=major]').value=draft.major;q('[name=gpa]').value=draft.cgpa;
    q('#cs-delete').hidden=!student;
    q('#cs-form [type=submit]').textContent=student?'Save changes':'Save student';
    q('#cs-form [type=submit]').disabled=false;q('#cs-confirm-delete').disabled=false;
    if(!restored) q('[name=fullName]').focus();
  }
  function closeEditor(){readUI();ui.editor=null;ui.draft={};q('#cs-drawer').hidden=true;root.classList.remove('editing');}
  if(ui.editor){openEditor(data.selected,true);}else{q('#cs-drawer').hidden=true;root.classList.remove('editing');}
  q('#cs-add').onclick=()=>{ui.draft={};openEditor(null);};
  q('#cs-close').onclick=closeEditor;
  q('#cs-form').onsubmit=e=>{e.preventDefault();if(!q('#cs-form').reportValidity())return;const draft=readUI().draft;q('#cs-form [type=submit]').disabled=true;send('save',{record:draft});};
  q('#cs-delete').onclick=()=>{q('#cs-confirm-message').textContent='Delete '+ui.editor+'? You can undo this change.';q('#cs-confirm').hidden=false;};
  q('#cs-keep').onclick=()=>{q('#cs-confirm').hidden=true;};
  q('#cs-confirm-delete').onclick=()=>{q('#cs-confirm-delete').disabled=true;send('delete',{student_id:ui.editor,confirmed:true});};
  q('#cs-toggle').onclick=()=>{readUI();ui.collapsed=!ui.collapsed;root.classList.toggle('compact',ui.collapsed);send('ui');};
  q('#cs-rail-search').onclick=()=>{ui.collapsed=false;ui.focus='#cs-id';send('ui');};
  q('#cs-theme').onclick=()=>{ui.theme=ui.theme==='light'?'dark':'light';root.style.colorScheme=ui.theme;send('ui');};
  all('[data-view]').forEach(b=>b.onclick=()=>{ui.view=b.dataset.view;closeEditor();applyView();send('ui');});
  function reset(){q('#cs-id').value='';q('#cs-name').value='';q('#cs-major').value='';q('#cs-min').value=0;q('#cs-sort').value='id';ui.focus='';send('ui');}
  q('#cs-reset').onclick=reset;q('#cs-clear').onclick=reset;
  ['#cs-id','#cs-name'].forEach(selector=>{q(selector).oninput=()=>{ui.focus=selector;clearTimeout(timer);timer=setTimeout(()=>send('ui'),550);};q(selector).onkeydown=e=>{if(e.key==='Enter')send('ui');};});
  ['#cs-major','#cs-min','#cs-sort'].forEach(selector=>{q(selector).onchange=()=>{ui.focus=selector;send('ui');};});
  q('#cs-min').oninput=()=>{q('#cs-min-value').textContent=Number(q('#cs-min').value).toFixed(2);};
  let toastTimer;
  q('#cs-toast').hidden=true;
  if(data.toast_id&&root.dataset.toastId!==data.toast_id){root.dataset.toastId=data.toast_id;q('#cs-toast').textContent=data.message;q('#cs-toast').hidden=false;toastTimer=setTimeout(()=>{q('#cs-toast').hidden=true;},4500);}
  const escape=e=>{if(e.key==='Escape')closeEditor();};root.addEventListener('keydown',escape);
  if(ui.focus&&q(ui.focus)){const input=q(ui.focus);input.focus();if(input.type==='text')input.setSelectionRange(input.value.length,input.value.length);}
  return ()=>{clearTimeout(timer);clearTimeout(toastTimer);root.removeEventListener('keydown',escape);};
}

"""


def main():
    import streamlit as st
    from streamlit.components.v2 import component
    st.set_page_config(page_title="CampusFlow", page_icon="🎓", layout="wide")
    # Page spacing only; all product styles remain isolated in the component.
    st.html("<style>.stMainBlockContainer{padding-top:1.2rem;max-width:1500px}</style>")
    if "campusflow_polished_state" not in st.session_state:
        st.session_state["campusflow_polished_state"] = new_state()
    state = st.session_state["campusflow_polished_state"]
    panel = component("campusflow_polished", html=HTML, css=CSS, js=JAVASCRIPT)
    result = panel(key="campusflow_panel", data=build_payload(state),
                   on_action_change=lambda: None, height="content")
    event = result.action
    if event and event.get("id") != state["last_event"]:
        handle_event(state, event)
        st.rerun()
    with st.expander("Backup & project information"):
        import json
        st.download_button("Download all students as JSON",
                           json.dumps(state["students"], indent=2, ensure_ascii=False),
                           file_name="students.json", mime="application/json")
        st.caption("The records are kept in this browser session, not permanently. Download a backup before closing. The custom UI uses HTML, CSS and JavaScript; CRUD, validation, filtering and statistics run in Python.")
        st.caption("This graphical version is supplementary: section 12 of the PDF prohibits graphical interfaces. Keep the console version for the strict PDF requirements.")


if __name__ == "__main__":
    main()

#python -m streamlit run campusflow_polished.py
