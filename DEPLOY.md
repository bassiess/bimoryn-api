# BIMoryn API — Deployment Guide

Deploys the REST API (`POST /validate`, `GET /rules`, `GET /health`) to a public HTTPS endpoint for pilot access.

## Prerequisites

- Git repo pushed to GitHub (needed for Render auto-deploy)
- API key generated: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Docker installed (needed for local smoke test before deploying)

---

## Option A — Fly.io (recommended, ~5 min)

Fly.io has a generous free tier and deploys to Amsterdam (closest to NL/BE/DE pilots).

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Authenticate
fly auth login

# 3. Create the app (first time only — generates a unique subdomain)
fly launch --no-deploy --name bimoryn-api --region ams

# 4. Set the API key secret
fly secrets set BIMORYN_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 5. Deploy
fly deploy --dockerfile Dockerfile.api

# 6. Smoke test
curl https://bimoryn-api.fly.dev/health
curl -H "Authorization: Bearer <YOUR_KEY>" https://bimoryn-api.fly.dev/rules
curl -H "Authorization: Bearer <YOUR_KEY>" \
     -F "file=@samples/demo.ifc" \
     https://bimoryn-api.fly.dev/validate
```

Public URL: `https://bimoryn-api.fly.dev` (or the subdomain assigned in step 3)

---

## Option B — Render (no CLI needed, free tier)

1. Push this repo to GitHub.
2. Go to render.com → New → Web Service → Connect repo.
3. Render detects `render.yaml` automatically — click **Apply**.
4. In the service dashboard → **Environment** → add `BIMORYN_API_KEY` = `<generated key>`.
5. Wait for first deploy (~3–5 min).

Public URL: `https://bimoryn-api.onrender.com` (assigned by Render)

> Note: Render free tier spins down after 15 min of inactivity — first request after sleep takes ~30s. Upgrade to Starter ($7/mo) for always-on for pilots.

---

## Option C — Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Authenticate
railway login

# 3. Init and deploy
railway init
railway up --dockerfile Dockerfile.api

# 4. Set the API key
railway variables set BIMORYN_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 5. Generate public domain
railway domain
```

---

## Local smoke test (before deploying)

```bash
# Build and run locally
docker build -f Dockerfile.api -t bimoryn-api .
docker run -e BIMORYN_API_KEY=test-key -p 8000:8000 bimoryn-api

# In another terminal
curl http://localhost:8000/health
curl -H "Authorization: Bearer test-key" http://localhost:8000/rules
curl -H "Authorization: Bearer test-key" \
     -F "file=@samples/demo.ifc" \
     http://localhost:8000/validate
```

---

## Pilot API key management

Generate one key per pilot account:

```bash
python -c "import secrets; print('bim_' + secrets.token_urlsafe(24))"
```

Share with pilot: `Authorization: Bearer bim_<key>`

Store keys in a password manager or 1Password vault — the API has no key rotation UI yet.

---

## API reference

| Endpoint | Auth | Description |
|---|---|---|
| `GET /health` | None | Liveness check — use for uptime monitoring |
| `GET /rules` | Bearer | List all 35 active validation rules |
| `POST /validate` | Bearer | Upload `.ifc` file → JSON validation report |
| `GET /docs` | None | Interactive OpenAPI UI (Swagger) |
| `GET /redoc` | None | ReDoc API docs |

Full OpenAPI spec: `GET /openapi.json`
