# Nebius Token Factory cloud inference

LensGuard can run on a CPU host with cloud inference on Nebius Token Factory:

- **Primary vision model:** `zai-org/GLM-5.3-Flash` via the Responses API. It interprets the user-only task, observes the image, and selects existing citations in separate calls.
- **Independent Nemotron text evaluator:** `backend/second_opinion_gateway.py` calls a configured NVIDIA Nemotron model via Chat Completions. It reviews the primary model's structured output and cited text, not the original image. Set `SECOND_OPINION_MODEL` to the Nemotron model available on your endpoint. The repository default is `nvidia/Nemotron-3-Ultra-550b-a55b`; this is a configuration default, not evidence that a deployed server ran it.
- **Deterministic Guard:** the existing Prototype checks citations, grounding, task scope, and action authorization. The Demo displays that decision unchanged. An evaluator's `agree`, `disagree`, `uncertain`, timeout, or failure cannot grant authority or override the decision.

The actual service order is primary model stages → deterministic Prototype checks → advisory evaluator → Demo display. The evaluator is an additional diagnostic layer, not a replacement for the gate. Guard OFF makes one independent primary request and can also receive an advisory review; its authorization checks remain bypassed for the simulation.

No CUDA, PyTorch, downloaded weights, or local GPU is required. Images and task text go to Nebius for primary inference; structured primary output and the user task go to the configured evaluator, which sends them to Nebius. All calls/actions in the demo are simulated. Use synthetic or appropriately authorized images.

## Reproducible setup

The committed `prototype/` gitlink is `fc5003faebc0f51bd6b8959ab03ee5af0dac7400`, which includes `prototype_demo_server/nebius.py`. A clean recursive checkout contains the adapter; uncommitted submodule edits are not required.

```bash
git clone --recurse-submodules https://github.com/tyc4d/LensGuard.git
cd LensGuard
git submodule status
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-cloud.txt
npm --prefix frontend ci
cp backend/.env.example backend/.env
```

Set these values in `backend/.env`, preserving unrelated settings:

```dotenv
LENSGUARD_RUNTIME=prototype
PROTOTYPE_RUNTIME_URL=http://127.0.0.1:8010
INFERENCE_TIMEOUT_SECONDS=300
NEBIUS_API_KEY=your_private_key
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_MODEL=zai-org/GLM-5.3-Flash
SECOND_OPINION_URL=http://127.0.0.1:8020
SECOND_OPINION_MODEL=nvidia/Nemotron-3-Ultra-550b-a55b
```

Use a Nemotron model your Token Factory account actually supports; do not assume model access from a label or health endpoint. The primary and evaluator currently use the same Nebius key/base URL. Keep credentials server-side, out of Git, frontend variables, logs, screenshots, and submission artifacts. Leave `SECOND_OPINION_URL` empty only when intentionally running without the independent evaluator; the UI reports it as not configured.

Start each service in a separate terminal from the repository root:

```bash
# Primary cloud inference and deterministic Prototype checks, port 8010
backend/.venv/bin/python backend/cloud_gateway.py

# Independent Nemotron evaluator, port 8020
backend/.venv/bin/python backend/second_opinion_gateway.py

# Demo API, port 8000
(cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000)

# Frontend, port 5173
(cd frontend && VITE_HTTPS=false VITE_API_BASE_URL=/api \
  API_PROXY_TARGET=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1)
```

Gateways load `backend/.env` first, then the root `.env` for missing values; existing process variables take precedence. This is a host-based setup. The existing Docker Compose backend image does not include the cloud gateway or Prototype dependencies.

## Verify actual inference, not configuration

1. Check `/api/health` and the private service health endpoints on ports 8010 and 8020. Health establishes configuration and local reachability only; it does not authenticate to Nebius or prove model access.
2. Upload a synthetic exit-arrow image. Ask **“Which direction does the emergency exit sign indicate?”** to test the arrow direction. **“Where is the emergency exit?”** is a physical-location question: without a visible exit and a supported spatial relation, an insufficient-evidence answer is intentional.
3. Add a separate AI-directed instruction to the same scene and repeat the exact task with Guard ON/OFF. Keep the actual outputs, including matching outputs, uncertainty, and failures. A single successful example is not a defense-rate measurement.
4. Press `D`, then open “View technical details.” Inspect the primary model and stage metadata, deterministic decision, and independent opinion. For the evaluator, the configured `model` and provider-reported `provider_model` are distinct. `provider_origin` is derived from the actual HTTP response URL and excludes credentials, path, query, and fragment. `response_id`, optional `provider_request_id`, token usage, and measured `elapsed_ms` come from the provider transport, never model-generated prose. Missing metadata stays absent. The pinned primary adapter records stage timings and configured model, but does not yet retain provider response IDs.
5. Check both run IDs in the comparison. The evaluator's actual model can differ from an old page caption or repository default; the returned run evidence is what matters.

The origin and provider IDs are server-reported correlation evidence, not cryptographic proof. They can be checked against provider-side records where available. A healthy local service or a model name alone is not authenticated inference evidence.

## Timeouts and failures

Primary requests use `reasoning.effort=low`, an 8,192-token output budget including reasoning, and `store=false`. Each primary analysis has a shared 240-second budget and no automatic retries. The evaluator uses a separate 60-second HTTP timeout, a 1,200-token output limit, and no automatic retries. Its token limit, latency, and availability may need tuning based on the selected model; incomplete responses are errors, not successful opinions.

The page shows elapsed time and primary stages correlated with the current run ID, then an explicit independent-review stage. Evaluator failure remains visible and does not alter the already-computed deterministic decision. Primary credentials, rate limits, connection errors, incomplete output, and invalid JSON fail explicitly; they never trigger a local-model or Mock fallback. Cloud model revisions are provider-managed.

## Offline regression checks

These tests use mocked transports and make no paid model requests:

```bash
(cd backend && .venv/bin/python -m pytest -q)
npm --prefix frontend run build
(cd frontend && npx playwright install chromium && PLAYWRIGHT_ISOLATED=true npm test)
```

If a compatible Chromium is already installed, `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/path/to/chromium` selects it for Playwright. This is optional and does not change application behavior. See the [2026-10-18 audit](verification-2026-10-18.md) for actual passed checks, live observations, and execution blockers.
