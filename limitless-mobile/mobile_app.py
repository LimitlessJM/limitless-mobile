import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import os, requests, json, base64, random, string
try:
    from zoneinfo import ZoneInfo
    SYDNEY_TZ = ZoneInfo("Australia/Sydney")
except:
    import pytz
    SYDNEY_TZ = pytz.timezone("Australia/Sydney")

def now_sydney():
    try:
        return datetime.now(SYDNEY_TZ)
    except:
        from datetime import timezone, timedelta
        return datetime.now(timezone(timedelta(hours=11)))

st.set_page_config(
    page_title="Limitless Site",
    page_icon="⚒️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;500;600;700;800;900&display=swap');
* { font-family: 'Barlow Semi Condensed', sans-serif !important; }
.main .block-container { padding: 1rem 1rem 5rem 1rem !important; max-width: 480px !important; margin: 0 auto !important; }
.stButton button { width: 100% !important; min-height: 52px !important; font-size: 16px !important; font-weight: 700 !important; border-radius: 12px !important; margin-bottom: 6px !important; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.site-card { background: #1e2d3d; border: 1px solid #2a3d4f; border-radius: 14px; padding: 16px; margin-bottom: 10px; }
.pin-display { font-size: 36px; letter-spacing: 12px; text-align: center; color: #2dd4bf; font-weight: 700; padding: 16px; background: #111c27; border-radius: 12px; margin-bottom: 14px; min-height: 72px; border: 1px solid #2a3d4f; }
.clock-btn-in { background: #2dd4bf !important; color: #0f172a !important; font-size: 20px !important; min-height: 70px !important; border-radius: 16px !important; }
.clock-btn-out { background: #f43f5e !important; color: #fff !important; font-size: 20px !important; min-height: 70px !important; border-radius: 16px !important; }
.status-badge-in { background: #0d2a1f; border: 1px solid #2dd4bf; border-radius: 8px; padding: 6px 14px; color: #2dd4bf; font-weight: 700; font-size: 13px; display: inline-block; }
.status-badge-out { background: #2d0f1a; border: 1px solid #f43f5e; border-radius: 8px; padding: 6px 14px; color: #f43f5e; font-weight: 700; font-size: 13px; display: inline-block; }
div[data-testid="stNumberInput"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Supabase ────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
try:
    if not SUPABASE_URL: SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    if not SUPABASE_KEY: SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
except: pass

USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

def supa_get(table, filters=None):
    if not USE_SUPABASE: return []
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
        if filters:
            for k, v in filters.items():
                url += f"&{k}=eq.{v}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        r = requests.get(url, headers=headers, timeout=8)
        return r.json() if r.status_code == 200 else []
    except: return []

def supa_post(table, data):
    if not USE_SUPABASE: return False, ""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {
            "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json", "Prefer": "return=minimal"
        }
        r = requests.post(url, headers=headers, data=json.dumps(data), timeout=8)
        return r.status_code in [200, 201], f"{r.status_code}: {r.text[:100]}"
    except Exception as e: return False, str(e)

def supa_patch(table, match_col, match_val, data):
    """Update a record in Supabase."""
    if not USE_SUPABASE: return False
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}?{match_col}=eq.{match_val}"
        headers = {
            "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json", "Prefer": "return=minimal"
        }
        r = requests.patch(url, headers=headers, data=json.dumps(data), timeout=8)
        return r.status_code in [200, 204]
    except: return False

# ── Local DB ─────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "limitless_mobile.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def local_fetch(query, params=()):
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()

def local_execute(query, params=()):
    with get_conn() as conn:
        conn.execute(query, params)
        conn.commit()

def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY, name TEXT, company_code TEXT UNIQUE)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY, name TEXT, role TEXT DEFAULT 'Roofer',
            hourly_rate REAL DEFAULT 0, active INTEGER DEFAULT 1,
            pin TEXT DEFAULT '', company_id INTEGER DEFAULT 1)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY, client TEXT DEFAULT '',
            address TEXT DEFAULT '', stage TEXT DEFAULT 'Live Job',
            company_id INTEGER DEFAULT 1)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS day_assignments (
            id INTEGER PRIMARY KEY, job_id TEXT DEFAULT '', client TEXT DEFAULT '',
            employee TEXT DEFAULT '', date TEXT DEFAULT '', note TEXT DEFAULT '',
            start_time TEXT DEFAULT '', end_time TEXT DEFAULT '',
            company_id INTEGER DEFAULT 1)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS clock_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, employee TEXT,
            job_id TEXT DEFAULT '', event_type TEXT, event_time TEXT,
            event_date TEXT, note TEXT DEFAULT '', status TEXT DEFAULT 'Pending',
            approved_by TEXT DEFAULT '', approved_at TEXT DEFAULT '',
            company_id INTEGER DEFAULT 1, synced INTEGER DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS labour_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, work_date TEXT,
            job_id TEXT, employee TEXT, hours REAL DEFAULT 0,
            hourly_rate REAL DEFAULT 0, note TEXT DEFAULT '',
            company_id INTEGER DEFAULT 1, synced INTEGER DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS job_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT,
            photo_date TEXT, caption TEXT DEFAULT '', photo_data BLOB,
            uploaded_by TEXT DEFAULT '', company_id INTEGER DEFAULT 1,
            synced INTEGER DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS mobile_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, employee TEXT,
            job_id TEXT, description TEXT, submitted_at TEXT,
            status TEXT DEFAULT 'Pending', company_id INTEGER DEFAULT 1,
            synced INTEGER DEFAULT 0)""")
        # Safe migrations
        for ddl in [
            "ALTER TABLE clock_events ADD COLUMN approved_by TEXT DEFAULT ''",
            "ALTER TABLE clock_events ADD COLUMN approved_at TEXT DEFAULT ''",
            "ALTER TABLE clock_events ADD COLUMN company_id INTEGER DEFAULT 1",
            "ALTER TABLE employees ADD COLUMN company_id INTEGER DEFAULT 1",
            "ALTER TABLE jobs ADD COLUMN company_id INTEGER DEFAULT 1",
            "ALTER TABLE day_assignments ADD COLUMN company_id INTEGER DEFAULT 1",
            "ALTER TABLE day_assignments ADD COLUMN start_time TEXT DEFAULT ''",
            "ALTER TABLE day_assignments ADD COLUMN end_time TEXT DEFAULT ''",
            "ALTER TABLE labour_logs ADD COLUMN company_id INTEGER DEFAULT 1",
            "ALTER TABLE labour_logs ADD COLUMN synced INTEGER DEFAULT 0",
            "ALTER TABLE job_photos ADD COLUMN synced INTEGER DEFAULT 0",
            "ALTER TABLE job_photos ADD COLUMN company_id INTEGER DEFAULT 1",
            "ALTER TABLE mobile_variations ADD COLUMN company_id INTEGER DEFAULT 1",
        ]:
            try: conn.execute(ddl)
            except: pass
        conn.commit()

init_db()

# ── Sync ─────────────────────────────────────────────────────────────────────
def sync_from_supabase(company_id):
    """Pull data for this company only."""
    if not USE_SUPABASE: return
    try:
        # Employees for this company
        emps = supa_get("employees", {"company_id": company_id})
        if emps:
            local_execute("DELETE FROM employees WHERE company_id=?", (company_id,))
            for e in emps:
                local_execute("""INSERT OR REPLACE INTO employees
                    (id,name,role,hourly_rate,active,pin,company_id) VALUES (?,?,?,?,?,?,?)""",
                    (e.get("id"), e.get("name",""), e.get("role",""),
                     e.get("hourly_rate",0), e.get("active",1),
                     e.get("pin",""), company_id))
        # Jobs for this company
        jobs = supa_get("jobs", {"company_id": company_id})
        if jobs:
            local_execute("DELETE FROM jobs WHERE company_id=?", (company_id,))
            for j in jobs:
                local_execute("""INSERT OR REPLACE INTO jobs
                    (job_id,client,address,stage,company_id) VALUES (?,?,?,?,?)""",
                    (j.get("job_id"), j.get("client",""),
                     j.get("address",""), j.get("stage",""), company_id))
        # Day assignments for this company
        assigns = supa_get("day_assignments", {"company_id": company_id})
        today = date.today().isoformat()
        for a in assigns:
            if a.get("date","") >= today:
                local_execute("""INSERT OR REPLACE INTO day_assignments
                    (id,job_id,client,employee,date,note,start_time,end_time,company_id)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (a.get("id"), a.get("job_id",""), a.get("client",""),
                     a.get("employee",""), a.get("date",""), a.get("note",""),
                     a.get("start_time",""), a.get("end_time",""), company_id))
        # Pull clock event approvals back
        clock_updates = supa_get("clock_events", {"company_id": company_id})
        for ce in clock_updates:
            cid = ce.get("id")
            status = ce.get("status","Pending")
            if cid and status in ("Approved","Rejected"):
                local_execute("UPDATE clock_events SET status=? WHERE id=?", (status, cid))
        # Pull approved labour_logs
        approved_ll = supa_get("labour_logs", {"company_id": company_id})
        for ll in approved_ll:
            emp   = ll.get("employee","")
            wdate = ll.get("work_date","")
            jid   = ll.get("job_id","")
            hrs   = ll.get("hours",0)
            if not emp or not wdate: continue
            rows = local_fetch(
                "SELECT id FROM labour_logs WHERE employee=? AND work_date=? AND job_id=? AND hours=? AND company_id=?",
                (emp, wdate, jid, hrs, company_id))
            if not rows:
                local_execute("""INSERT INTO labour_logs
                    (work_date,job_id,employee,hours,hourly_rate,note,company_id,synced)
                    VALUES (?,?,?,?,?,?,?,1)""",
                    (wdate, jid, emp, hrs, ll.get("hourly_rate",0), ll.get("note","") or "", company_id))
    except: pass

def sync_to_supabase(employee, company_id):
    """Push unsynced records for this employee/company."""
    if not USE_SUPABASE: return []
    errors = []
    try:
        # Clock events
        unsynced = local_fetch(
            "SELECT * FROM clock_events WHERE synced=0 AND employee=? AND company_id=?",
            (employee, company_id))
        for e in unsynced:
            ok, msg = supa_post("clock_events", {
                "employee": e["employee"], "job_id": e["job_id"] or "",
                "event_type": e["event_type"], "event_time": e["event_time"],
                "event_date": e["event_date"], "note": e["note"] or "",
                "status": "Pending", "company_id": company_id
            })
            if ok:
                local_execute("UPDATE clock_events SET synced=1 WHERE id=?", (e["id"],))
            else:
                errors.append(f"clock_event: {msg}")
        # Variations
        unsynced_v = local_fetch(
            "SELECT * FROM mobile_variations WHERE synced=0 AND employee=? AND company_id=?",
            (employee, company_id))
        for v in unsynced_v:
            ok, msg = supa_post("mobile_variations", {
                "employee": v["employee"], "job_id": v["job_id"],
                "description": v["description"], "submitted_at": v["submitted_at"],
                "status": v["status"], "company_id": company_id
            })
            if ok:
                local_execute("UPDATE mobile_variations SET synced=1 WHERE id=?", (v["id"],))
            else:
                errors.append(f"variation: {msg}")
        # Labour logs
        unsynced_ll = local_fetch(
            "SELECT * FROM labour_logs WHERE synced=0 AND employee=? AND company_id=?",
            (employee, company_id))
        for ll in unsynced_ll:
            ok, msg = supa_post("labour_logs", {
                "work_date": ll["work_date"], "job_id": ll["job_id"] or "",
                "employee": ll["employee"], "hours": ll["hours"],
                "hourly_rate": ll["hourly_rate"], "note": ll["note"] or "",
                "company_id": company_id
            })
            if ok:
                local_execute("UPDATE labour_logs SET synced=1 WHERE id=?", (ll["id"],))
            else:
                errors.append(f"labour_log: {msg}")
        # Photos — resize before upload to keep under Supabase limits
        unsynced_ph = local_fetch(
            "SELECT * FROM job_photos WHERE synced=0 AND company_id=?", (company_id,))
        for ph in unsynced_ph:
            if not ph["photo_data"]: continue
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(ph["photo_data"]))
                img.thumbnail((1200, 1200))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=75)
                photo_b64 = base64.b64encode(buf.getvalue()).decode()
            except:
                photo_b64 = base64.b64encode(ph["photo_data"]).decode()
            ok, msg = supa_post("job_photos", {
                "job_id": ph["job_id"] or "", "photo_date": ph["photo_date"] or "",
                "caption": ph["caption"] or "", "photo_data": photo_b64,
                "uploaded_by": ph["uploaded_by"] or "", "company_id": company_id
            })
            if ok:
                local_execute("UPDATE job_photos SET synced=1 WHERE id=?", (ph["id"],))
            else:
                errors.append(f"photo: {msg}")
    except Exception as e:
        errors.append(str(e))
    return errors

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [
    ("mobile_user", None), ("mobile_company_id", None),
    ("mobile_company_name", ""), ("mobile_page", "login"),
    ("pin_input", ""), ("login_stage", "company"),  # company → employee → pin
    ("selected_employee", None), ("company_employees", []),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_clock_status(employee, company_id):
    today = date.today().isoformat()
    events = local_fetch(
        "SELECT event_type, event_time, job_id FROM clock_events WHERE employee=? AND event_date=? AND company_id=? ORDER BY id DESC LIMIT 1",
        (employee, today, company_id))
    if not events: return None, None, None
    return events[0]["event_type"], events[0]["event_time"], events[0]["job_id"]

def get_today_hours(employee, company_id):
    today = date.today().isoformat()
    events = local_fetch(
        "SELECT event_type, event_time FROM clock_events WHERE employee=? AND event_date=? AND company_id=? ORDER BY id",
        (employee, today, company_id))
    total = 0.0
    cin = None
    for e in events:
        if e["event_type"] == "in":
            try: cin = datetime.strptime(e["event_time"], "%H:%M:%S")
            except: pass
        elif e["event_type"] == "out" and cin:
            try:
                cout = datetime.strptime(e["event_time"], "%H:%M:%S")
                total += (cout - cin).seconds / 3600
                cin = None
            except: pass
    if cin:
        total += (now_sydney().replace(tzinfo=None) - cin).seconds / 3600
    return round(total, 1)

def lookup_company_code(code):
    """Check local DB first, then Supabase."""
    code = code.strip().upper()
    local = local_fetch("SELECT id, name FROM companies WHERE UPPER(company_code)=?", (code,))
    if local:
        return local[0]["id"], local[0]["name"]
    if USE_SUPABASE:
        rows = supa_get("companies")
        for r in rows:
            if str(r.get("company_code","")).upper() == code:
                cid = r.get("id")
                cname = r.get("name","")
                local_execute("INSERT OR REPLACE INTO companies (id,name,company_code) VALUES (?,?,?)",
                    (cid, cname, r.get("company_code","")))
                return cid, cname
    return None, None

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN FLOW
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.mobile_user is None:
    st.markdown("""
    <div style='text-align:center;padding:32px 0 20px'>
        <div style='font-size:28px;font-weight:900;letter-spacing:.08em;color:#2dd4bf'>LIMITLESS</div>
        <div style='font-size:12px;color:#475569;letter-spacing:.15em;text-transform:uppercase;margin-top:4px'>Field App</div>
    </div>""", unsafe_allow_html=True)

    stage = st.session_state.login_stage

    # ── STAGE 1: Company Code ─────────────────────────────────────────────
    if stage == "company":
        st.markdown("<div style='font-size:16px;font-weight:700;color:#94a3b8;text-align:center;margin-bottom:20px'>Enter your Company Code</div>", unsafe_allow_html=True)
        code_input = st.text_input("Company Code", placeholder="e.g. UTR-4821",
            max_chars=12, label_visibility="collapsed").upper()
        if st.button("Continue →", type="primary", use_container_width=True):
            if code_input.strip():
                with st.spinner("Looking up company..."):
                    cid, cname = lookup_company_code(code_input)
                if cid:
                    st.session_state.mobile_company_id = cid
                    st.session_state.mobile_company_name = cname
                    # Pull employees for this company
                    sync_from_supabase(cid)
                    emps = local_fetch(
                        "SELECT name FROM employees WHERE active=1 AND company_id=? ORDER BY name",
                        (cid,))
                    st.session_state.company_employees = [e["name"] for e in emps]
                    st.session_state.login_stage = "employee"
                    st.rerun()
                else:
                    st.error("❌ Company code not found. Check with your supervisor.")
            else:
                st.error("Please enter your company code.")
        st.markdown("<div style='text-align:center;color:#334155;font-size:12px;margin-top:20px'>Your supervisor will give you your company code</div>", unsafe_allow_html=True)

    # ── STAGE 2: Select Employee ──────────────────────────────────────────
    elif stage == "employee":
        st.markdown(f"<div style='text-align:center;font-size:14px;font-weight:700;color:#2dd4bf;margin-bottom:4px'>{st.session_state.mobile_company_name}</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:16px;font-weight:700;color:#94a3b8;text-align:center;margin-bottom:20px'>Who are you?</div>", unsafe_allow_html=True)
        emps = st.session_state.company_employees
        if not emps:
            st.warning("No employees found. Contact your supervisor.")
        else:
            for name in emps:
                if st.button(name, use_container_width=True):
                    st.session_state.selected_employee = name
                    st.session_state.pin_input = ""
                    st.session_state.login_stage = "pin"
                    st.rerun()
        if st.button("← Back", use_container_width=False):
            st.session_state.login_stage = "company"
            st.session_state.mobile_company_id = None
            st.rerun()

    # ── STAGE 3: PIN Entry ────────────────────────────────────────────────
    elif stage == "pin":
        emp_name = st.session_state.selected_employee
        cid = st.session_state.mobile_company_id
        st.markdown(f"<div style='text-align:center;font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:4px'>G'day, {emp_name.split()[0]} 👋</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:14px;color:#475569;text-align:center;margin-bottom:20px'>Enter your PIN</div>", unsafe_allow_html=True)

        pin = st.session_state.pin_input
        dots = "●" * len(pin) + "○" * (4 - min(len(pin), 4))
        st.markdown(f"<div class='pin-display'>{dots}</div>", unsafe_allow_html=True)

        # Numpad
        digits = [["1","2","3"],["4","5","6"],["7","8","9"],["←","0","✓"]]
        for row in digits:
            cols = st.columns(3)
            for col, digit in zip(cols, row):
                with col:
                    if st.button(digit, use_container_width=True, key=f"pin_{digit}"):
                        if digit == "←":
                            st.session_state.pin_input = pin[:-1]
                            st.rerun()
                        elif digit == "✓":
                            emp = local_fetch(
                                "SELECT pin FROM employees WHERE name=? AND company_id=? AND active=1",
                                (emp_name, cid))
                            stored_pin = emp[0]["pin"] if emp else ""
                            if pin == stored_pin:
                                st.session_state.mobile_user = emp_name
                                st.session_state.mobile_page = "home"
                                st.session_state.login_stage = "company"
                                st.session_state.pin_input = ""
                                st.rerun()
                            else:
                                st.session_state.pin_input = ""
                                st.error("❌ Wrong PIN")
                                st.rerun()
                        else:
                            if len(pin) < 6:
                                st.session_state.pin_input = pin + digit
                                st.rerun()

        if st.button("← Back to name select"):
            st.session_state.login_stage = "employee"
            st.session_state.pin_input = ""
            st.rerun()

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# LOGGED IN
# ══════════════════════════════════════════════════════════════════════════════
user       = st.session_state.mobile_user
company_id = st.session_state.mobile_company_id
company_name = st.session_state.mobile_company_name

last_event, last_time, last_job = get_clock_status(user, company_id)
is_clocked_in = last_event == "in"
today_hours   = get_today_hours(user, company_id)

# Top bar
st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;
    background:#111c27;border-radius:14px;padding:10px 14px;margin-bottom:14px;
    border:1px solid #1e2d3d'>
    <div style="font-size:20px;font-weight:700;letter-spacing:.06em;color:#2dd4bf">LIMITLESS</div>
    <div style='text-align:right'>
        <div style='font-size:14px;font-weight:700;color:#e2e8f0'>{user}</div>
        <div style='font-size:11px;color:#334155'>{company_name}</div>
        <div style='font-size:12px;color:{"#2dd4bf" if is_clocked_in else "#475569"}'>
            {"🟢 On Site" if is_clocked_in else "⚫ Off Site"} · {today_hours}h today
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation
page = st.session_state.mobile_page
nav_items = [("🏠","Home","home"),("⏱","Clock","clock"),("📷","Photos","photos"),("⚠️","Variation","variation"),("👤","Profile","profile")]
nav_cols = st.columns(5)
for col, (icon, label, pg) in zip(nav_cols, nav_items):
    with col:
        color = "#2dd4bf" if page == pg else "#475569"
        st.markdown(f"<div style='text-align:center;font-size:20px'>{icon}</div><div style='text-align:center;font-size:10px;font-weight:700;color:{color};letter-spacing:.05em;text-transform:uppercase'>{label}</div>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{pg}", use_container_width=True):
            st.session_state.mobile_page = pg; st.rerun()

st.divider()
today_str  = date.today().isoformat()

# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
if page == "home":
    today_nice = date.today().strftime("%A, %d %B")
    hour = now_sydney().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "G'day"

    st.markdown(f"<div style='font-size:24px;font-weight:800;color:#e2e8f0;margin-bottom:2px'>{greeting}, {user.split()[0]}.</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:16px'>{today_nice}</div>", unsafe_allow_html=True)

    if is_clocked_in:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#0d2a1f,#1a3a2a);border:2px solid #2dd4bf;
            border-radius:16px;padding:20px;text-align:center;margin-bottom:16px'>
            <div style='font-size:13px;font-weight:700;color:#2dd4bf;letter-spacing:.1em;text-transform:uppercase'>On Site</div>
            <div style='font-size:48px;font-weight:900;color:#2dd4bf;line-height:1.1'>{today_hours}h</div>
            <div style='color:#94a3b8;font-size:13px'>Clocked in at {(last_time or "")[:5]} · {last_job or ""}</div>
        </div>""", unsafe_allow_html=True)
        if st.button("⏹ Clock Out Now", type="primary"):
            st.session_state.mobile_page = "clock"; st.rerun()
    else:
        st.markdown(f"""
        <div style='background:#111c27;border:1px solid #2a3d4f;
            border-radius:16px;padding:20px;text-align:center;margin-bottom:16px'>
            <div style='font-size:13px;font-weight:700;color:#475569;letter-spacing:.1em;text-transform:uppercase'>Not On Site</div>
            <div style='font-size:48px;font-weight:900;color:#475569;line-height:1.1'>{today_hours}h</div>
            <div style='color:#64748b;font-size:13px'>Ready to start</div>
        </div>""", unsafe_allow_html=True)
        if st.button("▶ Clock In", type="primary"):
            st.session_state.mobile_page = "clock"; st.rerun()

    st.markdown("<div style='font-size:12px;font-weight:700;color:#2dd4bf;text-transform:uppercase;letter-spacing:.1em;margin:18px 0 8px'>My Jobs Today</div>", unsafe_allow_html=True)
    assigned = local_fetch("""
        SELECT da.job_id, da.client, da.note, da.start_time, da.end_time, j.address
        FROM day_assignments da LEFT JOIN jobs j ON j.job_id=da.job_id
        WHERE da.employee=? AND da.date=? AND da.company_id=?""",
        (user, today_str, company_id))

    if not assigned:
        st.markdown("<div class='site-card'><p style='color:#64748b;margin:0'>No jobs assigned today. Check with your supervisor.</p></div>", unsafe_allow_html=True)
    else:
        for job in assigned:
            st_t = str(job["start_time"] or "")
            en_t = str(job["end_time"] or "")
            time_str = f"{st_t[:5]} – {en_t[:5]}" if st_t and en_t else ""
            st.markdown(f"""
            <div class='site-card'>
                <div style='font-size:18px;font-weight:800;color:#2dd4bf'>{job['job_id']}</div>
                <div style='color:#e2e8f0;font-size:15px;font-weight:600'>{job['client'] or ''}</div>
                <div style='color:#64748b;font-size:13px;margin-top:4px'>📍 {job['address'] or ''}</div>
                {f"<div style='color:#f59e0b;font-size:13px;margin-top:4px'>🕐 {time_str}</div>" if time_str else ""}
                {f"<div style='color:#94a3b8;font-size:13px'>{job['note']}</div>" if job['note'] else ""}
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CLOCK
# ══════════════════════════════════════════════════════════════════════════════
elif page == "clock":
    now_str = now_sydney().strftime("%I:%M %p")

    _border_col = "#2dd4bf" if is_clocked_in else "#2a3d4f"
    _badge_cls  = "status-badge-in" if is_clocked_in else "status-badge-out"
    _site_label = "🟢 ON SITE" if is_clocked_in else "⚫ OFF SITE"
    _cin_line   = f"<div style='color:#94a3b8;font-size:13px;margin-top:10px'>Clocked in at {(last_time or '')[:5]} on {last_job or ''}</div>" if is_clocked_in else ""
    st.markdown(f"""
    <div style='background:#111c27;border:2px solid {_border_col};
        border-radius:16px;padding:24px;text-align:center;margin-bottom:20px'>
        <div style='font-size:52px;font-weight:900;color:#e2e8f0;letter-spacing:-.02em'>{now_str}</div>
        <div style='margin-top:8px'>
            <span class='{_badge_cls}'>{_site_label}</span>
        </div>
        {_cin_line}
        <div style='font-size:28px;font-weight:800;color:#2dd4bf;margin-top:8px'>{today_hours}h today</div>
    </div>""", unsafe_allow_html=True)

    all_jobs = local_fetch(
        "SELECT job_id, client FROM jobs WHERE stage='Live Job' AND company_id=? ORDER BY job_id",
        (company_id,))
    if not all_jobs:
        all_jobs = local_fetch(
            "SELECT job_id, client FROM jobs WHERE company_id=? ORDER BY job_id",
            (company_id,))
    job_options = [f"{j['job_id']} — {j['client']}" for j in all_jobs] if all_jobs else ["No jobs"]
    job_ids     = [j["job_id"] for j in all_jobs] if all_jobs else [""]

    # Pre-select today's assigned job if only one
    assigned_today = local_fetch(
        "SELECT job_id FROM day_assignments WHERE employee=? AND date=? AND company_id=? LIMIT 1",
        (user, today_str, company_id))
    default_idx = 0
    if assigned_today and assigned_today[0]["job_id"] in job_ids:
        default_idx = job_ids.index(assigned_today[0]["job_id"])

    selected_idx = st.selectbox("Job", range(len(job_options)),
        format_func=lambda x: job_options[x], index=default_idx)
    selected_job = job_ids[selected_idx] if job_ids else ""
    clock_note = st.text_input("Note (optional)", placeholder="e.g. Started ridge capping")

    if is_clocked_in:
        if st.button("⏹  Clock Out", type="primary", use_container_width=True):
            now = datetime.now()
            local_execute("""INSERT INTO clock_events
                (employee,job_id,event_type,event_time,event_date,note,status,company_id,synced)
                VALUES (?,?,?,?,?,?,?,?,0)""",
                (user, selected_job, "out", now.strftime("%H:%M:%S"), today_str, clock_note, "Pending", company_id))
            emp = local_fetch("SELECT hourly_rate FROM employees WHERE name=? AND company_id=?", (user, company_id))
            rate = float(emp[0]["hourly_rate"]) if emp else 0.0
            hours_worked = get_today_hours(user, company_id)
            if hours_worked > 0:
                local_execute("""INSERT INTO labour_logs
                    (work_date,job_id,employee,hours,hourly_rate,note,company_id,synced)
                    VALUES (?,?,?,?,?,?,?,0)""",
                    (today_str, selected_job, user, hours_worked, rate, clock_note or "", company_id))
            sync_from_supabase(company_id)
            errs = sync_to_supabase(user, company_id)
            if errs:
                st.warning(f"⚠️ Sync issue — data saved locally: {errs[0]}")
            else:
                st.success(f"✅ Clocked out — {hours_worked}h logged · Pending approval")
            st.rerun()
    else:
        if st.button("▶  Clock In", type="primary", use_container_width=True):
            local_execute("""INSERT INTO clock_events
                (employee,job_id,event_type,event_time,event_date,note,status,company_id,synced)
                VALUES (?,?,?,?,?,?,?,?,0)""",
                (user, selected_job, "in", now_sydney().strftime("%H:%M:%S"), today_str, clock_note, "Pending", company_id))
            sync_from_supabase(company_id)
            errs = sync_to_supabase(user, company_id)
            if errs:
                st.warning(f"⚠️ Sync issue: {errs[0]}")
            else:
                st.success(f"✅ Clocked in on {selected_job}")
            st.rerun()

    history = local_fetch(
        "SELECT event_type, event_time, job_id, status FROM clock_events WHERE employee=? AND event_date=? AND company_id=? ORDER BY id",
        (user, today_str, company_id))
    if history:
        st.markdown("<div style='font-size:12px;font-weight:700;color:#2dd4bf;text-transform:uppercase;margin:20px 0 8px'>Today's Log</div>", unsafe_allow_html=True)
        for h in history:
            color = "#2dd4bf" if h["event_type"]=="in" else "#f43f5e"
            label = "IN" if h["event_type"]=="in" else "OUT"
            status_col = "#f59e0b" if h["status"]=="Pending" else "#2dd4bf" if h["status"]=="Approved" else "#f43f5e"
            st.markdown(f"""
            <div style='display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid #1e2d3d'>
                <span style='color:{color};font-weight:800;font-size:12px;min-width:32px'>{label}</span>
                <span style='color:#e2e8f0;font-size:15px;font-weight:700'>{h["event_time"][:5]}</span>
                <span style='color:#64748b;font-size:13px;flex:1'>{h["job_id"]}</span>
                <span style='color:{status_col};font-size:11px;font-weight:700'>{h["status"] or "Pending"}</span>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PHOTOS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "photos":
    st.markdown("<div style='font-size:22px;font-weight:800;color:#e2e8f0;margin-bottom:16px'>📷 Site Photos</div>", unsafe_allow_html=True)
    all_jobs = local_fetch("SELECT job_id FROM jobs WHERE company_id=? ORDER BY job_id", (company_id,))
    job_options = [j["job_id"] for j in all_jobs] if all_jobs else ["No jobs"]
    photo_job = st.selectbox("Job", job_options)
    photo_caption = st.text_input("Caption", placeholder="e.g. Ridge completed, north face")
    photo_file = st.file_uploader("Take or upload photo", type=["jpg","jpeg","png","heic"])
    if photo_file and st.button("Upload Photo", type="primary"):
        local_execute("""INSERT INTO job_photos
            (job_id,photo_date,caption,photo_data,uploaded_by,company_id,synced)
            VALUES (?,?,?,?,?,?,0)""",
            (photo_job, today_str, photo_caption, photo_file.read(), user, company_id))
        errs = sync_to_supabase(user, company_id)
        if not errs:
            st.success("✅ Photo uploaded and synced!")
        else:
            st.success("✅ Photo saved locally — will sync when connected.")
        st.rerun()

    recent = local_fetch(
        "SELECT caption, photo_date, job_id FROM job_photos WHERE uploaded_by=? AND company_id=? ORDER BY id DESC LIMIT 10",
        (user, company_id))
    if recent:
        st.markdown("<div style='font-size:12px;font-weight:700;color:#2dd4bf;text-transform:uppercase;margin:16px 0 8px'>Recent Uploads</div>", unsafe_allow_html=True)
        for p in recent:
            st.markdown(f"<div class='site-card'><span style='color:#2dd4bf'>📷</span> <span style='color:#e2e8f0'>{p['caption'] or 'No caption'}</span> <span style='color:#64748b;font-size:12px'>· {p['job_id']} · {p['photo_date']}</span></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VARIATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "variation":
    st.markdown("<div style='font-size:22px;font-weight:800;color:#e2e8f0;margin-bottom:6px'>⚠️ Log Variation</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#94a3b8;font-size:13px;margin-bottom:16px'>Found extra work on site? Log it here for office approval.</div>", unsafe_allow_html=True)

    all_jobs = local_fetch("SELECT job_id, client FROM jobs WHERE company_id=? ORDER BY job_id", (company_id,))
    job_options = [f"{j['job_id']} — {j['client']}" for j in all_jobs] if all_jobs else ["No jobs"]
    job_ids = [j["job_id"] for j in all_jobs] if all_jobs else [""]
    var_idx = st.selectbox("Job", range(len(job_options)), format_func=lambda x: job_options[x])
    var_job = job_ids[var_idx] if job_ids else ""
    var_desc = st.text_area("What did you find?", placeholder="e.g. Found rotten fascia board on north face — approx 6m needs replacing", height=120)

    if st.button("Submit Variation", type="primary"):
        if var_desc.strip():
            local_execute("""INSERT INTO mobile_variations
                (employee,job_id,description,submitted_at,status,company_id,synced)
                VALUES (?,?,?,?,?,?,0)""",
                (user, var_job, var_desc.strip(), now_sydney().isoformat(), "Pending", company_id))
            errs = sync_to_supabase(user, company_id)
            st.success("✅ Variation submitted — office will review and approve.")
            st.balloons()
        else:
            st.error("Please describe what you found.")

    my_vars = local_fetch(
        "SELECT job_id, description, status FROM mobile_variations WHERE employee=? AND company_id=? ORDER BY id DESC LIMIT 5",
        (user, company_id))
    if my_vars:
        st.markdown("<div style='font-size:12px;font-weight:700;color:#2dd4bf;text-transform:uppercase;margin:16px 0 8px'>My Variations</div>", unsafe_allow_html=True)
        for v in my_vars:
            sc = "#2dd4bf" if v["status"]=="Approved" else "#f59e0b" if v["status"]=="Pending" else "#f43f5e"
            st.markdown(f"""
            <div class='site-card'>
                <div style='display:flex;justify-content:space-between;align-items:center'>
                    <span style='color:#e2e8f0;font-weight:700'>{v['job_id']}</span>
                    <span style='color:{sc};font-size:12px;font-weight:700'>{v['status']}</span>
                </div>
                <div style='color:#94a3b8;font-size:13px;margin-top:4px'>{str(v['description'])[:80]}</div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "profile":
    st.markdown(f"<div style='font-size:22px;font-weight:800;color:#e2e8f0;margin-bottom:4px'>👤 {user}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:13px;color:#475569;margin-bottom:16px'>{company_name}</div>", unsafe_allow_html=True)

    if USE_SUPABASE:
        st.markdown("<div style='background:#0d2a1f;border:1px solid #2dd4bf;border-radius:8px;padding:8px 14px;font-size:13px;color:#2dd4bf;margin-bottom:12px'>🟢 Connected to office</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background:#2d0f0f;border:1px solid #f43f5e;border-radius:8px;padding:8px 14px;font-size:13px;color:#f43f5e;margin-bottom:12px'>🔴 Offline — data saves locally and syncs when connected</div>", unsafe_allow_html=True)

    week_total = local_fetch(
        "SELECT SUM(hours) AS h FROM labour_logs WHERE employee=? AND company_id=? AND work_date >= date('now','-7 days')",
        (user, company_id))
    week_h = float(week_total[0]["h"] or 0) if week_total and week_total[0]["h"] else 0

    st.markdown(f"""
    <div class='site-card' style='text-align:center;padding:24px'>
        <div style='font-size:52px;font-weight:900;color:#2dd4bf'>{today_hours}h</div>
        <div style='color:#64748b;font-size:14px'>today</div>
        <div style='height:1px;background:#2a3d4f;margin:16px 0'></div>
        <div style='font-size:28px;font-weight:700;color:#94a3b8'>{week_h:.1f}h</div>
        <div style='color:#64748b;font-size:13px'>this week (approved)</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='color:#475569;font-size:12px;text-align:center;margin:8px 0 16px'>Hours are pending director approval before counting toward your timesheet.</div>", unsafe_allow_html=True)

    if st.button("🔄 Sync with Office", use_container_width=True):
        with st.spinner("Syncing..."):
            sync_from_supabase(company_id)
            errs = sync_to_supabase(user, company_id)
        if errs:
            for err in errs:
                st.error(f"⚠️ {err}")
        else:
            st.success("✅ Synced!")

    st.markdown("<div style='font-size:12px;font-weight:700;color:#2dd4bf;text-transform:uppercase;margin:20px 0 10px'>Change PIN</div>", unsafe_allow_html=True)
    new_pin     = st.text_input("New PIN (4-6 digits)", type="password", max_chars=6)
    confirm_pin = st.text_input("Confirm PIN", type="password", max_chars=6)
    if st.button("Update PIN"):
        if new_pin and new_pin == confirm_pin and new_pin.isdigit():
            local_execute("UPDATE employees SET pin=? WHERE name=? AND company_id=?",
                (new_pin, user, company_id))
            # Push the PIN change to Supabase so it survives a re-sync
            supa_patch("employees", "name", user, {"pin": new_pin})
            st.success("✅ PIN updated!")
        else:
            st.error("PINs must match and be digits only.")

    st.divider()
    if st.button("Sign Out"):
        st.session_state.mobile_user       = None
        st.session_state.mobile_company_id = None
        st.session_state.mobile_company_name = ""
        st.session_state.mobile_page       = "login"
        st.session_state.login_stage       = "company"
        st.session_state.pin_input         = ""
        st.session_state.selected_employee = None
        st.rerun()
