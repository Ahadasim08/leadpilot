# LeadPilot — Execution Plan (lives in repo root; Claude Code reads this every session)

AI lead-response agent for marketing agencies. Catches inbound leads, qualifies with AI (rules-first), replies using RAG over the agency's own docs, follows up automatically. Built by carving DocuWise (RAG core) + reusing Promyx patterns (structured extraction, rules-first/LLM-advisory, eval harness).

---

## SESSION PROTOCOL (read first, every session)

1. Every session begins with: read `PLAN.md` (this file) and `PROGRESS.md`. Implement ONLY the phase named in the user's instruction. Anything from later phases = scope violation, do not build it.
2. Contracts, prompts, DB schema, env var names, and DoD commands in this file are LAW. File paths are suggestions.
3. Every session ends with: update `PROGRESS.md` (template at bottom), then stop.
4. Never touch `.env`. Never commit secrets. `.env` is gitignored; `.env.example` carries dummy values.
5. If a task requires a GUI (Render, Supabase, n8n, Slack, Google OAuth), output the exact values/SQL/JSON for the user to paste — never claim to have done it.

## GIT PROTOCOL

- Repo initialized in Phase 1 (Phase 0 is its own tiny repo).
- `.gitignore` from the start: `.env`, `__pycache__/`, `*.db`, `node_modules/`, `.venv/`.
- Commit after each numbered task, message format: `phase1: add hard rules with tests`.
- Push at the end of every session. The GitHub repo is itself a portfolio artifact — commit history showing steady phased work reads better than one giant dump.
- Never commit: API keys, the filled `.env`, client data (fake Acme data is fine).

---

## GLOBAL CONTRACTS

### Env vars (`.env.example` mirrors with dummies)
```
SUPABASE_URL=
SUPABASE_KEY=            # service role key, NOT anon
LLM_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDINGS_PROVIDER=local   # local | api (fallback if Render OOMs)
AGENCY_NAME=Acme Digital
```

### `POST /score`
```json
// request
{"name":"Sarah","email":"sarah@x.com","company":"RealCo","message":"...","budget":"$3k/month"}
// response
{"verdict":"hot","score":88,"reasons":["explicit budget"],"missing_info":[],"rule_triggered":null}
```
`verdict` ∈ `hot|warm|cold|spam`; `score` 0–100; `rule_triggered` = name of hard rule that decided, or null if LLM decided. `name`, `email`, `message` required (422 otherwise); `company`, `budget` optional.

### `POST /draft`
```json
// request
{"lead":{...same shape...},"mode":"reply"}
// response
{"subject":"...","body":"...","sources_used":[{"doc":"pricing.md","chunk_id":"c_12"}],"low_context":false}
```
`mode` ∈ `reply|followup`. Empty retrieval → generic acknowledgment body with NO specific claims, `low_context:true`, empty sources.

### Non-negotiable behaviors
- Hard rules run BEFORE any LLM call; if a rule fires, the LLM is never called.
- All LLM calls: strict-JSON system prompt → strip ```json fences → `json.loads` → one retry on failure → then HTTP 502.
- `sources_used` is populated by the retrieval code from actual fetched chunk ids — NEVER by the LLM.
- Drafts may only claim what's in retrieved chunks.
- Single tenant: no auth, no user scoping, no multi-agency logic.

---

## PHASE 0 — Prove deployment (own folder `leadpilot-hello/`, own repo, 2h max)

`[CC]` Minimal FastAPI: `GET /health` → `{"status":"ok","service":"leadpilot"}`; `requirements.txt` (fastapi, uvicorn, pinned); `render.yaml` (free tier, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
`[MANUAL]` Push to GitHub → Render → New → Blueprint → deploy.
**DoD:** `curl https://<app>.onrender.com/health` returns ok. Do not start Phase 1 before this passes.

## PHASE 1 — Carve the brain (session opens inside a COPY of the DocuWise repo)

First instruction to CC: read the repo structure and present a carving plan before deleting anything.

Target structure (suggestion):
```
app/{main.py, config.py, db.py, rules.py}
app/models/schemas.py
app/services/{parsing.py, chunking.py, embeddings.py, retrieval.py, scoring.py, drafting.py}
app/llm/            # keep pluggable layer
app/routers/{score.py, draft.py}
scripts/seed.py     data/acme/     tests/     supabase_schema.sql
```

Tasks in order (one commit each):
1. Delete pass: frontend, auth routers/middleware, sessions/messages, SSE streaming. Headless — no JWT, no `require_user`. List deletions before deleting.
2. `supabase_schema.sql`: only `documents` + `chunks` (embedding `vector(384)`, HNSW) + `match_chunks` RPC `(query_embedding vector(384), match_count int, similarity_threshold float)`. No user_id columns.
3. `app/models/schemas.py`: pydantic models matching Global Contracts exactly; verdict/mode as `Literal`.
4. `app/rules.py` — pure functions, zero I/O, in order:
   - invalid email regex → spam, `"invalid_email"`
   - stripped message < 10 chars → spam, `"message_too_short"`
   - spam substrings (case-insensitive: buy backlinks, guest post, SEO packages, crypto, loan offer, increase your ranking, viagra) → spam, `"spam_pattern"`
   - disposable domains (mailinator.com, tempmail.com, guerrillamail.com, 10minutemail.com) → cold, `"disposable_email"`
   - Returns `ScoreResponse | None` (None = fall through to LLM).
5. `services/scoring.py`: rules → LLM (prompt below) → fence-strip → parse → retry once → clamp/validate → 502 on double failure.

Scoring prompt (LAW):
```
System: You are a lead-qualification engine for {AGENCY_NAME}, a digital marketing agency
offering: PPC/Google Ads, SEO, web design, social media management.
Return ONLY a JSON object, no markdown, no prose:
{"verdict":"hot|warm|cold|spam","score":<0-100>,"reasons":[...],"missing_info":[...]}
Rules: hot = clear service fit AND (budget signal OR urgency). warm = service fit, vague on
budget/timing. cold = unclear fit or mismatched need. spam = promotional/irrelevant.
User: Name: {name}\nEmail: {email}\nCompany: {company}\nBudget: {budget}\nMessage: {message}
```

6. `services/drafting.py`: embed message → `match_chunks(count=4, threshold=0.35)` → empty: generic ack + `low_context:true` → else prompt below → parse → attach `sources_used` from retrieved chunk ids.

Drafting prompt (LAW):
```
System: You write replies to inbound leads on behalf of {AGENCY_NAME}.
Use ONLY the facts in CONTEXT. Never invent services, prices, or timelines.
If CONTEXT lacks something the lead asked, say a specialist will confirm it.
Mode "reply": respond to the inquiry, reference their need, propose a short call. Under 150 words.
Mode "followup": polite nudge referencing their original message, one line of value, re-offer the call. Under 80 words.
Return ONLY JSON: {"subject":"...","body":"..."}
User: MODE: {mode}\nCONTEXT:\n{chunks}\nLEAD MESSAGE:\n{message}\nLEAD NAME: {name}
```

7. `services/embeddings.py`: add `EMBEDDINGS_PROVIDER=local|api` switch; `api` = stub raising NotImplementedError (implement only if Render OOMs).
8. `scripts/seed.py`: ingest `data/acme/*` → parse → chunk → embed → insert. Stringify embedding before pgvector insert (known trap).
9. Tests (no network; mock LLM + retrieval): every rule + pass-through; fence-wrapped LLM output; empty-retrieval path.

`[MANUAL]`: Supabase project + run schema SQL; write the 4 Acme docs YOURSELF (`services.md`, `pricing.md` with explicit tiers e.g. PPC $2.5k–5k/mo, `faq.md`, `case_studies.md`); fill `.env`; `python scripts/seed.py`.

**DoD:**
```bash
python -m pytest -v
# hot lead → verdict hot, rule_triggered null:
curl -s -X POST localhost:8000/score -H 'Content-Type: application/json' -d '{"name":"Sarah","email":"sarah@realco.com","company":"RealCo","message":"We need Google Ads for our property listings, budget around $3k/month, can we talk this week?","budget":"$3k/month"}'
# spam → rule_triggered spam_pattern, NO Groq call in logs:
curl -s -X POST localhost:8000/score -H 'Content-Type: application/json' -d '{"name":"x","email":"x@mailinator.com","message":"buy backlinks cheap"}'
# draft quotes real pricing from pricing.md, sources_used non-empty:
curl -s -X POST localhost:8000/draft -H 'Content-Type: application/json' -d '{"lead":{"name":"Sarah","email":"sarah@realco.com","message":"Need Google Ads help, ~$3k/month budget"},"mode":"reply"}'
```
By day 3: deploy brain to Render; if OOM → flip `EMBEDDINGS_PROVIDER=api`, implement stub next session.

## PHASE 2 — n8n happy path — `[MANUAL]` (CC writes nothing unless a reshape helper proves necessary)

`docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n`
Docker cannot reach localhost:8000 — use `http://host.docker.internal:8000` or the Render URL.

Nodes in order: **Webhook** (POST `/lead`) → **HTTP /score** (map body fields, e.g. `{{ $json.body.name }}`) → **IF** verdict in [hot, warm] (FALSE → Sheets append status `rejected`, end) → **HTTP /draft** → **Slack** notify (name/company, verdict+score, draft) → **Gmail/SMTP** send → **Sheets** append.

Sheet columns (create exactly): `timestamp | name | email | company | message | verdict | score | status | nudge_count | replied`

Webhook test:
```bash
curl -X POST http://localhost:5678/webhook-test/lead -H 'Content-Type: application/json' -d '{"name":"Sarah","email":"sarah@realco.com","company":"RealCo","message":"Need Google Ads, $3k/month budget","budget":"$3k/month"}'
```
**DoD:** hot lead → email + Sheet row + Slack ping. Spam lead → rejected row only.

## PHASE 3 — Follow-up + approval — `[MANUAL]`

After send: **Wait** (2 min testing / 3 days live) → Sheets lookup → IF `replied==TRUE` end → IF `nudge_count>=2` set status `cold`, end → **HTTP /draft** `mode:followup` → send → increment `nudge_count` → back to Wait.
`replied` is a manual Sheet flag in v1. Automated reply detection = v2 upsell, DO NOT BUILD.
Approval: Slack interactive button, timeboxed to half a day; sanctioned fallback = `pending` Sheet tab + Schedule-node poller sends rows flipped to `approved`.
**DoD:** unanswered lead nudged twice on test timer then `cold`; flipping `replied` stops the loop; nothing sends without approval.

## PHASE 4 — Eval harness

1. `[CC]` `eval/leads.csv`: 30 leads (10 hot, 8 warm, 6 cold, 6 spam/edge — gibberish, competitor fishing pricing, unoffered service, $50 budget, disposable-domain valid-looking, ALL-CAPS spam). Columns: `id,name,email,company,message,budget,expected_verdict`.
   **User then reviews and corrects expected verdicts by hand — the answer key is human judgment.**
2. `[CC]` `eval/run_eval.py`: fire each at /score (1s sleep, exponential backoff on 429) → `eval/report.md`: overall accuracy, per-class precision/recall, confusion matrix, headline **spam_or_cold_classified_as_hot rate**, list of misclassifications with reasons.
3. Manual: run all 30 through /draft, eyeball every body for invented services/prices; fix prompts; re-run.
**DoD:** `python eval/run_eval.py --url ...` → publishable numbers. Under ~85% accuracy → iterate the prompt. Never delete hard cases to inflate the score.

## PHASE 5 — Deploy + demo + post

1. `[CC]` Final `render.yaml`; health check `/health`; confirm `.env` gitignored; secrets only in Render dashboard.
2. `[MANUAL]` Deploy → repoint n8n HTTP nodes at Render URL → rerun Phase 2+3 DoD against prod → hit `/health` before recording (cold start).
3. `[MANUAL]` 3-min Loom: hot lead → Slack draft → approve → email lands → Sheet row → follow-up on short timer. One take.
4. `[MANUAL]` LinkedIn case-study post: the problem (slow lead response kills deals), the build, the eval numbers, the Loom link, free-install-for-3-agencies-for-testimonial offer.
**DoD:** live URL + published video + published post. Day 14 ships regardless of polish.

## EXCLUDED FROM V1 (building any of these = scope violation)
Gmail trigger, multi-tenant, any custom frontend/UI, automated reply detection, CRM integrations beyond Sheets, Vercel or any second hosting platform.

## PITFALLS QUICK TABLE
| Symptom | Fix |
|---|---|
| pgvector can't cast list → vector(384) | stringify embedding before insert |
| Supabase access blocked | service role key, not anon |
| Render OOM on boot | sentence-transformers > 512MB free tier → `EMBEDDINGS_PROVIDER=api` |
| First prod request 60s+ | free-tier cold start → warm `/health` first |
| n8n node gets undefined | check exact JSON path in previous node's output tab |
| LLM JSON parse errors | strict prompt, strip fences, retry once |
| Groq 429 during eval | sleep + backoff in eval script |
Debug rule: reproduce with one curl before touching n8n; decide brain (code) vs plumbing (node config) before changing either.

## AFTER DAY 14 — GO-TO-MARKET
Loom + one-page site (Carrd/Notion) + rewritten LinkedIn headline → 50 personalized cold messages to small agencies (foreign AND local), free-install-for-testimonial, need 3 yeses → per install: testimonial + permission + one number → content 2–3x/week (case studies, failures-and-fixes, free n8n template as lead magnet) → month 2–3: paid fixed-scope installs ($300–500, rising), Upwork profile with Loom from day 1.

---

## PROGRESS.md TEMPLATE (create in repo root at Phase 1 start; CC updates at every session end)

```markdown
# LeadPilot Progress

## Current phase: <N>
## Last session: <date> — <one-line summary>

## Done & DoD-VERIFIED (user ran the commands)
- [ ] Phase 0: /health live on Render — URL: ___
- [ ] Phase 1: pytest green; 3 DoD curls pass; brain deployed, memory OK / OOM→api fallback
- [ ] Phase 2: happy path end-to-end (email + Sheet + Slack)
- [ ] Phase 3: follow-up loop + approval verified
- [ ] Phase 4: eval report — accuracy: __%, spam-as-hot: __%
- [ ] Phase 5: prod URL + Loom + LinkedIn post published

## Done but NOT yet verified
- <task>: <what still needs the user's DoD run>

## Known issues / open bugs
- <issue>: <symptom, suspected zone (brain vs plumbing), what was tried>

## Decisions made (so future sessions don't relitigate)
- <e.g. EMBEDDINGS_PROVIDER=local, fits in Render memory as of day 3>

## Next task
- <exact next numbered task from PLAN.md>
```
