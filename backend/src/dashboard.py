"""
Day 8 — Call Analytics Dashboard.

Start:
    python src/dashboard.py

Opens a web dashboard at http://localhost:8080 showing
total calls, successful calls, and failed calls from
the real call_logs database.
"""

import json
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from database import get_call_stats, get_recent_calls

_backend_dir = Path(__file__).resolve().parent.parent

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FinAssist — Call Analytics Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f172a; color: #e2e8f0; min-height: 100vh;
    padding: 32px;
  }
  h1 { font-size: 24px; margin-bottom: 8px; }
  .subtitle { color: #94a3b8; font-size: 14px; margin-bottom: 32px; }
  .cards { display: flex; gap: 20px; margin-bottom: 40px; flex-wrap: wrap; }
  .card {
    background: #1e293b; border-radius: 12px; padding: 28px 32px;
    min-width: 200px; flex: 1;
  }
  .card-label { font-size: 13px; color: #94a3b8; text-transform: uppercase;
    letter-spacing: 1.5px; margin-bottom: 8px; }
  .card-value { font-size: 42px; font-weight: 700; }
  .card-value.total { color: #60a5fa; }
  .card-value.success { color: #34d399; }
  .card-value.failed { color: #f87171; }
  .section-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 12px; color: #94a3b8; text-transform: uppercase;
    letter-spacing: 1px; padding: 10px 12px; border-bottom: 1px solid #334155; }
  td { padding: 12px; border-bottom: 1px solid #1e293b; font-size: 14px; }
  tr:hover td { background: #1e293b; }
  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 600;
  }
  .badge.success { background: #064e3b; color: #34d399; }
  .badge.failed { background: #450a0a; color: #f87171; }
  .refresh-note { color: #64748b; font-size: 12px; margin-top: 24px; }
  .success-reason { color: #94a3b8; font-size: 12px; }
</style>
</head>
<body>
<h1>FinAssist Call Analytics</h1>
<p class="subtitle">Day 8 Dashboard — Real-time call metrics</p>

<div class="cards">
  <div class="card">
    <div class="card-label">Total Calls</div>
    <div class="card-value total" id="total">—</div>
  </div>
  <div class="card">
    <div class="card-label">Successful</div>
    <div class="card-value success" id="successful">—</div>
  </div>
  <div class="card">
    <div class="card-label">Failed</div>
    <div class="card-value failed" id="failed">—</div>
  </div>
</div>

<div class="section-title">Recent Calls</div>
<table>
  <thead>
    <tr>
      <th>Time</th>
      <th>Channel</th>
      <th>Duration</th>
      <th>Outcome</th>
      <th>Reason</th>
    </tr>
  </thead>
  <tbody id="calls"></tbody>
</table>

<p class="refresh-note">Auto-refreshes every 5 seconds. No sensitive data is displayed.</p>

<script>
async function load() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('total').textContent = data.total;
    document.getElementById('successful').textContent = data.successful;
    document.getElementById('failed').textContent = data.failed;

    const tbody = document.getElementById('calls');
    tbody.innerHTML = '';
    for (const c of data.recent) {
      const tr = document.createElement('tr');
      const started = new Date(c.started_at);
      const ended = c.ended_at ? new Date(c.ended_at) : null;
      const dur = ended
        ? ((ended - started) / 1000).toFixed(1) + 's'
        : '—';
      const reason = c.success_reason || '—';
      tr.innerHTML =
        '<td>' + started.toLocaleString() + '</td>' +
        '<td>' + c.channel + '</td>' +
        '<td>' + dur + '</td>' +
        '<td><span class="badge ' + c.outcome + '">' + c.outcome + '</span></td>' +
        '<td class="success-reason">' + reason + '</td>';
      tbody.appendChild(tr);
    }
  } catch (e) {
    console.error('Failed to load stats:', e);
  }
}
load();
setInterval(load, 5000);
</script>
</body>
</html>
"""


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/stats":
            stats = get_call_stats()
            recent = get_recent_calls(20)
            data = {**stats, "recent": recent}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        elif self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # Suppress request logs


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("localhost", port), DashboardHandler)
    url = f"http://localhost:{port}"
    print(f"Dashboard running at {url}")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
