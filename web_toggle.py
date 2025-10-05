#!/usr/bin/env python3
import os
import re
import sqlite3
import subprocess
from functools import wraps
from typing import Tuple

from flask import Flask, request, Response, redirect, url_for, render_template_string, flash

DB_PATH = "/etc/pihole/gravity.db"
GROUP_YOUTUBE = "KidsRestricted"
GROUP_ROBLOX = "KidsRoblox"

HTTP_USER = os.getenv("TOGGLE_WEB_USER", "admin")
HTTP_PASS = os.getenv("TOGGLE_WEB_PASS", "change-me")

app = Flask(__name__)
app.secret_key = os.getenv("TOGGLE_WEB_SECRET", "dev-secret")


def _auth_failed() -> Response:
    return Response(
        "Authentication required", 401, {"WWW-Authenticate": 'Basic realm="Pi-Toggle"'}
    )


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != HTTP_USER or auth.password != HTTP_PASS:
            return _auth_failed()
        return fn(*args, **kwargs)

    return wrapper


def _query_enabled(group_name: str) -> bool:
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=0.1)
        try:
            conn.execute("PRAGMA busy_timeout=100")
            cur = conn.execute(
                "SELECT enabled FROM 'group' WHERE name=?;", (group_name,)
            )
            row = cur.fetchone()
            if not row:
                return False
            return int(row[0]) == 1
        finally:
            conn.close()
    except Exception:
        return False


def _set_enabled(group_name: str, enabled: bool) -> None:
    conn = sqlite3.connect(DB_PATH, timeout=2.0)
    try:
        conn.execute("PRAGMA busy_timeout=2000")
        conn.execute(
            "INSERT OR IGNORE INTO 'group'(name,enabled) VALUES(?,0);", (group_name,)
        )
        conn.execute(
            "UPDATE 'group' SET enabled=? WHERE name=?;", (1 if enabled else 0, group_name)
        )
        conn.commit()
    finally:
        conn.close()


def _get_status() -> Tuple[bool, bool]:
    yt = _query_enabled(GROUP_YOUTUBE)
    rb = _query_enabled(GROUP_ROBLOX)
    return yt, rb


INDEX_TMPL = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pi Toggle</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; }
    .row { display: flex; gap: 16px; align-items: center; margin: 12px 0; }
    .badge { padding: 6px 10px; border-radius: 8px; color: #fff; font-weight: 600; }
    .ok { background: #0a7d0a; }
    .warn { background: #cc5a00; }
    .err { background: #b30000; }
    button { padding: 8px 12px; font-weight: 600; cursor: pointer; }
    form { display: inline; }
    .sep { height: 1px; background: #ddd; margin: 16px 0; }
    .note { color: #555; font-size: 0.95rem; }
    .flash { color: #333; background: #ffedb1; padding: 8px 10px; border-radius: 6px; margin-bottom: 12px; display: inline-block; }
  </style>
  <meta http-equiv="refresh" content="5" />
  <!-- light auto-refresh to reflect hardware button presses -->
  
</head>
<body>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
    {% endif %}
  {% endwith %}

  <h2>Local Toggles</h2>

  <div class="row">
    <div style="width: 120px;">YouTube</div>
    {% if yt %}<span class="badge err">BLOCKED</span>{% else %}<span class="badge ok">ALLOWED</span>{% endif %}
    <form method="post" action="{{ url_for('toggle_youtube') }}">
      {% if yt %}
        <button type="submit">Allow</button>
      {% else %}
        <button type="submit">Block</button>
      {% endif %}
    </form>
  </div>

  <div class="row">
    <div style="width: 120px;">Roblox</div>
    {% if rb %}<span class="badge warn">BLOCKED</span>{% else %}<span class="badge ok">ALLOWED</span>{% endif %}
    <form method="post" action="{{ url_for('toggle_roblox') }}">
      {% if rb %}
        <button type="submit">Allow</button>
      {% else %}
        <button type="submit">Block</button>
      {% endif %}
    </form>
  </div>

  <div class="sep"></div>
  <h3>Cron Schedule</h3>
  <div class="row"><div style="width: 160px;">Block time</div><div>{{ cron_block or '—' }}</div></div>
  <div class="row"><div style="width: 160px;">Allow time</div><div>{{ cron_allow or '—' }}</div></div>

  <div class="sep"></div>
  <h3>One-shot Block</h3>
  <form method="post" action="{{ url_for('schedule_block_after') }}" class="row">
    <label for="minutes" style="width: 160px;">Block after (minutes)</label>
    <input id="minutes" name="minutes" type="number" min="1" max="1440" placeholder="e.g. 30" required />
    <button type="submit">Set</button>
  </form>

  <div class="sep"></div>
  <div class="note">Authenticated access only. Page refreshes every ~5s to reflect hardware button presses.</div>

</body>
</html>
"""


@app.route("/")
@require_auth
def index() -> Response:
    yt, rb = _get_status()
    cron_block, cron_allow = _get_cron_times()
    return render_template_string(INDEX_TMPL, yt=yt, rb=rb, cron_block=cron_block, cron_allow=cron_allow)


@app.post("/toggle/youtube")
@require_auth
def toggle_youtube():
    yt, rb = _get_status()
    _set_enabled(GROUP_YOUTUBE, not yt)
    flash(f"YouTube => {'BLOCKED' if not yt else 'ALLOWED'}")
    return redirect(url_for("index"))


@app.post("/toggle/roblox")
@require_auth
def toggle_roblox():
    yt, rb = _get_status()
    _set_enabled(GROUP_ROBLOX, not rb)
    flash(f"Roblox => {'BLOCKED' if not rb else 'ALLOWED'}")
    return redirect(url_for("index"))


def _get_cron_times() -> tuple[str | None, str | None]:
    try:
        out = subprocess.check_output(["/usr/bin/crontab", "-l"], text=True)
    except Exception:
        return None, None
    block_time = None
    allow_time = None
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(\S+)\s+(\S+)\s+\S+\s+\S+\s+\S+\s+(.+)$", line)
        if not m:
            continue
        minute, hour, cmd = m.groups()
        hhmm = f"{hour.zfill(2)}:{minute.zfill(2)}"
        if "pitft_cron_block" in cmd and not block_time:
            block_time = hhmm
        if "pitft_cron_allow" in cmd and not allow_time:
            allow_time = hhmm
    return block_time, allow_time


def _schedule_block_after_minutes(minutes: int) -> bool:
    if minutes < 1 or minutes > 1440:
        return False
    cmd = [
        "/usr/bin/systemd-run",
        "--unit", f"web-toggle-once-{minutes}m",
        "--on-active", f"{minutes}m",
        "/bin/bash", "-lc",
        "/usr/local/bin/pitft_block.sh && /usr/local/bin/pitft_roblox_block.sh"
    ]
    try:
        subprocess.check_output(cmd, text=True)
        return True
    except Exception:
        return False


@app.post("/schedule/block_after")
@require_auth
def schedule_block_after():
    try:
        minutes = int(request.form.get("minutes", "0"))
    except Exception:
        minutes = 0
    if _schedule_block_after_minutes(minutes):
        flash(f"Scheduled one-shot block in {minutes} minute(s)")
    else:
        flash("Failed to schedule block; please enter 1–1440 minutes")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))


