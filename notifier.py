import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# Email / SMTP configuration (set these in your .env file, see .env.example).
# Defaults target Gmail; SMTP_USER/SMTP_PASSWORD are required to actually send.
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")          # sender email address
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # Gmail app password (not your login password)
DEFAULT_RECIPIENT = os.environ.get("NOTIFY_EMAIL", "vivekchaudhary1816@gmail.com")


def build_email_body(candidates):
    """Build plain-text and HTML summaries of the selected candidates.

    candidates: list of dicts with keys
        username, profile_url, github_score, top_language, commit_count
    Returns (text_body, html_body).
    """
    if not candidates:
        text = "No candidates are currently marked as selected."
        html = f"<p>{text}</p>"
        return text, html

    lines = []
    rows = []
    for c in candidates:
        username = c.get("username", "unknown")
        score = c.get("github_score", 0)
        language = c.get("top_language") or "-"
        commits = c.get("commit_count", 0)
        url = c.get("profile_url", "")

        lines.append(f"- {username} | score {score} | {language} | {commits} commits | {url}")
        rows.append(
            "<tr>"
            f"<td><a href='{url}'>{username}</a></td>"
            f"<td align='center'>{score}</td>"
            f"<td align='center'>{language}</td>"
            f"<td align='center'>{commits}</td>"
            "</tr>"
        )

    text = (
        f"HushHush Recruiter selected {len(candidates)} candidate(s):\n\n"
        + "\n".join(lines)
    )

    html = f"""\
<html>
  <body style="font-family: Arial, sans-serif; color: #222;">
    <h2>HushHush Recruiter &mdash; {len(candidates)} Selected Candidate(s)</h2>
    <table cellpadding="8" cellspacing="0" style="border-collapse: collapse; border: 1px solid #ddd;">
      <tr style="background:#f2f2f2;">
        <th align="left">Username</th>
        <th>GitHub Score</th>
        <th>Top Language</th>
        <th>Commits (90d)</th>
      </tr>
      {''.join(rows)}
    </table>
    <p style="color:#888; font-size:12px;">Sent automatically by HushHush Recruiter.</p>
  </body>
</html>
"""
    return text, html


def send_email(subject, text_body, html_body=None, to_email=None):
    """Send an email over SMTP. Returns the recipient address on success."""
    to_email = to_email or DEFAULT_RECIPIENT

    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USER and SMTP_PASSWORD must be set in your .env file to send emails."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_USER
    message["To"] = to_email
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)

    return to_email


def notify_selected_candidates(candidates, to_email=None):
    """Email the list of selected candidates. Returns the recipient address.

    candidates: list of dicts (already filtered to selected candidates).
    """
    text_body, html_body = build_email_body(candidates)
    subject = f"HushHush Recruiter - {len(candidates)} selected candidate(s)"
    return send_email(subject, text_body, html_body, to_email)
