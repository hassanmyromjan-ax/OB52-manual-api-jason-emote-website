# -*- coding: utf-8 -*-
"""
AX EMOTE SERVER — MANAGER (website + admin panel + multi-bot supervisor)

প্রতিটি guest account একটা আলাদা process (bot_worker.py) হিসেবে চলে:
  - একটা bot ban/crash হলেও বাকিগুলো চলতে থাকে
  - bot ডিলেট করলে process বন্ধ + data থেকে একেবারে মুছে যায়
Admin panel:  <your-link>/romjan100
"""
import os, sys
sys.dont_write_bytecode = True   # __pycache__ তৈরি হবে না
import json, time, threading, subprocess, socket, secrets, hashlib, hmac, atexit, signal, re, math, html as _html
from datetime import date
import requests
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from flask import Flask, request, jsonify, send_from_directory, make_response, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
# কোনো data/ ফোল্ডার, logs বা json ফাইল তৈরি হয় না — সব memory তে থাকে।
# (ঐচ্ছিক) restart এর পরেও bot রাখতে চাইলে hosting এ env দিন:  AX_STORE_FILE=/path/to/store.json
STORE_FILE = os.environ.get("AX_STORE_FILE", "").strip()
JSON_POOL_FILE = os.environ.get("AX_JSON_POOL_FILE", os.path.join(BASE_DIR, "json_accounts.json")).strip()

app = Flask(__name__, static_folder=STATIC_DIR)

# ═══════════════ WEBSITE CONFIG (task system) ═══════════════
TASKS_CONFIG = [
    {"id": "task1", "name": "JOIN TELEGRAM CHANNEL", "link": "https://t.me/axemoteserver"},
    {"id": "task2", "name": "JOIN 2d TELEGRAM", "link": "https://t.me/axromjanyt"},
    {"id": "task3", "name": "SUBSCRIBE YOUTUBE", "link": "https://www.youtube.com/@axromjan"},
]
SETTINGS_CONFIG = {"maintenance": "off", "telegram": "https://t.me/axemoteserver"}
DEFAULT_SITE_CONFIG = {"tasks": TASKS_CONFIG, "maintenance": "off", "notice": "ওয়েবসাইটে সাময়িক রক্ষণাবেক্ষণের কাজ চলছে। অনুগ্রহ করে কিছুক্ষণ পরে আবার আসুন।", "social_links": [{"name": "TELEGRAM", "link": "https://t.me/axemoteserver"}], "auth_mode": "manual", "api_name": "AX-ROM", "api_urls": {"BD": "https://guest-make-ff.vercel.app/make_account?server=BD&name=AX-ROM", "IND": "https://guest-make-ff.vercel.app/make_account?server=IND&name=AX-ROM"}, "auto_leave": True}

# ═══════════════ ADMIN AUTH (password কখনোই browser এ যায় না) ═══════════════
ADMIN_PATH = os.environ.get("ADMIN_PATH", "/romjan100")
_SALT = bytes.fromhex("41582d524f4d4a414e2d41444d494e2d7631")
# PBKDF2-SHA256 hash — মূল password এই ফাইলে/HTML/JS এ কোথাও লেখা নেই
_ADMIN_HASH = "d39afb5c8af4d442b48698ace0a9152fd2f8b0d894e6050cd23f69f4a2a6a39f"
if os.environ.get("ADMIN_PASSWORD"):   # চাইলে hosting env দিয়ে বদলানো যায়
    _ADMIN_HASH = hashlib.pbkdf2_hmac('sha256', os.environ["ADMIN_PASSWORD"].encode(), _SALT, 200000).hex()

SESSIONS = {}            # token -> (scope_key, expiry)   scope_key: 'main' বা clone slug
SESSION_TTL = 12 * 3600
FAILS = {}               # "scope|ip" -> (count, lock_until)
_auth_lock = threading.Lock()

def _client_ip():
    xf = request.headers.get('X-Forwarded-For', '')
    return (xf.split(',')[0].strip() if xf else request.remote_addr) or '?'

def _pw_hash(pw, salt=_SALT):
    return hashlib.pbkdf2_hmac('sha256', (pw or '').encode(), salt, 200000).hex()

def _check_password(pw: str) -> bool:
    # Environment password has priority; otherwise use the persisted admin hash.
    if os.environ.get("ADMIN_PASSWORD"):
        expected = _pw_hash(os.environ["ADMIN_PASSWORD"])
    else:
        site = _MEM.get("site") or {}
        expected = site.get("admin_password_hash") or _ADMIN_HASH
    return hmac.compare_digest(_pw_hash(pw), expected)

# ═══════════════ STORAGE ═══════════════
_store_lock = threading.RLock()

REGIONS = [
    {"code": "BD",  "label": "BANGLADESH 🇧🇩"}, {"code": "IND", "label": "INDIA 🇮🇳"},
    {"code": "PK",  "label": "PAKISTAN 🇵🇰"},   {"code": "SG",  "label": "SINGAPORE 🇸🇬"},
    {"code": "ID",  "label": "INDONESIA 🇮🇩"},  {"code": "ME",  "label": "MIDDLE EAST 🇦🇪"},
    {"code": "VN",  "label": "VIETNAM 🇻🇳"},    {"code": "TW",  "label": "TAIWAN 🇹🇼"},
    {"code": "CIS", "label": "CIS 🇷🇺"},        {"code": "TH",  "label": "THAILAND 🇹🇭"},
    {"code": "EU",  "label": "EUROPE 🇪🇺"},     {"code": "US",  "label": "USA 🇺🇸"},
    {"code": "SAC", "label": "SOUTH AMERICA 🌎"}, {"code": "LK", "label": "SRI LANKA 🇱🇰"},
    {"code": "BR",  "label": "BRAZIL 🇧🇷"},
]
REGION_CODES = {r["code"] for r in REGIONS}

_MEM = {"servers": None, "bots": [], "tenants": {}, "site": None, "json_accounts": {}}

def _persist():
    """শুধু AX_STORE_FILE সেট করা থাকলেই ফাইলে লেখে; নাহলে কিছুই লেখে না"""
    if not STORE_FILE: return
    try:
        with open(STORE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"servers": _MEM["servers"], "bots": _MEM["bots"], "tenants": _MEM["tenants"], "site": _MEM.get("site"), "json_accounts": _MEM.get("json_accounts", {})}, f, ensure_ascii=False)
    except Exception as e:
        print("[store]", e)

def _load_store_file():
    if not STORE_FILE or not os.path.exists(STORE_FILE): return
    try:
        with open(STORE_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
        _MEM["servers"] = d.get("servers") or None
        _MEM["bots"] = d.get("bots") or []
        _MEM["tenants"] = d.get("tenants") or {}
        _MEM["site"] = d.get("site")
        _MEM["json_accounts"] = d.get("json_accounts") or {}
        # Session-bound JSON bots are temporary; retain their source accounts, not active leases.
        _MEM["bots"] = [b for b in _MEM["bots"] if b.get("source") != "json"]
    except Exception as e:
        print("[store]", e)

def server_bot_mode(server, scope=None):
    """Original Website uses one globally selected bot category for every server."""
    cfg = site_config(scope)
    mode = str(cfg.get("auth_mode") or "manual").lower()
    return mode if mode in ("manual", "api", "json") else "manual"

def load_servers():
    with _store_lock:
        if _MEM["servers"] is None:
            _MEM["servers"] = [{"id": "bd", "name": "BANGLADESH 🇧🇩", "region": "BD"},
                               {"id": "ind", "name": "INDIA 🇮🇳", "region": "IND"}]
        return [dict(s) for s in _MEM["servers"]]

def save_servers(s):
    with _store_lock:
        _MEM["servers"] = s; _persist()

def load_bots():
    with _store_lock: return [dict(b) for b in _MEM["bots"]]

def save_bots(b):
    with _store_lock:
        _MEM["bots"] = b; _persist()

# === VISIT COUNTER (file-based — আগের লজিক, শুধু এই একটি visits.json ফাইল) ===
VISITS_FILE = os.path.join(BASE_DIR, 'visits.json')

def load_visits():
    try:
        with open(VISITS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"total": 0, "today": 0, "date": str(date.today())}

def save_visits(v):
    try:
        with open(VISITS_FILE, 'w') as f:
            json.dump(v, f)
    except Exception:
        pass

def record_visit():
    with _store_lock:
        v = load_visits()
        today = str(date.today())
        v["total"] = v.get("total", 0) + 1
        if v.get("date") != today:
            v["date"] = today
            v["today"] = 1
        else:
            v["today"] = v.get("today", 0) + 1
        save_visits(v)
        return v

# ═══════════════ BOT PROCESS SUPERVISOR ═══════════════
PROCS = {}     # bot_id -> dict(proc, port, started, restarts, next_restart, status, ...)
API_USER_BOTS = {}  # (scope_key, browser_session_token) -> ephemeral bot; never persisted/admin-visible
API_USER_LOCK = threading.RLock()
_proc_lock = threading.RLock()

def _free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def _region_of(bot):
    if bot.get("region"):            # clone এর নিজস্ব bot এ region সরাসরি থাকে
        return bot["region"]
    for sv in load_servers():
        if sv["id"] == bot["server_id"]:
            return sv["region"]
    return "BD"

def _bot_scope_slug(bot_id):
    for rec, slug in all_bot_records():
        if rec.get("id") == bot_id: return slug
    return None

def _bot_auto_leave(bot):
    # Original bots use Original setting; clone-owned custom bots use that clone's setting.
    slug = _bot_scope_slug(bot.get("id", ""))
    cfg = site_config(Scope(slug) if slug else None)
    return bool(cfg.get("auto_leave", True))

def start_bot(bot):
    """একটা bot এর worker process চালু করে"""
    with _proc_lock:
        stop_bot(bot["id"], keep_entry=True)
        port = _free_port()
        env = os.environ.copy()
        env.update({
            "BOT_GUEST_UID": str(bot["uid"]), "BOT_GUEST_PW": str(bot["password"]),
            "BOT_REGION": _region_of(bot), "BOT_AUTO_LEAVE": "1" if _bot_auto_leave(bot) else "0", "WORKER_PORT": str(port),
            "PARENT_PID": str(os.getpid()), "PYTHONUNBUFFERED": "1",
        })
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.Popen([sys.executable, '-B', os.path.join(BASE_DIR, 'bot_worker.py')],
                                cwd=BASE_DIR, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)   # কোনো log ফাইল নয়
        old = PROCS.get(bot["id"], {})
        PROCS[bot["id"]] = {"proc": proc, "port": port, "started": time.time(),
                            "restarts": old.get("restarts", 0), "next_restart": 0,
                            "status": "connecting", "error": "", "bot_uid": None, "queue": 0,
                            "team_code": old.get("team_code"), "lease_started": old.get("lease_started"),
                            "lease_expires": old.get("lease_expires")}

def stop_bot(bot_id, keep_entry=False):
    with _proc_lock:
        info = PROCS.get(bot_id)
        if not info: return
        p = info.get("proc")
        if p and p.poll() is None:
            try:
                p.terminate()
                try: p.wait(timeout=4)
                except subprocess.TimeoutExpired: p.kill()
            except Exception: pass
        if not keep_entry:
            PROCS.pop(bot_id, None)

def _poll_status(info):
    try:
        r = requests.get(f"http://127.0.0.1:{info['port']}/api/status", timeout=1.5)
        d = r.json()
        raw_status = str(d.get("status", "offline")).lower()
        info["status"] = "online" if raw_status in ("online", "connected", "running", "success", "ready") else raw_status
        info["error"] = d.get("error", "")
        info["bot_uid"] = d.get("uid")
        info["queue"] = d.get("queue", 0)
    except Exception:
        # worker এখনো উঠছে, বা কিছু সময় সাড়া দিচ্ছে না
        if time.time() - info["started"] > 15:
            info["status"] = "offline"
            info["error"] = info.get("error") or "Worker সাড়া দিচ্ছে না"

# ═══════════════ CLONE (TENANT) HELPERS ═══════════════
MAX_TENANTS = int(os.environ.get("AX_MAX_CLONES", "200"))
MAX_BOTS_PER_TENANT = int(os.environ.get("AX_MAX_BOTS_PER_CLONE", "10"))
MAX_TOTAL_BOTS = int(os.environ.get("AX_MAX_TOTAL_BOTS", "80"))
RESERVED_SLUGS = {"static", "admin", "api", "join", "login", "logout", "script", "style", "clones", "clone", "romjan", "public"}

def tenant_active(t):
    if not t or not t.get("enabled", True): return False
    exp = t.get("expires_at", 0)
    return (not exp) or time.time() < exp

def tenant_runs_own_bots(t):
    return bool(t) and t.get("bot_mode") == "own" and tenant_active(t)

def all_bot_records():
    """(bot, tenant_slug|None) — সব bot (original + clone)"""
    with _store_lock:
        out = [(dict(b), None) for b in _MEM["bots"]]
        for slug, t in _MEM["tenants"].items():
            out += [(dict(b), slug) for b in t.get("bots", [])]
        return out

def allowed_bots():
    """Managed bots plus active browser-session API bots (ephemeral)."""
    res = []
    for b, slug in all_bot_records():
        if slug is None or tenant_runs_own_bots(_MEM["tenants"].get(slug)):
            res.append(b)
    with API_USER_LOCK:
        res.extend(dict(b) for b in API_USER_BOTS.values())
    return res

def find_bot_anywhere(bid):
    found = next((b for b, _ in all_bot_records() if b["id"] == bid), None)
    if found: return found
    with API_USER_LOCK:
        return next((dict(b) for b in API_USER_BOTS.values() if b["id"] == bid), None)

def all_guest_uids():
    return {b["uid"] for b, _ in all_bot_records()}

def total_bot_count():
    return len(all_bot_records())

def monitor_loop():
    while True:
        try:
            ids = {b["id"] for b in allowed_bots()}
            with _proc_lock:
                # ডিলিট/মেয়াদোত্তীর্ণ/বন্ধ করা bot এর process পরিষ্কার
                for bid in list(PROCS.keys()):
                    if bid not in ids: stop_bot(bid)
                for bid, info in list(PROCS.items()):
                    p = info["proc"]
                    if p.poll() is not None:     # process মারা গেছে
                        info["status"] = "offline"
                        info["error"] = f"Process crashed (exit {p.returncode}) — আবার চালু হচ্ছে"
                        if info["next_restart"] == 0:
                            info["restarts"] += 1
                            info["next_restart"] = time.time() + min(5 * info["restarts"], 60)
                        elif time.time() >= info["next_restart"]:
                            bot = find_bot_anywhere(bid)
                            if bot: start_bot(bot)
                    else:
                        _poll_status(info)
                        bot = find_bot_anywhere(bid)
                        if bot and bot.get("source") == "json":
                            if info.get("status") == "online" and not info.get("lease_started"):
                                info["lease_started"] = time.time()
                                info["lease_expires"] = info["lease_started"] + int(bot.get("lease_minutes", 10)) * 60
                            if info.get("lease_expires") and time.time() >= info["lease_expires"]:
                                _expire_json_bot(bid)
        except Exception as e:
            print("[monitor]", e)
        time.sleep(3)

def start_all_bots():
    for b in allowed_bots():
        if b.get("source") == "json": continue  # temporary 10-minute leases are not resumed after server restart
        try: start_bot(b)
        except Exception as e: print("[start_all]", e)
        time.sleep(2)   # login burst এড়াতে ধাপে ধাপে

def start_missing_bots_of(slug):
    """clone আবার active/own হলে তার bot গুলো ধাপে ধাপে চালু"""
    t = _MEM["tenants"].get(slug)
    if not tenant_runs_own_bots(t): return
    for b in [dict(x) for x in t.get("bots", [])]:
        if b["id"] not in PROCS:
            try: start_bot(b)
            except Exception as e: print("[start_missing]", e)
            time.sleep(2)

def bot_view(b, admin=False):
    info = PROCS.get(b["id"], {})
    st = info.get("status", "offline")
    d = {"id": b["id"], "name": b["name"], "server_id": b["server_id"],
         "status": "online" if st == "online" else ("offline" if not admin else st)}
    if admin:
        exp = info.get("lease_expires", 0)
        d.update({"uid": b["uid"], "bot_uid": info.get("bot_uid"), "error": info.get("error", ""),
                  "queue": info.get("queue", 0), "restarts": info.get("restarts", 0),
                  "source": b.get("source", "manual"), "team_code": info.get("team_code") or b.get("team_code", ""),
                  "remaining_seconds": max(0, int(exp-time.time())) if exp else None})
    return d

# ═══════════════ PUBLIC ROUTES ═══════════════
@app.route('/')
def index():
    record_visit()
    if site_config().get('maintenance') == 'on': return redirect('/maintenance')
    resp = send_from_directory(STATIC_DIR, 'index.html')
    resp.headers['Cache-Control'] = 'no-cache'
    return resp

@app.route('/style.css')
def css(): return send_from_directory(STATIC_DIR, 'style.css')

@app.route('/script.js')
def js():
    resp = send_from_directory(STATIC_DIR, 'script.js')
    resp.headers['Cache-Control'] = 'no-cache'
    return resp

def site_config(scope=None):
    if scope and scope.slug:
        t = scope.tenant or {}
        cfg = t.setdefault("site", {})
        cfg.setdefault("tasks", t.get("tasks", [])); cfg.setdefault("maintenance", "off"); cfg.setdefault("tasks_enabled", True)
        cfg.setdefault("notice", "এই ওয়েবসাইটটি সাময়িকভাবে বন্ধ আছে।"); cfg.setdefault("social_links", [])
        cfg.setdefault("auth_mode", "manual"); cfg.setdefault("api_name", "AX-ROM"); cfg.setdefault("api_urls", dict(DEFAULT_SITE_CONFIG["api_urls"])); cfg.setdefault("auto_leave", True)
        return cfg
    if _MEM.get("site") is None: _MEM["site"] = json.loads(json.dumps(DEFAULT_SITE_CONFIG))
    _MEM["site"].setdefault("tasks_enabled", True)
    _MEM["site"].setdefault("auth_mode", "manual"); _MEM["site"].setdefault("api_name", "AX-ROM"); _MEM["site"].setdefault("api_urls", dict(DEFAULT_SITE_CONFIG["api_urls"])); _MEM["site"].setdefault("auto_leave", True)
    return _MEM["site"]

def _effective_tasks(cfg):
    """টাস্ক OFF থাকলে (বা তালিকা খালি হলে) ইউজার সরাসরি Main UI পায়"""
    return (cfg.get("tasks", []) or []) if cfg.get("tasks_enabled", True) else []

def _public_site_settings(cfg):
    tasks = _effective_tasks(cfg); links = cfg.get("social_links", [])
    return {"maintenance": cfg.get("maintenance", "off"), "notice": cfg.get("notice", ""),
            "social_links": links, "telegram": (links or [{}])[0].get("link", ""), "no_tasks": len(tasks) == 0, "auth_mode": cfg.get("auth_mode", "manual")}

@app.route('/api/tasks')
def get_tasks(): return jsonify([{"id": x["id"], "name": _html.escape(x["name"]), "link": x["link"]} for x in _effective_tasks(site_config())])

@app.route('/api/settings')
def get_settings(): return jsonify(_public_site_settings(site_config()))

@app.route('/maintenance')
def original_maintenance():
    if site_config().get('maintenance') != 'on': return redirect('/')
    return _maintenance_page(site_config(), original=True)


@app.route('/api/visits')
def get_visits():
    v = load_visits()
    return jsonify({"total": v.get("total", 0), "today": v.get("today", 0)})

API_SAVE_LOCK = threading.Lock()
API_SAVE_LAST = {}
API_SAVE_ACTIVE = set()

def _effective_public_scope(scope=None):
    # Clone websites inherit Original Website login/API configuration.
    return Scope(None) if scope and scope.slug else (scope or Scope(None))

def _api_cookie_name(scope):
    return "ax_api_user" if not scope or not scope.slug else "ax_api_user_" + scope.slug

def _api_session_token(scope, create=False):
    name = _api_cookie_name(scope)
    token = request.cookies.get(name, "")
    if not token and create: token = secrets.token_urlsafe(32)
    return token

def _api_session_key(scope, token=None):
    return ((scope.key if scope else "main"), token or _api_session_token(scope))

def _api_bot_for_request(scope):
    token = _api_session_token(scope)
    if not token: return None
    with API_USER_LOCK:
        bot = API_USER_BOTS.get(_api_session_key(scope, token))
        return dict(bot) if bot else None

def _generate_api_account(scope, server_id):
    cfg = site_config(_effective_public_scope(scope))
    srv = next((x for x in scope.usable_servers() if x.get("id") == server_id), None)
    if not srv: return jsonify({"ok": False, "error": "সঠিক Server নির্বাচন করুন"}), 400
    if server_bot_mode(srv, _effective_public_scope(scope)) != "api": return jsonify({"ok": False, "error": "এই Server API mode-এ নেই"}), 400
    token = _api_session_token(scope, create=True)
    session_key = _api_session_key(scope, token)
    with API_USER_LOCK:
        current = API_USER_BOTS.get(session_key)
        if current:
            if current.get("server_id") == server_id:
                status = PROCS.get(current["id"], {}).get("status", "offline")
                resp = jsonify({"ok": True, "existing": True, "status": status, "server_id": server_id})
                if not request.cookies.get(_api_cookie_name(scope)): _set_api_cookie(resp, scope, token)
                return resp
            return jsonify({"ok": False, "error": "আগের Bot Logout করে নতুন Server চালু করুন"}), 409
    ip = _client_ip(); now = time.time()
    with API_SAVE_LOCK:
        if now - API_SAVE_LAST.get((session_key, ip), 0) < 8:
            return jsonify({"ok": False, "error": "কিছুক্ষণ পরে আবার চেষ্টা করুন"}), 429
        if session_key in API_SAVE_ACTIVE:
            return jsonify({"ok": False, "error": "Guest Account তৈরি হচ্ছে, একটু অপেক্ষা করুন"}), 409
        API_SAVE_LAST[(session_key, ip)] = now
        API_SAVE_ACTIVE.add(session_key)
    try:
        region = srv.get("region", "BD")
        api_url = srv.get("api_url") or (cfg.get("api_urls") or {}).get(region, "")
        if not api_url: return jsonify({"ok": False, "error": region + " API URL Admin Panel-এ সেট করা নেই"}), 400
        try:
            parts = urlsplit(api_url); q = dict(parse_qsl(parts.query, keep_blank_values=True))
            q.update({"server": region, "name": cfg.get("api_name", "AX-ROM")})
            target = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), ""))
            r = requests.get(target, timeout=20, allow_redirects=False, headers={"Accept": "application/json"})
            r.raise_for_status(); data = r.json()
            uid, pw = str(data.get("uid", "")), str(data.get("password", ""))
            if data.get("status") != "success" or not uid.isdigit() or not pw:
                return jsonify({"ok": False, "error": "API valid Guest UID/Password দেয়নি"}), 502
        except Exception as e:
            return jsonify({"ok": False, "error": "Account API failed: " + str(e)[:160]}), 502
        # This account is tied only to this browser session; it is never added to bot storage.
        bid = "api_" + secrets.token_hex(8)
        bot = {"id": bid, "name": str(data.get("nickname") or cfg.get("api_name", "API BOT"))[:30],
               "server_id": server_id, "region": region, "uid": uid, "password": pw,
               "created": int(time.time()), "source": "api_session"}
        with API_USER_LOCK:
            if API_USER_BOTS.get(session_key):
                return jsonify({"ok": False, "error": "এই Browser Session-এ ইতিমধ্যে Bot চালু আছে"}), 409
            if any(str(x.get("uid")) == uid for x in API_USER_BOTS.values()):
                return jsonify({"ok": False, "error": "API একই Guest UID অন্য একটি active session-এ দিয়েছে; নতুন account তৈরি করে আবার চেষ্টা করুন"}), 409
            API_USER_BOTS[session_key] = bot
        threading.Thread(target=start_bot, args=(dict(bot),), daemon=True).start()
        resp = jsonify({"ok": True, "existing": False, "status": "connecting", "server_id": server_id})
        if not request.cookies.get(_api_cookie_name(scope)): _set_api_cookie(resp, scope, token)
        return resp
    finally:
        with API_SAVE_LOCK: API_SAVE_ACTIVE.discard(session_key)

def _json_pool(scope=None):
    # Main website has separate account pools keyed by server ID.
    return _MEM.setdefault("json_accounts", {})

def _save_json_pool_file():
    if not JSON_POOL_FILE: return
    try:
        tmp = JSON_POOL_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_json_pool(), f, ensure_ascii=False)
        try: os.chmod(tmp, 0o600)
        except Exception: pass
        os.replace(tmp, JSON_POOL_FILE)
    except Exception as e:
        print("[json-pool-save]", e)

def _load_json_pool_file():
    if not JSON_POOL_FILE or not os.path.exists(JSON_POOL_FILE): return
    try:
        with open(JSON_POOL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict): _MEM["json_accounts"] = data
    except Exception as e:
        print("[json-pool-load]", e)

def _expire_json_bot(bot_id):
    bot = next((b for b, _ in all_bot_records() if b.get("id") == bot_id and b.get("source") == "json"), None)
    if not bot: return
    with API_USER_LOCK:
        for key, val in list(API_USER_BOTS.items()):
            if val.get("id") == bot_id: API_USER_BOTS.pop(key, None)
    with _store_lock:
        _MEM["bots"] = [b for b in _MEM["bots"] if b.get("id") != bot_id]
        _persist()
    stop_bot(bot_id)

def _start_json_account(scope, server_id):
    # Clone public sites inherit the Original Website category and consume the
    # Original Website's server-specific JSON pool; each browser scope gets its
    # own session cookie and active lease.
    public_scope = _effective_public_scope(scope)
    srv = next((x for x in load_servers() if x.get("id") == server_id), None)
    if not srv: return jsonify({"ok": False, "error": "সঠিক Server নির্বাচন করুন"}), 400
    if server_bot_mode(srv, public_scope) != "json":
        return jsonify({"ok": False, "error": "Original Website JSON mode-এ নেই"}), 400
    token = _api_session_token(scope, create=True); skey = _api_session_key(scope, token)
    with API_USER_LOCK:
        existing = API_USER_BOTS.get(skey)
        if existing:
            return jsonify({"ok": True, "existing": True, "status": PROCS.get(existing["id"], {}).get("status", "connecting"), "server_id": server_id})
    with _store_lock:
        pool = _json_pool().get(server_id, [])
        active_uids = {str(b.get("uid")) for b in _MEM["bots"] if b.get("source") == "json"}
        account = next((a for a in pool if str(a.get("uid")) not in active_uids), None)
        if not account: return jsonify({"ok": False, "error": "এই Server-এর JSON pool-এ available account নেই"}), 409
        bot = {"id": "json_" + secrets.token_hex(8), "name": str(account.get("name") or "JSON BOT")[:30],
               "server_id": server_id, "region": srv.get("region", "BD"), "uid": str(account["uid"]),
               "password": str(account["password"]), "source": "json", "lease_minutes": 10,
               "team_code": "", "created": int(time.time()), "session_key": skey,
               "started_from_scope": scope.key}
        _MEM["bots"].append(bot); _persist()
    with API_USER_LOCK: API_USER_BOTS[skey] = bot
    threading.Thread(target=start_bot, args=(dict(bot),), daemon=True).start()
    resp = jsonify({"ok": True, "status": "connecting", "server_id": server_id})
    if not request.cookies.get(_api_cookie_name(scope)): _set_api_cookie(resp, scope, token)
    return resp

def _set_api_cookie(resp, scope, token):
    secure = request.is_secure or request.headers.get("X-Forwarded-Proto") == "https"
    resp.set_cookie(_api_cookie_name(scope), token, max_age=30 * 24 * 3600, httponly=True,
                    samesite="Lax", secure=secure, path="/" if not scope or not scope.slug else "/" + scope.slug)

def _api_status_response(scope):
    bot = _api_bot_for_request(scope)
    if not bot: return jsonify({"active": False, "status": "not_running"})
    info = PROCS.get(bot["id"], {})
    return jsonify({"active": True, "server_id": bot["server_id"],
                    "status": info.get("status", "connecting"), "error": info.get("error", ""),
                    "bot_uid": info.get("bot_uid")})

def _api_logout(scope):
    token = _api_session_token(scope)
    if token:
        key = _api_session_key(scope, token)
        with API_USER_LOCK: bot = API_USER_BOTS.pop(key, None)
        if bot:
            if bot.get("source") == "json": _expire_json_bot(bot["id"])
            else: stop_bot(bot["id"])
    resp = jsonify({"ok": True, "active": False})
    resp.delete_cookie(_api_cookie_name(scope), path="/" if not scope or not scope.slug else "/" + scope.slug)
    return resp

@app.route('/api/runtime-config')
def api_runtime_config():
    modes = {s["id"]: server_bot_mode(s) for s in load_servers()}
    return jsonify({"auth_mode": site_config().get("auth_mode", "manual"), "server_modes": modes})

@app.route('/api/save-server', methods=['POST'])
def api_save_server():
    d = request.get_json(silent=True) or {}; sid = _clean(d.get("server_id"), 20)
    srv = next((x for x in load_servers() if x.get("id") == sid), None)
    if not srv: return jsonify({"ok": False, "error": "সঠিক Server নির্বাচন করুন"}), 400
    mode = server_bot_mode(srv)
    if mode == "json": return _start_json_account(Scope(None), sid)
    if mode == "api": return _generate_api_account(Scope(None), sid)
    return jsonify({"ok": False, "error": "এই Server Manual mode-এ আছে; Admin থেকে Manual Bot সিলেক্ট করুন"}), 400

@app.route('/api/my-bot')
def api_my_bot(): return _api_status_response(Scope(None))

@app.route('/api/logout-bot', methods=['POST'])
def api_logout_bot(): return _api_logout(Scope(None))

@app.route('/api/servers')
def api_servers():
    bots = load_bots(); out = []
    for s in load_servers():
        mine = [b for b in bots if b["server_id"] == s["id"]]
        online = sum(1 for b in mine if PROCS.get(b["id"], {}).get("status") == "online")
        out.append({"id": s["id"], "name": s["name"], "total": len(mine), "online": online,
                    "mode": server_bot_mode(s), "json_available": max(0, len(_json_pool().get(s["id"], [])) - sum(1 for b in _MEM["bots"] if b.get("source") == "json" and b.get("server_id") == s["id"]))})
    return jsonify(out)

@app.route('/api/bots')
def api_bots():
    sid = request.args.get('server')
    return jsonify([bot_view(b) for b in load_bots() if b["server_id"] == sid])

def _proxy_join(bot):
    bot_id = bot["id"] if bot else None
    if not bot:
        return jsonify({"status": "error", "message": "Bot not found (হয়তো ডিলিট করা হয়েছে)"}), 404
    info = PROCS.get(bot_id)
    if not info or info.get("status") != "online":
        return jsonify({"status": "error", "message": "Bot is offline"}), 503
    params = {k: v for k, v in request.args.items() if k != 'bot'}
    team_code = str(params.get("tc", "")).strip()
    if team_code:
        with _proc_lock:
            for other_id, other in PROCS.items():
                if other_id != bot_id and other.get("team_code") == team_code and other.get("status") == "online":
                    return jsonify({"status": "error", "message": "এই Team Code-এ অন্য Bot ইতিমধ্যে চলছে"}), 409
            info["team_code"] = team_code
            if bot.get("source") == "json":
                with _store_lock:
                    for rec in _MEM["bots"]:
                        if rec.get("id") == bot_id: rec["team_code"] = team_code
                    _persist()
    try:
        r = requests.get(f"http://127.0.0.1:{info['port']}/join", params=params, timeout=10)
        return (r.text, r.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Bot unreachable: {e}"}), 502

@app.route('/join')
def join_proxy():
    bot_id = request.args.get('bot')
    if bot_id: bot = next((b for b in load_bots() if b["id"] == bot_id), None)
    elif request.args.get("server"):
        sid = request.args.get("server")
        srv = next((x for x in load_servers() if x.get("id") == sid), None)
        bot = _api_bot_for_request(Scope(None)) if srv and server_bot_mode(srv) in ("api", "json") else None
        if bot and bot.get("server_id") != sid: bot = None
    else: bot = None
    return _proxy_join(bot)

# ═══════════════ SCOPES (main admin / clone admin একই কোড, আলাদা data) ═══════════════
class Scope:
    def __init__(self, slug=None):
        self.slug = slug
    @property
    def key(self): return self.slug or 'main'
    @property
    def tenant(self): return _MEM["tenants"].get(self.slug) if self.slug else None
    @property
    def cookie_name(self): return 'axa' if not self.slug else 'axa_' + self.slug
    @property
    def cookie_path(self): return '/' if not self.slug else '/' + self.slug
    def is_shared(self):
        t = self.tenant
        return bool(t and t.get("bot_mode") == "shared")
    # --- managed (admin panel) data ---
    def servers(self):
        if not self.slug: return load_servers()
        t = self.tenant
        return [dict(x) for x in t.get("servers", [])] if t and not self.is_shared() else []
    def save_servers(self, lst):
        if not self.slug: return save_servers(lst)
        with _store_lock:
            self.tenant["servers"] = lst; _persist()
    def bots(self):
        if not self.slug: return load_bots()
        t = self.tenant
        return [dict(x) for x in t.get("bots", [])] if t and not self.is_shared() else []
    def save_bots(self, lst):
        if not self.slug: return save_bots(lst)
        with _store_lock:
            self.tenant["bots"] = lst; _persist()
    # --- public user site data ---
    def usable_servers(self):
        return load_servers() if (not self.slug or self.is_shared()) else self.servers()
    def usable_bots(self):
        return load_bots() if (not self.slug or self.is_shared()) else self.bots()
    def check_password(self, pw):
        if not self.slug: return _check_password(pw)
        t = self.tenant
        if not t: return False
        return hmac.compare_digest(_pw_hash(pw, bytes.fromhex(t["pw_salt"])), t["pw_hash"])

def _clone_scope(slug):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,38}[a-z0-9]', slug or ''): return None
    return Scope(slug) if slug in _MEM["tenants"] else None

def _scope_is_admin(scope):
    tok = request.cookies.get(scope.cookie_name)
    with _auth_lock:
        v = SESSIONS.get(tok)
        if v and v[0] == scope.key and v[1] > time.time():
            return True
        SESSIONS.pop(tok, None)
    return False

def _unauth():
    return jsonify({"ok": False, "error": "unauthorized"}), 401

def _no_store(resp):
    resp.headers['Cache-Control'] = 'no-store'
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return resp

def _clean(s, n): return (s or '').strip()[:n]

def _new_session(scope):
    tok = secrets.token_urlsafe(32)
    with _auth_lock:
        SESSIONS[tok] = (scope.key, time.time() + SESSION_TTL)
    return tok

def _set_cookie(resp, scope, tok):
    secure = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
    resp.set_cookie(scope.cookie_name, tok, max_age=SESSION_TTL, httponly=True,
                    samesite='Strict', secure=secure, path=scope.cookie_path)

# ═══════════════ GENERIC ADMIN HANDLERS (scope = main বা clone) ═══════════════
def h_admin_page(scope):
    return _no_store(send_from_directory(STATIC_DIR, 'admin.html'))

def h_login(scope):
    ip = _client_ip(); now = time.time(); fkey = f"{scope.key}|{ip}"
    if scope.slug and not tenant_active(scope.tenant):
        return jsonify({"ok": False, "error": "এই ওয়েবসাইটের মেয়াদ শেষ / বন্ধ আছে"}), 403
    with _auth_lock:
        cnt, lock_until = FAILS.get(fkey, (0, 0))
        if lock_until > now:
            return jsonify({"ok": False, "error": f"অনেকবার ভুল। {int(lock_until-now)} সেকেন্ড পরে চেষ্টা করুন"}), 429
    pw = (request.get_json(silent=True) or {}).get('password', '')
    if scope.check_password(pw):
        with _auth_lock: FAILS.pop(fkey, None)
        tok = _new_session(scope)
        resp = jsonify({"ok": True}); _set_cookie(resp, scope, tok)
        return _no_store(resp)
    with _auth_lock:
        cnt += 1
        FAILS[fkey] = (cnt, now + 300 if cnt >= 5 else 0)
    time.sleep(0.8)
    return jsonify({"ok": False, "error": "ভুল পাসওয়ার্ড"}), 401

def h_logout(scope):
    with _auth_lock: SESSIONS.pop(request.cookies.get(scope.cookie_name), None)
    resp = jsonify({"ok": True}); resp.delete_cookie(scope.cookie_name, path=scope.cookie_path); return resp

def h_site_config(scope):
    if not _scope_is_admin(scope): return _unauth()
    return _no_store(jsonify({"ok": True, **site_config(scope)}))

def h_update_site_config(scope):
    """শুধু যে key গুলো পাঠানো হয় সেগুলোই বদলায় (partial update)"""
    if not _scope_is_admin(scope): return _unauth()
    d = request.get_json(silent=True) or {}
    tasks = links = None
    if "tasks" in d:
        tasks, err = _clean_tasks(d.get("tasks", []))
        if err: return jsonify({"ok": False, "error": err}), 400
    if "social_links" in d:
        links, err = _clean_tasks(d.get("social_links", []))
        if err: return jsonify({"ok": False, "error": err}), 400
    auto_leave_changed = False
    with _store_lock:
        cfg = site_config(scope)
        old_auto_leave = bool(cfg.get("auto_leave", True))
        if tasks is not None:
            cfg["tasks"] = tasks
            if scope.slug: scope.tenant["tasks"] = tasks
        if links is not None: cfg["social_links"] = links
        if "tasks_enabled" in d: cfg["tasks_enabled"] = bool(d.get("tasks_enabled"))
        if "maintenance" in d: cfg["maintenance"] = "on" if d.get("maintenance") else "off"
        if "notice" in d:
            cfg["notice"] = _clean(d.get("notice"), 1200) or "ওয়েবসাইটে সাময়িক রক্ষণাবেক্ষণের কাজ চলছে।"
        if "auth_mode" in d:
            mode = str(d.get("auth_mode") or "manual").lower()
            if mode not in ("manual", "api", "json"): return jsonify({"ok": False, "error": "Login mode ভুল"}), 400
            cfg["auth_mode"] = mode
        if "api_name" in d: cfg["api_name"] = _clean(d.get("api_name"), 40) or "AX-ROM"
        if "api_urls" in d:
            urls = d.get("api_urls") or {}; clean_urls = dict(cfg.get("api_urls", DEFAULT_SITE_CONFIG["api_urls"]))
            for region in ("BD", "IND"):
                val = _clean(urls.get(region), 500) if isinstance(urls, dict) else ""
                if val:
                    parts = urlsplit(val)
                    if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
                        return jsonify({"ok": False, "error": region + " API URL অবশ্যই HTTPS হতে হবে"}), 400
                    clean_urls[region] = val
            cfg["api_urls"] = clean_urls
        if "auto_leave" in d: cfg["auto_leave"] = bool(d.get("auto_leave"))
        auto_leave_changed = old_auto_leave != bool(cfg.get("auto_leave", True))
        _persist()
    if auto_leave_changed:
        records = all_bot_records() if not scope.slug else [(b, scope.slug) for b in scope.bots()]
        for b, _slug in records: threading.Thread(target=start_bot, args=(dict(b),), daemon=True).start()
        if not scope.slug:
            with API_USER_LOCK: api_records = [dict(b) for b in API_USER_BOTS.values()]
            for b in api_records: threading.Thread(target=start_bot, args=(b,), daemon=True).start()
    return jsonify({"ok": True, "site": site_config(scope)})

@app.route(ADMIN_PATH + '/api/password-change', methods=['POST'])
def admin_change_password():
    scope = Scope(None)
    if not _scope_is_admin(scope): return _unauth()
    if os.environ.get("ADMIN_PASSWORD"):
        return jsonify({"ok": False, "error": "Hosting-এর ADMIN_PASSWORD environment variable থেকে password নিয়ন্ত্রিত হচ্ছে। সেখানে পরিবর্তন করুন।"}), 400
    d = request.get_json(silent=True) or {}
    current = str(d.get("current_password") or "")
    new = str(d.get("new_password") or "")
    confirm = str(d.get("confirm_password") or "")
    if not _check_password(current): return jsonify({"ok": False, "error": "বর্তমান Admin Password সঠিক নয়"}), 400
    if len(new) < 8 or len(new) > 128: return jsonify({"ok": False, "error": "নতুন Password কমপক্ষে ৮ এবং সর্বোচ্চ ১২৮ অক্ষরের হতে হবে"}), 400
    if new != confirm: return jsonify({"ok": False, "error": "নতুন Password ও Confirm Password মিলছে না"}), 400
    with _store_lock:
        cfg = site_config()
        cfg["admin_password_hash"] = _pw_hash(new)
        _persist()
    current_token = request.cookies.get(scope.cookie_name)
    with _auth_lock:
        for token, value in list(SESSIONS.items()):
            if value[0] == "main" and token != current_token:
                SESSIONS.pop(token, None)
    return jsonify({"ok": True, "message": "Admin Password সফলভাবে পরিবর্তন হয়েছে"})

def h_state(scope):
    if not _scope_is_admin(scope): return _unauth()
    d = {"ok": True, "regions": REGIONS, "site": site_config(scope), "servers": scope.servers(),
         "bots": [bot_view(b, True) for b in scope.bots()],
         "public_auth_mode": (site_config(Scope(None)).get("auth_mode", "manual") if (not scope.slug or scope.is_shared()) else "manual"),
         "scope": "clone" if scope.slug else "main", "shared": scope.is_shared()}
    # JSON pool inventory is private to the Original Website admin only.
    if not scope.slug:
        d["json_pool_counts"] = {sid: {"total": len(items), "active": sum(1 for b in _MEM["bots"] if b.get("source") == "json" and b.get("server_id") == sid), "available": max(0, len(items)-sum(1 for b in _MEM["bots"] if b.get("source") == "json" and b.get("server_id") == sid))} for sid, items in _json_pool().items()}
    if scope.slug:
        t = scope.tenant
        d.update({"clone_name": t["name"], "expires_at": t.get("expires_at", 0), "active": tenant_active(t)})
    return _no_store(jsonify(d))

def _shared_block(scope):
    if scope.is_shared():
        return jsonify({"ok": False, "error": "এই ওয়েবসাইট অরিজিনাল সার্ভারের bot ব্যবহার করছে — আলাদা bot যোগ করা যাবে না"}), 400
    return None

def h_add_server(scope):
    if not _scope_is_admin(scope): return _unauth()
    blk = _shared_block(scope)
    if blk: return blk
    d = request.get_json(silent=True) or {}
    name, region = _clean(d.get('name'), 40), _clean(d.get('region'), 8).upper()
    if not name or region not in REGION_CODES:
        return jsonify({"ok": False, "error": "সার্ভারের নাম ও region দিন"}), 400
    with _store_lock:
        servers = scope.servers()
        servers.append({"id": "s" + secrets.token_hex(3), "name": name, "region": region})
        scope.save_servers(servers)
    return jsonify({"ok": True})

def h_del_server(scope, sid):
    if not _scope_is_admin(scope): return _unauth()
    with _store_lock:
        if any(b["server_id"] == sid for b in scope.bots()):
            return jsonify({"ok": False, "error": "এই সার্ভারে bot আছে — আগে bot ডিলেট করুন"}), 400
        scope.save_servers([s for s in scope.servers() if s["id"] != sid])
    return jsonify({"ok": True})

def _limits_error(scope):
    if total_bot_count() >= MAX_TOTAL_BOTS:
        return jsonify({"ok": False, "error": f"সার্ভারে মোট bot সীমা ({MAX_TOTAL_BOTS}) পূর্ণ"}), 400
    if scope.slug and len(scope.bots()) >= MAX_BOTS_PER_TENANT:
        return jsonify({"ok": False, "error": f"এই ওয়েবসাইটে সর্বোচ্চ {MAX_BOTS_PER_TENANT}টি bot যোগ করা যাবে"}), 400
    return None

def h_add_bot(scope):
    if not _scope_is_admin(scope): return _unauth()
    blk = _shared_block(scope)
    if blk: return blk
    d = request.get_json(silent=True) or {}
    name, uid, pw = _clean(d.get('name'), 30), _clean(d.get('uid'), 24), _clean(d.get('password'), 200)
    sid = _clean(d.get('server_id'), 20)
    if not name or not uid.isdigit() or not pw:
        return jsonify({"ok": False, "error": "নাম, সঠিক Guest UID (শুধু সংখ্যা) ও Password দিন"}), 400
    srv = next((s for s in scope.servers() if s["id"] == sid), None)
    if not srv:
        return jsonify({"ok": False, "error": "সার্ভার সিলেক্ট করুন"}), 400
    with _store_lock:
        lim = _limits_error(scope)
        if lim: return lim
        if uid in all_guest_uids():       # একই guest account দুই জায়গায় চালালে একে অপরকে kick করে
            return jsonify({"ok": False, "error": "এই Guest UID আগে থেকেই যোগ করা আছে"}), 400
        used = {b["id"] for b, _ in all_bot_records()}
        bid = secrets.token_hex(4)
        while bid in used: bid = secrets.token_hex(4)
        bot = {"id": bid, "name": name, "server_id": sid, "uid": uid,
               "password": pw, "created": int(time.time())}
        if scope.slug: bot["region"] = srv["region"]
        bots = scope.bots(); bots.append(bot); scope.save_bots(bots)
    threading.Thread(target=start_bot, args=(dict(bot),), daemon=True).start()
    return jsonify({"ok": True, "id": bot["id"]})

def h_edit_bot(scope, bid):
    if not _scope_is_admin(scope): return _unauth()
    d = request.get_json(silent=True) or {}
    with _store_lock:
        bots = scope.bots(); bot = next((b for b in bots if b["id"] == bid), None)
        if not bot: return jsonify({"ok": False, "error": "Bot পাওয়া যায়নি"}), 404
        original_uid = str(bot.get("uid", ""))
        if d.get('name') is not None and _clean(d['name'], 30): bot["name"] = _clean(d['name'], 30)
        sv = next((s for s in scope.servers() if s["id"] == d.get('server_id')), None) if d.get('server_id') else None
        if sv:
            bot["server_id"] = sv["id"]
            if scope.slug: bot["region"] = sv["region"]
        if d.get('uid'):
            u = _clean(d['uid'], 24)
            if not u.isdigit(): return jsonify({"ok": False, "error": "Guest UID শুধু সংখ্যা হবে"}), 400
            if any(b2["uid"] == u and b2["id"] != bid for b2, _ in all_bot_records()):
                return jsonify({"ok": False, "error": "এই UID অন্য bot এ আছে"}), 400
            bot["uid"] = u
        if d.get('password'): bot["password"] = _clean(d['password'], 200)
        if bot.get("source") == "json" and not scope.slug:
            for acc in _json_pool().get(bot["server_id"], []):
                if str(acc.get("uid")) == original_uid:
                    acc["uid"] = bot["uid"]; acc["password"] = bot["password"]; acc["name"] = bot["name"]
                    break
            _save_json_pool_file()
        scope.save_bots(bots); _persist()
    threading.Thread(target=start_bot, args=(dict(bot),), daemon=True).start()   # নতুন তথ্য দিয়ে restart
    return jsonify({"ok": True})

def h_restart_bot(scope, bid):
    if not _scope_is_admin(scope): return _unauth()
    bot = next((b for b in scope.bots() if b["id"] == bid), None)
    if not bot: return jsonify({"ok": False, "error": "Bot পাওয়া যায়নি"}), 404
    with _proc_lock:
        if bid in PROCS: PROCS[bid]["restarts"] = 0
    threading.Thread(target=start_bot, args=(dict(bot),), daemon=True).start()
    return jsonify({"ok": True})

def h_del_bot(scope, bid):
    if not _scope_is_admin(scope): return _unauth()
    with _store_lock:
        bots = scope.bots()
        if not any(b["id"] == bid for b in bots):
            return jsonify({"ok": False, "error": "Bot পাওয়া যায়নি"}), 404
        scope.save_bots([b for b in bots if b["id"] != bid])      # data থেকে একেবারে মুছে যায়
    with API_USER_LOCK:
        for key, val in list(API_USER_BOTS.items()):
            if val.get("id") == bid: API_USER_BOTS.pop(key, None)
    stop_bot(bid)                                                 # process বন্ধ
    return jsonify({"ok": True})

def h_export(scope):
    if not _scope_is_admin(scope): return _unauth()
    payload = {"servers": scope.servers(), "bots": scope.bots()}
    if not scope.slug: payload["json_accounts"] = _json_pool()
    return _no_store(jsonify(payload))

def h_import(scope):
    if not _scope_is_admin(scope): return _unauth()
    blk = _shared_block(scope)
    if blk: return blk
    d = request.get_json(silent=True) or {}
    servers, bots = d.get("servers"), d.get("bots")
    if not isinstance(servers, list) or not isinstance(bots, list):
        return jsonify({"ok": False, "error": "ভুল ফরম্যাট"}), 400
    ok_srv = [s for s in servers if isinstance(s, dict) and s.get("id") and s.get("name") and s.get("region") in REGION_CODES]
    srv_by_id = {s["id"]: s for s in ok_srv}
    # অন্য scope এর UID/ID এর সাথে সংঘর্ষ এড়াতে
    mine_ids = {b["id"] for b in scope.bots()}
    other_uids = {b["uid"] for b, sl in all_bot_records() if sl != scope.slug}
    other_ids = {b["id"] for b, sl in all_bot_records() if sl != scope.slug}
    seen, ok_bots = set(), []
    for b in bots:
        if not isinstance(b, dict): continue
        uid, pw, nm = str(b.get("uid", "")), str(b.get("password", "")), str(b.get("name", ""))[:30]
        if not uid.isdigit() or not pw or not nm or b.get("server_id") not in srv_by_id: continue
        if uid in seen or uid in other_uids: continue
        bid = str(b.get("id") or secrets.token_hex(4))
        if bid in other_ids or bid in {x["id"] for x in ok_bots}: bid = secrets.token_hex(4)
        seen.add(uid)
        rec = {"id": bid, "name": nm, "server_id": b["server_id"], "uid": uid, "password": pw, "created": int(time.time())}
        if b.get("source") == "api": rec["source"] = "api"
        if scope.slug: rec["region"] = srv_by_id[b["server_id"]]["region"]
        ok_bots.append(rec)
    if not ok_srv:
        return jsonify({"ok": False, "error": "কোনো valid সার্ভার নেই"}), 400
    if scope.slug and len(ok_bots) > MAX_BOTS_PER_TENANT:
        return jsonify({"ok": False, "error": f"সর্বোচ্চ {MAX_BOTS_PER_TENANT}টি bot"}), 400
    with _store_lock:
        scope.save_servers(ok_srv); scope.save_bots(ok_bots)
        if not scope.slug and isinstance(d.get("json_accounts"), dict):
            clean_pool = {}
            for sid, items in d.get("json_accounts", {}).items():
                if sid not in srv_by_id or not isinstance(items, list): continue
                seen_pool=set(); rows=[]
                for a in items:
                    if not isinstance(a, dict): continue
                    auid=str(a.get("uid", "")).strip(); apw=str(a.get("password", "")).strip()
                    if auid.isdigit() and apw and auid not in seen_pool:
                        rows.append({"uid":auid,"password":apw,"name":str(a.get("name") or "JSON BOT")[:30]}); seen_pool.add(auid)
                clean_pool[sid]=rows
            _MEM["json_accounts"] = clean_pool
            _save_json_pool_file()
        _persist()
    def _restart_scope():
        for bid in mine_ids: stop_bot(bid)          # শুধু এই scope এর bot — অন্য কারো নয়
        for b in ok_bots:
            start_bot(b); time.sleep(2)
    threading.Thread(target=_restart_scope, daemon=True).start()
    return jsonify({"ok": True, "servers": len(ok_srv), "bots": len(ok_bots)})

# ─────────── route registration (main + clone) ───────────
def _register_admin(rule_suffix, handler, methods=('GET',), ep=None):
    ep = ep or handler.__name__ + rule_suffix.replace('/', '_').replace('<', '').replace('>', '')
    def main_view(*a, **k): return handler(Scope(None), *a, **k)
    def clone_view(slug, *a, **k):
        sc = _clone_scope(slug)
        if not sc: return jsonify({"ok": False, "error": "not found"}), 404
        return handler(sc, *a, **k)
    app.add_url_rule(ADMIN_PATH + rule_suffix, 'main_' + ep, main_view, methods=list(methods))
    app.add_url_rule('/<slug>/admin' + rule_suffix, 'clone_' + ep, clone_view, methods=list(methods))

_register_admin('', h_admin_page, ('GET',), 'page')
_register_admin('/', h_admin_page, ('GET',), 'page_slash')
_register_admin('/api/login', h_login, ('POST',))
_register_admin('/api/logout', h_logout, ('POST',))
_register_admin('/api/state', h_state)
_register_admin('/api/site', h_site_config)
_register_admin('/api/site', h_update_site_config, ('PUT',), 'update_site')
_register_admin('/api/servers', h_add_server, ('POST',))
_register_admin('/api/servers/<sid>', h_del_server, ('DELETE',))
@app.route(ADMIN_PATH + '/api/servers/<sid>/mode', methods=['PUT'])
def admin_server_mode(sid):
    if not _scope_is_admin(Scope(None)): return _unauth()
    d=request.get_json(silent=True) or {}; mode=str(d.get("mode") or "manual").lower()
    if mode not in ("manual","api","json"): return jsonify({"ok":False,"error":"Mode ভুল"}),400
    with _store_lock:
        servers=load_servers(); srv=next((x for x in servers if x.get("id")==sid),None)
        if not srv: return jsonify({"ok":False,"error":"Server পাওয়া যায়নি"}),404
        srv["bot_mode"]=mode
        if "auto_leave" in d: srv["auto_leave"] = bool(d.get("auto_leave"))
        save_servers(servers)
    # Setting বদলালে ঐ server-এর চলমান bot নতুন worker env-এ restart হবে।
    if "auto_leave" in d:
        for b in [x for x in load_bots() if x.get("server_id") == sid]:
            threading.Thread(target=start_bot, args=(dict(b),), daemon=True).start()
    return jsonify({"ok":True,"mode":mode,"auto_leave":srv.get("auto_leave", True)})

@app.route(ADMIN_PATH + '/api/servers/<sid>/api-config', methods=['PUT'])
def admin_server_api_config(sid):
    if not _scope_is_admin(Scope(None)): return _unauth()
    d = request.get_json(silent=True) or {}
    val = _clean(d.get("api_url"), 1000)
    if val:
        parts = urlsplit(val)
        if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
            return jsonify({"ok": False, "error": "API URL অবশ্যই HTTPS হতে হবে"}), 400
    with _store_lock:
        servers = load_servers(); srv = next((x for x in servers if x.get("id") == sid), None)
        if not srv: return jsonify({"ok": False, "error": "Server পাওয়া যায়নি"}), 404
        srv["api_url"] = val
        save_servers(servers)
    return jsonify({"ok": True, "api_url_saved": bool(val)})

_register_admin('/api/bots', h_add_bot, ('POST',))
_register_admin('/api/bots/<bid>', h_edit_bot, ('PUT',), 'edit_bot')
_register_admin('/api/bots/<bid>', h_del_bot, ('DELETE',), 'del_bot')
_register_admin('/api/bots/<bid>/restart', h_restart_bot, ('POST',))
@app.route(ADMIN_PATH + '/api/json-accounts', methods=['POST'])
def admin_upload_json_accounts():
    if not _scope_is_admin(Scope(None)): return _unauth()
    d = request.get_json(silent=True) or {}; sid = _clean(d.get("server_id"), 20); accounts = d.get("accounts")
    srv = next((x for x in load_servers() if x.get("id") == sid), None)
    if not srv or not isinstance(accounts, list): return jsonify({"ok": False, "error": "Server এবং accounts array দিন"}), 400
    clean=[]; seen=set()
    for a in accounts:
        if not isinstance(a, dict): continue
        uid=str(a.get("uid", "")).strip(); pw=str(a.get("password", "")).strip(); name=str(a.get("name") or "JSON BOT")[:30]
        if uid.isdigit() and pw and uid not in seen:
            clean.append({"uid":uid,"password":pw,"name":name}); seen.add(uid)
    if not clean: return jsonify({"ok":False,"error":"Valid UID/Password account পাওয়া যায়নি"}),400
    with _store_lock:
        _json_pool()[sid]=clean; _persist(); _save_json_pool_file()
    return jsonify({"ok":True,"count":len(clean)})

@app.route(ADMIN_PATH + '/api/json-bots/bulk', methods=['POST'])
def admin_json_bulk():
    if not _scope_is_admin(Scope(None)): return _unauth()
    d=request.get_json(silent=True) or {}; action=d.get("action")
    ids=[b.get("id") for b in _MEM["bots"] if b.get("source")=="json"]
    if action not in ("restart","delete"): return jsonify({"ok":False,"error":"Action ভুল"}),400
    if action == "delete":
        for bid in ids: _expire_json_bot(bid)
        return jsonify({"ok":True,"count":len(ids)})
    for bid in ids:
        b=next((x for x in _MEM["bots"] if x.get("id")==bid),None)
        if b:
            info=PROCS.get(bid,{})
            if info.get("lease_expires") and time.time() >= info["lease_expires"]: _expire_json_bot(bid)
            else: threading.Thread(target=start_bot,args=(dict(b),),daemon=True).start()
    return jsonify({"ok":True,"count":len(ids)})

@app.route(ADMIN_PATH + '/api/json-accounts/<sid>', methods=['GET','DELETE'])
def admin_json_accounts(sid):
    if not _scope_is_admin(Scope(None)): return _unauth()
    with _store_lock:
        items=_json_pool().get(sid, [])
        if request.method=='DELETE':
            if any(b.get("source")=="json" and b.get("server_id")==sid for b in _MEM["bots"]): return jsonify({"ok":False,"error":"এই Server-এ JSON bot active আছে"}),409
            _json_pool().pop(sid,None); _persist(); _save_json_pool_file(); return jsonify({"ok":True})
        active=sum(1 for b in _MEM["bots"] if b.get("source")=="json" and b.get("server_id")==sid)
        return jsonify({"total":len(items),"active":active,"available":max(0,len(items)-active)})

_register_admin('/api/export', h_export)
_register_admin('/api/import', h_import, ('POST',))

# ═══════════════ CLONE MANAGEMENT (শুধু main admin) ═══════════════
def _main_ok(): return _scope_is_admin(Scope(None))

def _clean_slug(raw):
    slug = str(raw or '').strip().lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,38}[a-z0-9]', slug):
        return None, 'URL ২–৪০ অক্ষরের lowercase letter/number এবং মাঝখানে hyphen দিয়ে দিন'
    reserved = set(RESERVED_SLUGS) | {ADMIN_PATH.strip('/').split('/')[0]}
    if slug in reserved:
        return None, 'এই URL ব্যবহার করা যাবে না'
    return slug, None

def _gen_slug():
    letters = 'abcdefghijklmnopqrstuvwxyz'
    for _ in range(500):
        n = 5 + secrets.randbelow(3)                       # ৫–৭ অক্ষর
        slug = ''.join(secrets.choice(letters) for _ in range(n))
        if slug not in _MEM["tenants"] and slug not in RESERVED_SLUGS:
            return slug
    return None

_LINK_RE = re.compile(r"^https?://[^\s'\"<>\\]{3,300}$")

def _clean_tasks(raw):
    """[{name, link}] → validated list; ভুল হলে (None, error)"""
    if raw in (None, ''): return [], None
    if not isinstance(raw, list) or len(raw) > 8:
        return None, "সর্বোচ্চ ৮টি টাস্ক দেওয়া যাবে"
    out = []
    for i, t in enumerate(raw):
        if not isinstance(t, dict): continue
        name, link = _clean(t.get('name'), 40), _clean(t.get('link'), 300)
        if not name and not link: continue
        if not name or not _LINK_RE.match(link):
            return None, f"টাস্ক {i+1}: নাম ও সঠিক লিংক (https://...) দিন"
        tid = "t" + hashlib.sha1((name + "|" + link).encode("utf-8")).hexdigest()[:8]
        if any(x["id"] == tid for x in out): continue          # একই নাম+লিংক দুইবার নয়
        out.append({"id": tid, "name": name, "link": link})
    return out, None

def _expiry_from_days(days):
    try: days = float(days)
    except Exception: return None
    if days <= 0: return 0
    return int(time.time() + days * 86400)

def tenant_view(slug, t):
    exp = t.get("expires_at", 0)
    own = [b for b in t.get("bots", [])]
    online = sum(1 for b in own if PROCS.get(b["id"], {}).get("status") == "online")
    return {"slug": slug, "name": t["name"], "tasks": t.get("tasks", []), "site": t.get("site", {}), "bot_mode": t["bot_mode"],
            "enabled": t.get("enabled", True), "active": tenant_active(t), "created": t.get("created", 0),
            "expires_at": exp, "days_left": (None if not exp else max(0, round((exp - time.time()) / 86400, 1))),
            "expired": bool(exp and time.time() >= exp),
            "bots": len(own), "online": online, "servers": len(t.get("servers", [])),
            "visits": t.get("visits", {"total": 0, "today": 0})}

@app.route(ADMIN_PATH + '/clones')
@app.route(ADMIN_PATH + '/clones/')
def clones_page():
    return _no_store(send_from_directory(STATIC_DIR, 'clones.html'))

@app.route(ADMIN_PATH + '/api/clones')
def clones_list():
    if not _main_ok(): return _unauth()
    with _store_lock:
        items = [tenant_view(sl, t) for sl, t in _MEM["tenants"].items()]
    items.sort(key=lambda x: -x["created"])
    return _no_store(jsonify({"ok": True, "clones": items, "limits": {"bots_per_clone": MAX_BOTS_PER_TENANT}}))

@app.route(ADMIN_PATH + '/api/clones', methods=['POST'])
def clones_create():
    if not _main_ok(): return _unauth()
    d = request.get_json(silent=True) or {}
    name = _clean(d.get('name'), 40)
    if not name: return jsonify({"ok": False, "error": "Main UI Name দিন"}), 400
    pw = _clean(d.get('password'), 64)
    if len(pw) < 4: return jsonify({"ok": False, "error": "Clone Admin Password কমপক্ষে ৪ অক্ষর দিন"}), 400
    mode = d.get('bot_mode')
    if mode not in ('shared', 'own'): return jsonify({"ok": False, "error": "Bot সিস্টেম সিলেক্ট করুন"}), 400
    tasks, err = ([], None) if d.get('no_tasks') else _clean_tasks(d.get('tasks'))
    if err: return jsonify({"ok": False, "error": err}), 400
    if not d.get('no_tasks') and not tasks:
        return jsonify({"ok": False, "error": "কমপক্ষে একটি Social Link দিন, অথবা 'টাস্ক ছাড়া' সিলেক্ট করুন"}), 400
    exp = 0 if d.get('unlimited') else _expiry_from_days(d.get('days'))
    if exp is None or (not d.get('unlimited') and exp == 0):
        return jsonify({"ok": False, "error": "কত দিন চলবে (দিন সংখ্যা) দিন, অথবা Unlimited সিলেক্ট করুন"}), 400
    with _store_lock:
        if len(_MEM["tenants"]) >= MAX_TENANTS:
            return jsonify({"ok": False, "error": f"সর্বোচ্চ {MAX_TENANTS}টি clone"}), 400
        custom_slug = d.get('custom_slug', '')
        if str(custom_slug).strip():
            slug, slug_error = _clean_slug(custom_slug)
            if slug_error: return jsonify({"ok": False, "error": slug_error}), 400
            if slug in _MEM["tenants"]: return jsonify({"ok": False, "error": "এই URL আগে থেকেই ব্যবহৃত হচ্ছে"}), 400
        else:
            slug = _gen_slug()
        if not slug: return jsonify({"ok": False, "error": "URL তৈরি করা যায়নি, আবার চেষ্টা করুন"}), 500
        salt = secrets.token_bytes(12)
        t = {"name": name, "tasks": tasks, "site": {"tasks": tasks, "maintenance": "off", "notice": "এই ওয়েবসাইটটি সাময়িকভাবে বন্ধ আছে।", "social_links": []}, "bot_mode": mode, "enabled": True, "created": int(time.time()),
             "expires_at": exp, "pw_salt": salt.hex(), "pw_hash": _pw_hash(pw, salt),
             "visits": {"total": 0, "today": 0, "date": str(date.today())},
             "servers": ([{"id": "bd", "name": "BANGLADESH 🇧🇩", "region": "BD"},
                          {"id": "ind", "name": "INDIA 🇮🇳", "region": "IND"}] if mode == 'own' else []),
             "bots": []}
        t["site"].update({"auth_mode": site_config().get("auth_mode", "manual"), "api_name": site_config().get("api_name", "AX-ROM"), "api_urls": dict(site_config().get("api_urls", DEFAULT_SITE_CONFIG["api_urls"])), "auto_leave": site_config().get("auto_leave", True)})
        _MEM["tenants"][slug] = t; _persist()
    return jsonify({"ok": True, "slug": slug})

@app.route(ADMIN_PATH + '/api/clones/<slug>', methods=['PUT'])
def clones_edit(slug):
    if not _main_ok(): return _unauth()
    d = request.get_json(silent=True) or {}
    with _store_lock:
        t = _MEM["tenants"].get(slug)
        if not t: return jsonify({"ok": False, "error": "Clone পাওয়া যায়নি"}), 404
        new_slug = slug
        if 'custom_slug' in d and str(d.get('custom_slug') or '').strip():
            new_slug, slug_error = _clean_slug(d.get('custom_slug'))
            if slug_error: return jsonify({"ok": False, "error": slug_error}), 400
            if new_slug != slug and new_slug in _MEM["tenants"]:
                return jsonify({"ok": False, "error": "এই URL আগে থেকেই ব্যবহৃত হচ্ছে"}), 400
        if d.get('name') is not None:
            nm = _clean(d['name'], 40)
            if not nm: return jsonify({"ok": False, "error": "Main UI Name দিন"}), 400
            t["name"] = nm
        if 'tasks' in d or d.get('no_tasks'):
            tasks, err = ([], None) if d.get('no_tasks') else _clean_tasks(d.get('tasks'))
            if err: return jsonify({"ok": False, "error": err}), 400
            if not d.get('no_tasks') and not tasks:
                return jsonify({"ok": False, "error": "কমপক্ষে একটি Social Link দিন, অথবা 'টাস্ক ছাড়া' সিলেক্ট করুন"}), 400
            t["tasks"] = tasks
            _cfg = site_config(Scope(slug)); _cfg["tasks"] = tasks
            if tasks: _cfg["tasks_enabled"] = True
        if 'site_notice' in d or 'site_social_links' in d:
            cfg = site_config(Scope(slug))
            if 'site_notice' in d: cfg['notice'] = _clean(d.get('site_notice'), 1200) or "এই ওয়েবসাইটটি সাময়িকভাবে বন্ধ আছে।"
            if 'site_social_links' in d:
                links, link_err = _clean_tasks(d.get('site_social_links'))
                if link_err: return jsonify({"ok": False, "error": link_err}), 400
                cfg['social_links'] = links
        if d.get('password'):
            pw = _clean(d['password'], 64)
            if len(pw) < 4: return jsonify({"ok": False, "error": "Password কমপক্ষে ৪ অক্ষর"}), 400
            salt = secrets.token_bytes(12); t["pw_salt"] = salt.hex(); t["pw_hash"] = _pw_hash(pw, salt)
            with _auth_lock:                       # পুরনো session বাতিল
                for k in [k for k, v in SESSIONS.items() if v[0] == slug]: SESSIONS.pop(k, None)
        if d.get('bot_mode') in ('shared', 'own') and d['bot_mode'] != t["bot_mode"]:
            t["bot_mode"] = d['bot_mode']
            if t["bot_mode"] == 'own' and not t.get("servers"):
                t["servers"] = [{"id": "bd", "name": "BANGLADESH 🇧🇩", "region": "BD"},
                                {"id": "ind", "name": "INDIA 🇮🇳", "region": "IND"}]
            if t["bot_mode"] == 'own':
                main_cfg = site_config()
                own_cfg = site_config(Scope(slug))
                for key in ("auth_mode", "api_name", "api_urls", "auto_leave"):
                    own_cfg[key] = dict(main_cfg.get(key, {})) if key == "api_urls" else main_cfg.get(key)
        if 'enabled' in d: t["enabled"] = bool(d['enabled'])
        if d.get('unlimited'): t["expires_at"] = 0
        elif d.get('days') not in (None, ''):
            exp = _expiry_from_days(d['days'])
            if exp is None or exp == 0: return jsonify({"ok": False, "error": "সঠিক দিন সংখ্যা দিন"}), 400
            t["expires_at"] = exp
        elif d.get('extend_days') not in (None, ''):
            try: ex = float(d['extend_days'])
            except Exception: ex = 0
            if ex > 0:
                base = max(time.time(), t.get("expires_at", 0) or time.time())
                t["expires_at"] = int(base + ex * 86400)
        if new_slug != slug:
            _MEM["tenants"].pop(slug)
            _MEM["tenants"][new_slug] = t
            with _auth_lock:
                for k in [k for k, v in SESSIONS.items() if v[0] == slug]: SESSIONS.pop(k, None)
        _persist()
    # bot process গুলো নতুন অবস্থা অনুযায়ী (monitor বন্ধ করে দেয়; চালু এখানে)
    threading.Thread(target=start_missing_bots_of, args=(new_slug,), daemon=True).start()
    return jsonify({"ok": True, "slug": new_slug})

@app.route(ADMIN_PATH + '/api/clones/<slug>', methods=['DELETE'])
def clones_delete(slug):
    if not _main_ok(): return _unauth()
    with _store_lock:
        t = _MEM["tenants"].pop(slug, None)
        if not t: return jsonify({"ok": False, "error": "Clone পাওয়া যায়নি"}), 404
        _persist()
    for b in t.get("bots", []): stop_bot(b["id"])       # শুধু এই clone এর bot বন্ধ
    with _auth_lock:
        for k in [k for k, v in SESSIONS.items() if v[0] == slug]: SESSIONS.pop(k, None)
    return jsonify({"ok": True})

@app.route(ADMIN_PATH + '/api/clones/<slug>/enter')
def clones_enter(slug):
    """main admin 'Go to Admin' — password ছাড়াই ওই clone এর admin panel এ ঢোকে"""
    if not _main_ok(): return _unauth()
    sc = _clone_scope(slug)
    if not sc: return jsonify({"ok": False, "error": "not found"}), 404
    resp = make_response('', 302)
    resp.headers['Location'] = f'/{slug}/admin'
    _set_cookie(resp, sc, _new_session(sc))
    return _no_store(resp)

# ═══════════════ CLONE USER SITE ═══════════════
def _maintenance_page(cfg, original=False):
    title = "WEBSITE MAINTENANCE" if original else "WEBSITE TEMPORARILY UNAVAILABLE"
    notice = _html.escape(cfg.get("notice") or "ওয়েবসাইটে সাময়িক রক্ষণাবেক্ষণের কাজ চলছে।")
    buttons = "".join(f'<a class="social" href="{_html.escape(x.get("link", ""), quote=True)}" target="_blank" rel="noopener">{_html.escape(x.get("name", "SOCIAL LINK"))}</a>' for x in (cfg.get("social_links", []) or []) if x.get("link"))
    clones = ""
    if original:
        items = sorted(_MEM["tenants"].items(), key=lambda x: x[1].get("created", 0), reverse=True)
        clones = '<section class="clones"><h2>OUR CLONE WEBSITES</h2>' + "".join(f'<a class="clone" href="/{_html.escape(sl)}">{_html.escape(t.get("name", sl))} <span>OPEN WEBSITE →</span></a>' for sl,t in items) + '</section>'
    body = f'''<!doctype html><html lang="bn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;background:#0f0f13;color:#fff;font-family:Arial,sans-serif;display:flex;justify-content:center;align-items:center;padding:22px}}.wrap{{width:100%;max-width:760px;text-align:center}}.panel{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.13);border-radius:20px;padding:34px 22px;box-shadow:0 18px 60px #0008}}.mark{{font-size:42px;color:#00ff88}}h1{{color:#00ff88;font-size:clamp(25px,5vw,42px);margin:12px 0}}.notice{{font-size:clamp(17px,3vw,23px);line-height:1.7;color:#eee;margin:20px auto;max-width:650px}}.social,.clone{{display:flex;justify-content:center;align-items:center;gap:12px;width:100%;padding:18px 20px;margin:12px auto;border-radius:12px;text-decoration:none;font-weight:800;font-size:16px;background:linear-gradient(90deg,#ff0055,#ff00aa);color:#fff;border:1px solid #fff}}.clones{{margin-top:24px}}.clones h2{{color:#00ff88;font-size:18px}}.clone{{background:linear-gradient(90deg,#00b248,#00e676);color:#03140a;border-color:#b9ffd6;justify-content:space-between;text-align:left;box-shadow:0 6px 20px rgba(0,230,118,.28)}}.clone:hover{{filter:brightness(1.08)}}.clone span{{color:#03140a;font-size:12px;background:rgba(255,255,255,.55);padding:4px 10px;border-radius:20px}}.foot{{color:#777;font-size:11px;margin-top:20px}}</style></head>
<body><main class="wrap"><div class="panel"><div class="mark">⚙</div><h1>{title}</h1><p class="notice">{notice}</p>{clones}{buttons}<div class="foot">POWERED BY AX EMOTE SERVER</div></div></main></body></html>'''
    return make_response(body, 200)

def _inactive_page(t, slug):
    return _maintenance_page(site_config(Scope(slug)), original=False)

def _active_scope_or_resp(slug):
    sc = _clone_scope(slug)
    if not sc: return None, (jsonify({"status": "error", "message": "not found"}), 404)
    if not tenant_active(sc.tenant):
        return None, (jsonify({"status": "error", "message": "Website expired / disabled"}), 410)
    return sc, None

def _render_clone_index(slug, t):
    with open(os.path.join(STATIC_DIR, 'index.html'), 'r', encoding='utf-8') as f:
        page = f.read()
    name = _html.escape(t["name"])
    page = page.replace('<title>AX EMOTE SERVER</title>', f'<title>{name}</title>', 1)
    page = page.replace('<header><h1>AX EMOTE SERVER</h1></header>',
                        f'<header><h1>{name}</h1><div class="powered-by">POWERED BY AX EMOTE SERVER</div></header>', 1)
    page = page.replace('<h2>AX EMOTE SERVER UNLOCK 🔓</h2>', f'<h2>{name} UNLOCK 🔓</h2>', 1)
    cfg = (f'<script>window.AX_BASE={json.dumps("/" + slug)};'
           f'window.AX_NO_TASKS={"true" if not _effective_tasks(site_config(Scope(slug))) else "false"};</script>\n    ')
    page = page.replace('<script src="/script.js"></script>', cfg + '<script src="/script.js"></script>', 1)
    return page

def _record_tenant_visit(t):
    with _store_lock:
        v = t.setdefault("visits", {"total": 0, "today": 0, "date": str(date.today())})
        today = str(date.today())
        v["total"] = v.get("total", 0) + 1
        if v.get("date") != today: v["date"] = today; v["today"] = 1
        else: v["today"] = v.get("today", 0) + 1
        _persist()

@app.route('/<slug>')
@app.route('/<slug>/')
def clone_index(slug):
    sc = _clone_scope(slug)
    if not sc: return make_response("Not Found", 404)
    t = sc.tenant
    if not tenant_active(t): return _inactive_page(t, slug)
    if site_config(sc).get("maintenance") == "on": return _maintenance_page(site_config(sc), original=False)
    _record_tenant_visit(t)
    resp = make_response(_render_clone_index(slug, t))
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp

@app.route('/<slug>/api/tasks')
def clone_tasks(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    return jsonify([{"id": x["id"], "name": _html.escape(x["name"]), "link": x["link"]} for x in _effective_tasks(site_config(sc))])

@app.route('/<slug>/api/settings')
def clone_settings(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    return jsonify(_public_site_settings(site_config(sc)))

@app.route('/<slug>/api/visits')
def clone_visits(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    v = sc.tenant.get("visits", {})
    return jsonify({"total": v.get("total", 0), "today": v.get("today", 0)})

@app.route('/<slug>/api/servers')
def clone_servers(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    bots = sc.usable_bots(); out = []
    # Own-bot clones use only their own server and manual bot inventory.
    # Shared clones continue to inherit the Original Website's server/login mode.
    servers = sc.servers() if not sc.is_shared() else load_servers()
    for s in servers:
        mine = [b for b in bots if b["server_id"] == s["id"]]
        online = sum(1 for b in mine if PROCS.get(b["id"], {}).get("status") == "online")
        mode = server_bot_mode(s, _effective_public_scope(sc)) if sc.is_shared() else "manual"
        out.append({"id": s["id"], "name": s["name"], "total": len(mine), "online": online,
                    "mode": mode, "json_available": 0})
    return jsonify(out)

@app.route('/<slug>/api/bots')
def clone_bots(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    sid = request.args.get('server')
    return jsonify([bot_view(b) for b in sc.usable_bots() if b["server_id"] == sid])

@app.route('/<slug>/api/runtime-config')
def clone_runtime_config(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    if not sc.is_shared():
        # An own-bot clone is fully isolated from Original API/JSON/Manual mode.
        return jsonify({"auth_mode": "manual", "server_modes": {x["id"]: "manual" for x in sc.servers()}})
    cfg = site_config(Scope(None))
    mode = str(cfg.get("auth_mode") or "manual").lower()
    return jsonify({"auth_mode": mode, "server_modes": {x["id"]: mode for x in load_servers()}})

@app.route('/<slug>/api/save-server', methods=['POST'])
def clone_save_server(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    if not sc.is_shared():
        return jsonify({"ok": False, "error": "এই Clone Website নিজের Manual Bot ব্যবহার করে। Server-এর নিচে Bot সিলেক্ট করুন।"}), 400
    d = request.get_json(silent=True) or {}
    sid = _clean(d.get("server_id"), 20)
    mode = str(site_config(Scope(None)).get("auth_mode") or "manual").lower()
    if mode == "json": return _start_json_account(sc, sid)
    if mode == "api": return _generate_api_account(sc, sid)
    return jsonify({"ok": False, "error": "Original Website Manual mode-এ আছে"}), 400

@app.route('/<slug>/api/my-bot')
def clone_api_my_bot(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    if not sc.is_shared(): return jsonify({"active": False, "status": "not_running"})
    return _api_status_response(sc)

@app.route('/<slug>/api/logout-bot', methods=['POST'])
def clone_api_logout_bot(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    return _api_logout(sc)

@app.route('/<slug>/join')
def clone_join(slug):
    sc, err = _active_scope_or_resp(slug)
    if err: return err
    bot_id = request.args.get('bot')
    if bot_id:
        # Bot IDs are resolved strictly inside this clone's scope (or shared Original pool).
        bot = next((b for b in sc.usable_bots() if b["id"] == bot_id), None)
    elif sc.is_shared() and site_config(Scope(None)).get("auth_mode") in ("api", "json"):
        sid = request.args.get("server"); bot = _api_bot_for_request(sc)
        if bot and bot.get("server_id") != sid: bot = None
    else:
        # Own-bot clones never fall through to Original Website API/JSON sessions.
        bot = None
    return _proxy_join(bot)

# ═══════════════ STARTUP ═══════════════
def _shutdown(*_):
    for bid in list(PROCS.keys()):
        try: stop_bot(bid)
        except Exception: pass
    os._exit(0)

atexit.register(lambda: [stop_bot(b) for b in list(PROCS.keys())])
for _sig in (signal.SIGTERM, signal.SIGINT):
    try: signal.signal(_sig, _shutdown)
    except Exception: pass

def _fix_tenants():
    """store file থেকে লোড করা clone গুলোর ডিফল্ট ফিল্ড নিশ্চিত করে"""
    for t in _MEM["tenants"].values():
        t.setdefault("servers", []); t.setdefault("bots", []); t.setdefault("tasks", [])
        t.setdefault("site", {"tasks": t.get("tasks", []), "maintenance": "off", "notice": "এই ওয়েবসাইটটি সাময়িকভাবে বন্ধ আছে।", "social_links": []})
        t.setdefault("enabled", True); t.setdefault("expires_at", 0)
        t.setdefault("site", {}).setdefault("auth_mode", "manual"); t.setdefault("site", {}).setdefault("api_name", "AX-ROM"); t.setdefault("site", {}).setdefault("api_urls", dict(DEFAULT_SITE_CONFIG["api_urls"])); t.setdefault("site", {}).setdefault("auto_leave", True)
        t.setdefault("visits", {"total": 0, "today": 0, "date": str(date.today())})

def boot():
    _load_store_file()
    _load_json_pool_file()
    load_servers()
    _fix_tenants()
    threading.Thread(target=monitor_loop, daemon=True).start()
    threading.Thread(target=start_all_bots, daemon=True).start()

if __name__ == '__main__':
    boot()
    port = int(os.environ.get("PORT", 5000))
    print(f"[AX] Manager running on :{port} | admin panel: {ADMIN_PATH}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
