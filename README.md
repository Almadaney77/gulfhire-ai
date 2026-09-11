| File | What it does |
| --- | --- |
| `gulfhire-ai-live.html` | Main site: landing page + Scam Checker + Live Job Board |
| `jobs.js` | Live job database (loaded by the site) |
| `gulfhire-payment.html` | Paystack checkout (Go-Getter ₦3,500/mo · Fast-Track ₦15,000) |
| `whatsapp_bot.py` | WhatsApp bot (Twilio) — jobs, scam checks, upgrades |
| `gulfhire_scraper.py` | Daily scraper — regenerates `jobs.js` + `jobs.json` |
| `jobs.json` | Same database in JSON (used by the bot) |
