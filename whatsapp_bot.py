#!/usr/bin/env python3
"""
GulfHire AI — WhatsApp Bot (Twilio)
====================================
Users message your WhatsApp Business number; this bot replies with:
  - LIVE job matches from jobs.json (regenerate with gulfhire_scraper.py)
  - SCAM CHECKS on any suspicious offer text they forward
  - Plan upgrade links (Paystack checkout)

SETUP (15 minutes):
  1. pip install flask twilio requests
  2. Free Twilio account -> Messaging -> Try it out -> WhatsApp sandbox.
     Sandbox gives you a join code; users message "join <code>" to your number.
  3. Point the sandbox webhook to this app (needs a public URL):
     - Easiest free option: ngrok (ngrok http 5000) -> paste https URL + /webhook into Twilio.
  4. Run: python whatsapp_bot.py
  5. Go live: upgrade to Twilio WhatsApp Business API (approved sender).

SECURITY: set TWILIO_AUTH_TOKEN env var; Twilio signs every webhook.
"""
import json, os, re, requests
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")

# ---------------------------------------------------------------- SCAM FLAGS
FLAGS = [
 (r"(processing fee|visa fee|pay\s*(for)?\s*(the)?\s*(visa|job|registration|medical|slot)|send money)",
  "💸 Asks for money — legitimate Gulf employers NEVER charge fees."),
 (r"\+91", "🇮🇳 +91 contact — a known red flag for Nigeria-targeting scams."),
 (r"(guaranteed|100%\s*(visa|job)|assured visa|no interview needed)",
  "🎭 'Guaranteed visa/job' — real employers always interview."),
 (r"(urgent|only \d+ slots|limited slot|expires?)", "⏰ Manufactured urgency — pressure tactic."),
 (r"(whatsapp only|contact (the )?agent)", "📱 WhatsApp-only 'agent' — real hotels use official portals."),
 (r"\b(gmail|yahoo|hotmail|outlook)\.com", "📧 Free email posing as official — recruiters use company domains."),
 (r"(send (us )?(your )?(passport|id card|bvn)|scan of your passport)",
  "🪪 Requests passport/ID upfront — identity-theft risk."),
 (r"\$\s?[3-9],\d{3}\s*(per|/)?\s*week", "💰 Unrealistic salary for entry-level hospitality."),
]

def scam_check(text):
    hits = [msg for pat, msg in FLAGS if re.search(pat, text, re.I)]
    n = len(hits)
    if n == 0:
        verdict = ("✅ *No scam signatures detected.*\nStill verify: search the company on Qiwa.sa "
                   "and confirm the role on the hotel's official careers page.")
    elif n <= 2:
        verdict = f"⚠️ *CAUTION — {n} red flag(s).*\nVerify the employer's CR on Qiwa.sa before sharing any documents."
    else:
        verdict = (f"🚨 *LIKELY SCAM — {n} red flags.*\nDo NOT pay, do NOT send documents, "
                   "block & report this contact.")
    detail = "\n".join("• " + h for h in hits)
    return f"{verdict}\n\n{detail}" if detail else verdict

# ---------------------------------------------------------------- JOBS
def load_jobs():
    try:
        with open("jobs.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def match(role, city):
    js = load_jobs()
    r = re.sub(r"\s+", "", role.lower())
    out = [j for j in js if (not r or r == "any" or r in j["role"] or j["role"] == "any")
           and (not city or city == "any" or j["city"] == city)]
    out.sort(key=lambda j: (j["city"] != "madinah",))
    return out[:5]

# ---------------------------------------------------------------- WEBHOOK
HELP = ("🌟 *GulfHire AI*\n"
        "Reply with:\n"
        "• *jobs* — latest verified Gulf openings\n"
        "• *jobs <role> <city>*  e.g. _jobs waiter madinah_\n"
        "• *check <paste any offer text>* — instant scam analysis\n"
        "• *upgrade* — Go-Getter ₦3,500/mo or Fast-Track ₦15,000\n"
        "• *help* — this menu\n\n"
        "⚠️ Never pay recruitment fees. Verify employers on Qiwa.sa")

@app.route("/webhook", methods=["POST"])
def webhook():
    msg = request.values.get("Body", "").strip()
    from_no = request.values.get("From", "")
    reply = MessagingResponse()
    body = reply.message()
    low = msg.lower()

    if not msg or "help" in low or "menu" in low:
        body.body(HELP)

    elif low.startswith("check"):
        payload = msg[5:].strip()
        body.body(scam_check(payload) if payload else
                  "Paste the offer text after 'check', e.g.\ncheck Congratulations! You are selected... pay visa fee ₦85,000")

    elif low.startswith("jobs"):
        parts = low.split()
        role = parts[1] if len(parts) > 1 else "any"
        city = parts[2] if len(parts) > 2 else "any"
        ms = match(role, city)
        if not ms:
            body.body("No live matches for that filter right now. Try 'jobs any any' or 'jobs housekeeping madinah'.")
        else:
            lines = [f"🎯 *{len(ms)} verified opening(s)* — apply on official portals only:\n"]
            for j in ms:
                lines.append(f"▪ *{j['title']}*\n  {j['hotel']} · {j['city'].title()}\n  {j['url']}")
            body.body("\n\n".join(lines))

    elif "upgrade" in low or "pay" in low or "price" in low:
        body.body("💎 *Go-Getter* — ₦3,500/month: instant alerts, CV tailoring, ATS applications\n"
                  "🚀 *Fast-Track* — ₦15,000 once: everything + strategy call + Arabic CV\n\n"
                  "Pay securely here: https://YOURDOMAIN.com/gulfhire-payment.html\n"
                  "Activation within 1 hour of payment.")

    else:
        body.body("I didn't quite catch that.\n\n" + HELP)

    return Response(str(reply), mimetype="application/xml")

@app.route("/")
def health():
    return "GulfHire AI bot is running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
