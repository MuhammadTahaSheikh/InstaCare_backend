# Production deployment — API + email verification

Stack:

| Piece | Where |
|-------|--------|
| Frontend | Vercel — `https://bestech-care.vercel.app` |
| API | VPS — `https://instacare-api.bestechvision.com` (PM2, port 5002) |
| Database | Hostinger MySQL |

---

## 1. Choose an SMTP provider

### Recommended: Hostinger email (best for `@bestechcare.pk`)

You already use Hostinger for MySQL. Use the same panel for email.

1. **hPanel → Emails → Create email** (e.g. `noreply@bestechcare.pk` or use `hello@bestechcare.pk`)
2. Open the mailbox → **Configuration** / **Connect apps** → copy SMTP settings
3. Add to the VPS `backend/.env`:

```env
FRONTEND_URL=https://bestech-care.vercel.app

SMTP_HOST=smtp.hostinger.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=noreply@bestechcare.pk
SMTP_PASS=your_mailbox_password
SMTP_FROM=BestechCare <noreply@bestechcare.pk>
```

Typical Hostinger SMTP: `smtp.hostinger.com`, port **587** (STARTTLS) or **465** (`SMTP_SECURE=true`).

---

### Alternative: Resend (developer-friendly, custom domain)

Good if you want analytics and simple API keys instead of mailbox passwords.

1. Sign up at [resend.com](https://resend.com)
2. Add domain `bestechcare.pk` and verify DNS (SPF/DKIM in Hostinger DNS)
3. Create an API key
4. Use Resend’s SMTP relay:

```env
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=resend
SMTP_PASS=re_xxxxxxxxxxxx
SMTP_FROM=BestechCare <noreply@bestechcare.pk>
```

Free tier: 3,000 emails/month.

---

### Dev only: Gmail

Fine for local testing, not ideal for production (`@gmail.com` sender).

1. Google Account → Security → 2FA on → **App passwords**
2. Create an app password for “Mail”

```env
FRONTEND_URL=http://localhost:3000

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your@gmail.com
SMTP_PASS=16_char_app_password
SMTP_FROM=BestechCare <your@gmail.com>
```

If SMTP is **not** set locally, the verification link is printed in the backend terminal.

---

## 2. VPS `.env` checklist

On the server, `backend/.env` should include at least:

```env
PORT=5002
NODE_ENV=production

DB_HOST=...          # localhost on Hostinger VPS, or auth-db1535.hstgr.io remotely
DB_USER=u916710688_instacare
DB_PASSWORD=...
DB_NAME=u916710688_instacare
JWT_SECRET=...

FRONTEND_URL=https://bestech-care.vercel.app
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...
SMTP_FROM=BestechCare <noreply@bestechcare.pk>
```

`FRONTEND_URL` must match the live Vercel URL so verification links open the correct site.

---

## 3. Deploy backend on VPS

SSH into the VPS, then:

```bash
cd /path/to/instacare/backend
git pull origin main
bash scripts/deploy.sh
```

The script will:

1. `npm install`
2. `npm run db:migrate:email` — adds verification columns; existing users stay verified
3. `pm2 reload instacare-api`

First-time PM2 setup:

```bash
cd backend
npm install
npm run db:migrate:email
pm2 start ecosystem.config.cjs
pm2 save
pm2 startup   # follow the printed command so API survives reboot
```

Logs:

```bash
pm2 logs instacare-api
pm2 status
```

---

## 4. Deploy frontend (Vercel)

1. Push frontend changes to GitHub
2. Vercel auto-deploys, or trigger a redeploy in the Vercel dashboard
3. Confirm env var: `VITE_API_URL=https://instacare-api.bestechvision.com`

No frontend env changes are needed for email — links use `FRONTEND_URL` on the API.

---

## 5. One-time database migration (if not using deploy script)

From any machine that can reach Hostinger MySQL:

```bash
cd backend
npm run db:migrate:email
```

Or in **phpMyAdmin** → select database → Import → `database/migrations/add_email_verification.sql`

---

## 6. Test the flow

1. Register a new account on production
2. Check inbox (and spam) for “Verify your BestechCare account”
3. Click the link → should land on `/verify-email?token=...` → “Email verified successfully”
4. Log in

If email doesn’t arrive:

```bash
pm2 logs instacare-api --lines 50
```

Look for SMTP errors or `[email] SMTP not configured` (means `.env` SMTP vars are missing on the server).

---

## Quick comparison

| Provider | Best for | Cost |
|----------|----------|------|
| **Hostinger** | `@bestechcare.pk`, already on Hostinger | Included with email plan |
| **Resend** | Clean dashboard, DNS on your domain | Free 3k/mo |
| **Gmail** | Local dev only | Free |

**Recommendation:** Use **Hostinger** `noreply@bestechcare.pk` for production — matches your domain and keeps everything in one panel.
