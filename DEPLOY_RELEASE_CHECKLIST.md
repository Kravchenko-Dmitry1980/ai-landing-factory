# Deploy Release Checklist

Дата: 2026-07-26

## Local product

- [x] Local UAT pass
- [x] Algofusion DOCX repair pass
- [x] Backend health (`GET /health` → 200)
- [x] Frontend available (`/` → 200)
- [x] Frontend lint + production build
- [x] Targeted backend tests green (Algofusion + regression)

## Release artifacts

- [x] Static archive built (`.runtime/release/ai-landing-static-demo.zip`)
- [x] Full archive built (`.runtime/release/ai-landing-full-product.zip`)
- [x] Static archive contains `index.html` + wow + standard + showcase
- [x] Full archive excludes `.env`, `.venv`, `node_modules`, `.git`, `.runtime`, uploads

## Deploy layer

- [x] Env templates (`backend/.env.production.example`, `frontend/.env.production.example`, docker example)
- [x] nginx templates (static + full)
- [x] systemd templates (backend + frontend)
- [x] Ubuntu install / deploy / rollback / healthcheck scripts
- [x] Docker compose draft (experimental)
- [x] Static demo README
- [x] Full systemd README
- [x] `scripts/deploy_preflight.ps1`
- [x] Security audit documented
- [x] No secrets in git index

## Server (pending)

- [ ] Server params received
- [ ] Mode selected (A static / B systemd)
- [ ] SSL plan confirmed
- [ ] FreeModel decision (default: disabled)
- [ ] Actual server deploy executed
- [ ] Post-deploy healthcheck on public URL

## Stop-list confirmation

- [x] No `git push`
- [x] No SSH/SCP to server
- [x] No FreeModel / paid AI smoke
- [x] No DNS / SSL issuance
- [x] Local commit only (when hygiene OK)
