import http.server
import urllib.parse
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ── DB helper ──────────────────────────────────────────────────────────────────
def get_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "job_tracker_db")
        )
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None


def read_template(name):
    path = os.path.join("templates", name)
    with open(path, "r") as f:
        return f.read()


def render(template, **ctx):
    html = read_template(template)
    for key, val in ctx.items():
        html = html.replace("{{ " + key + " }}", str(val) if val is not None else "")
    return html


# ── Request Handler ────────────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # cleaner console output
        print(f"  {self.command} {self.path}")

    def send_html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def serve_static(self, path):
        # strip leading /
        filepath = path.lstrip("/")
        if not os.path.exists(filepath):
            self.send_response(404)
            self.end_headers()
            return
        ext = filepath.rsplit(".", 1)[-1]
        mime = {"css": "text/css", "js": "application/javascript"}.get(ext, "text/plain")
        with open(filepath, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def parse_query(self):
        parsed = urllib.parse.urlparse(self.path)
        return parsed.path, urllib.parse.parse_qs(parsed.query)

    def read_post(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        return urllib.parse.parse_qs(raw)

    def pv(self, params, key, default=""):
        # get first value from parse_qs dict
        return params.get(key, [default])[0]

    # ── GET ──────────────────────────────────────────────────────────────────
    def do_GET(self):
        path, params = self.parse_query()

        if path.startswith("/static/"):
            self.serve_static(path)
            return

        if path == "/" or path == "/index":
            self.page_index(params)
        elif path == "/add":
            self.page_add_form()
        elif path.startswith("/edit/"):
            job_id = path.split("/")[-1]
            self.page_edit_form(job_id)
        else:
            self.send_html("<h2>404 – Page not found</h2>", 404)

    # ── POST ─────────────────────────────────────────────────────────────────
    def do_POST(self):
        path, _ = self.parse_query()
        data = self.read_post()

        if path == "/add":
            self.handle_add(data)
        elif path.startswith("/edit/"):
            job_id = path.split("/")[-1]
            self.handle_edit(job_id, data)
        elif path.startswith("/delete/"):
            job_id = path.split("/")[-1]
            self.handle_delete(job_id)
        else:
            self.redirect("/")

    # ── Pages ─────────────────────────────────────────────────────────────────
    def page_index(self, params):
        conn = get_db()
        if not conn:
            self.send_html("<p>DB connection failed.</p>")
            return

        cursor = conn.cursor(dictionary=True)
        status_filter = self.pv(params, "status")
        search_q = self.pv(params, "q")

        query = "SELECT * FROM applications WHERE 1=1"
        args = []
        if status_filter:
            query += " AND status = %s"
            args.append(status_filter)
        if search_q:
            query += " AND (company LIKE %s OR role LIKE %s)"
            args.extend([f"%{search_q}%", f"%{search_q}%"])
        query += " ORDER BY date_applied DESC"

        cursor.execute(query, args)
        jobs = cursor.fetchall()

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(status='Interview') AS interviews,
                SUM(status='Offer') AS offers,
                SUM(status='Rejected') AS rejected
            FROM applications
        """)
        stats = cursor.fetchone()
        cursor.close()
        conn.close()

        # build table rows
        rows_html = ""
        for j in jobs:
            rows_html += f"""
            <tr>
              <td class="company-name">{j['company']}</td>
              <td>{j['role']}</td>
              <td><span class="tag">{j['job_type']}</span></td>
              <td><span class="badge badge-{j['status'].lower()}">{j['status']}</span></td>
              <td>{j['location'] or '—'}</td>
              <td>{j['date_applied']}</td>
              <td class="actions">
                <a href="/edit/{j['id']}" class="btn-icon" title="Edit">✏️</a>
                <form method="POST" action="/delete/{j['id']}" style="display:inline"
                      onsubmit="return confirm('Delete this application?')">
                  <button type="submit" class="btn-icon danger" title="Delete">🗑</button>
                </form>
              </td>
            </tr>"""

        table_html = f"""
        <div class="table-wrapper">
          <table class="jobs-table">
            <thead>
              <tr>
                <th>Company</th><th>Role</th><th>Type</th>
                <th>Status</th><th>Location</th><th>Date Applied</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>""" if jobs else '<div class="empty-state"><p>No applications found. <a href="/add">Add your first one →</a></p></div>'

        # build filter bar
        status_options = ""
        for s in ["Applied", "Interview", "Offer", "Rejected"]:
            sel = 'selected' if status_filter == s else ''
            status_options += f'<option value="{s}" {sel}>{s}</option>'

        clear_btn = f'<a href="/" class="btn btn-ghost">Clear</a>' if (status_filter or search_q) else ''

        html = read_template("base.html").replace("{{TITLE}}", "Dashboard – Job Tracker").replace("{{CONTENT}}", f"""
        <div class="page-header">
          <h1>My Applications</h1>
          <p class="subtext">Tracking every opportunity in one place.</p>
        </div>

        <div class="stats-grid">
          <div class="stat-card"><div class="stat-label">Total Applied</div><div class="stat-value">{stats['total'] or 0}</div></div>
          <div class="stat-card"><div class="stat-label">Interviews</div><div class="stat-value interview">{stats['interviews'] or 0}</div></div>
          <div class="stat-card"><div class="stat-label">Offers</div><div class="stat-value offer">{stats['offers'] or 0}</div></div>
          <div class="stat-card"><div class="stat-label">Rejected</div><div class="stat-value rejected">{stats['rejected'] or 0}</div></div>
        </div>

        <form method="GET" action="/" class="filter-bar">
          <input type="text" name="q" placeholder="Search company or role..." value="{search_q}" />
          <select name="status">
            <option value="">All Statuses</option>
            {status_options}
          </select>
          <button type="submit" class="btn btn-secondary">Filter</button>
          {clear_btn}
        </form>

        {table_html}
        """)

        self.send_html(html)

    def page_add_form(self, error=""):
        content = f"""
        <div class="page-header"><h1>Add New Application</h1></div>
        {'<div class="alert alert-error">' + error + '</div>' if error else ''}
        <div class="form-card">
          <form method="POST" action="/add">
            <div class="form-row">
              <div class="form-group">
                <label>Company Name *</label>
                <input type="text" name="company" placeholder="e.g. Google" required />
              </div>
              <div class="form-group">
                <label>Role / Position *</label>
                <input type="text" name="role" placeholder="e.g. Software Engineer Intern" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Job Type</label>
                <select name="job_type">
                  <option>Full-time</option><option>Internship</option>
                  <option>Contract</option><option>Part-time</option>
                </select>
              </div>
              <div class="form-group">
                <label>Status</label>
                <select name="status">
                  <option>Applied</option><option>Interview</option>
                  <option>Offer</option><option>Rejected</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Location</label>
                <input type="text" name="location" placeholder="e.g. Bengaluru / Remote" />
              </div>
              <div class="form-group">
                <label>CTC / Stipend</label>
                <input type="text" name="salary" placeholder="e.g. 12 LPA" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Date Applied</label>
                <input type="date" name="date_applied" value="{datetime.today().strftime('%Y-%m-%d')}" />
              </div>
              <div class="form-group">
                <label>Job Posting URL</label>
                <input type="url" name="job_link" placeholder="https://..." />
              </div>
            </div>
            <div class="form-group">
              <label>Notes</label>
              <textarea name="notes" rows="4" placeholder="Referral info, rounds, recruiter name..."></textarea>
            </div>
            <div class="form-actions">
              <a href="/" class="btn btn-ghost">Cancel</a>
              <button type="submit" class="btn btn-primary">Save Application</button>
            </div>
          </form>
        </div>"""

        html = read_template("base.html").replace("{{TITLE}}", "Add – Job Tracker").replace("{{CONTENT}}", content)
        self.send_html(html)

    def page_edit_form(self, job_id):
        conn = get_db()
        if not conn:
            self.redirect("/")
            return
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM applications WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        cursor.close()
        conn.close()

        if not job:
            self.redirect("/")
            return

        def opt(types, current):
            return "".join(f'<option {"selected" if t == current else ""}>{t}</option>' for t in types)

        content = f"""
        <div class="page-header">
          <h1>Edit Application</h1>
          <p class="subtext">{job['role']} at {job['company']}</p>
        </div>
        <div class="form-card">
          <form method="POST" action="/edit/{job['id']}">
            <div class="form-row">
              <div class="form-group">
                <label>Company Name *</label>
                <input type="text" name="company" value="{job['company']}" required />
              </div>
              <div class="form-group">
                <label>Role / Position *</label>
                <input type="text" name="role" value="{job['role']}" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Job Type</label>
                <select name="job_type">{opt(['Full-time','Internship','Contract','Part-time'], job['job_type'])}</select>
              </div>
              <div class="form-group">
                <label>Status</label>
                <select name="status">{opt(['Applied','Interview','Offer','Rejected'], job['status'])}</select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Location</label>
                <input type="text" name="location" value="{job['location'] or ''}" />
              </div>
              <div class="form-group">
                <label>CTC / Stipend</label>
                <input type="text" name="salary" value="{job['salary'] or ''}" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Date Applied</label>
                <input type="date" name="date_applied" value="{job['date_applied']}" />
              </div>
              <div class="form-group">
                <label>Job Posting URL</label>
                <input type="url" name="job_link" value="{job['job_link'] or ''}" />
              </div>
            </div>
            <div class="form-group">
              <label>Notes</label>
              <textarea name="notes" rows="4">{job['notes'] or ''}</textarea>
            </div>
            <div class="form-actions">
              <a href="/" class="btn btn-ghost">Cancel</a>
              <button type="submit" class="btn btn-primary">Update Application</button>
            </div>
          </form>
        </div>"""

        html = read_template("base.html").replace("{{TITLE}}", "Edit – Job Tracker").replace("{{CONTENT}}", content)
        self.send_html(html)

    # ── Handlers ──────────────────────────────────────────────────────────────
    def handle_add(self, data):
        company = self.pv(data, "company").strip()
        role = self.pv(data, "role").strip()
        if not company or not role:
            self.page_add_form(error="Company and role are required.")
            return

        conn = get_db()
        if not conn:
            self.redirect("/")
            return

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (company, role, job_type, status, location, salary, date_applied, notes, job_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            company, role,
            self.pv(data, "job_type", "Full-time"),
            self.pv(data, "status", "Applied"),
            self.pv(data, "location"),
            self.pv(data, "salary"),
            self.pv(data, "date_applied") or datetime.today().strftime("%Y-%m-%d"),
            self.pv(data, "notes"),
            self.pv(data, "job_link"),
        ))
        conn.commit()
        cursor.close()
        conn.close()
        self.redirect("/")

    def handle_edit(self, job_id, data):
        conn = get_db()
        if not conn:
            self.redirect("/")
            return

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE applications
            SET company=%s, role=%s, job_type=%s, status=%s,
                location=%s, salary=%s, date_applied=%s, notes=%s, job_link=%s
            WHERE id=%s
        """, (
            self.pv(data, "company"),
            self.pv(data, "role"),
            self.pv(data, "job_type", "Full-time"),
            self.pv(data, "status", "Applied"),
            self.pv(data, "location"),
            self.pv(data, "salary"),
            self.pv(data, "date_applied"),
            self.pv(data, "notes"),
            self.pv(data, "job_link"),
            job_id,
        ))
        conn.commit()
        cursor.close()
        conn.close()
        self.redirect("/")

    def handle_delete(self, job_id):
        conn = get_db()
        if not conn:
            self.redirect("/")
            return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications WHERE id = %s", (job_id,))
        conn.commit()
        cursor.close()
        conn.close()
        self.redirect("/")


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PORT = 5000
    print(f"\n  Job Tracker running → http://localhost:{PORT}\n")
    server = http.server.HTTPServer(("", PORT), Handler)
    server.serve_forever()
