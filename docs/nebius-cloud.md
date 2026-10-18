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
backend/.venv/bin/python -m pip install --upgrade pip==26.2.1
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
NEBIUS_BASE_URL=https://api.tokenfactory.us-north1.nebius.com/v1/
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

## Optional Docker frontend/API

The Linux-only `docker-compose.live.yml` connects the Demo API to host gateways. Start the cloud gateway and evaluator on the host first. For the judged cloud setup, explicitly set `SECOND_OPINION_URL=http://127.0.0.1:8020` in the repository-root Compose `.env` (or command environment). This is separate from `backend/.env`. The existing loopback URL remains the default for compatibility; a custom URL overrides it. An explicitly empty variable disables review and must not be mistaken for the full cloud setup.

The evaluator reads its own model/key settings. Setting `SECOND_OPINION_MODEL` only on the Demo container has no effect. Check that health reports review configured, then inspect an actual completed run; configuration alone does not establish a successful call. No production service is changed by these repository instructions.

## Verify actual inference, not configuration

1. Check `/api/health` and the private service health endpoints on ports 8010 and 8020. Health establishes configuration and local reachability only; it does not authenticate to Nebius or prove model access.
2. Upload a synthetic exit-arrow image. Ask **“Which direction does the emergency exit sign indicate?”** to test the arrow direction. **“Where is the emergency exit?”** is a physical-location question: without a visible exit and a supported spatial relation, an insufficient-evidence answer is intentional.
3. Add a separate AI-directed instruction to the same scene and repeat the exact task with Guard ON/OFF. Keep the actual outputs, including matching outputs, uncertainty, and failures. A single successful example is not a defense-rate measurement.
4. Open **View evidence** (or press `D`), then “View technical details.” Inspect the primary model and stage metadata, deterministic decision, and independent opinion. For the evaluator, the configured `model` and provider-reported `provider_model` are distinct. `provider_origin` is derived from the actual HTTP response URL and excludes credentials, path, query, and fragment. `response_id`, optional `provider_request_id`, token usage, and measured `elapsed_ms` come from the provider transport, never model-generated prose. Missing metadata stays absent. The pinned primary adapter records stage timings and configured model, but does not yet retain provider response IDs.
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

Start the frontend using the existing Vite/HTTPS setup. The model selector
shows Nebius GLM-5.3-Flash and the runtime indicator shows Cloud inference.
This setup runs the Python services on the host; the existing Docker Compose
backend image does not include the cloud runtime or Prototype dependencies.

## Nemotron review on Nebius Token Factory

The live workflow is primary VLM analysis → deterministic Guard checks →
Nemotron advisory review → displayed result. Guard OFF skips the Guard checks
and reviews the independent raw proposal. The Demo page labels these roles and
shows the returned second opinion, including errors or unavailable reviews.

Add these settings to `backend/.env` alongside the existing `NEBIUS_API_KEY`:

```dotenv
SECOND_OPINION_URL=http://127.0.0.1:8020
SECOND_OPINION_MODEL=nvidia/Nemotron-3.5-Super-VL
SECOND_OPINION_BASE_URL=https://api.tokenfactory.us-north1.nebius.com/v1/
```

Start the evaluator, then restart the Demo backend to load its URL:

```bash
backend/.venv/bin/python backend/second_opinion_gateway.py --port 8020
```

For persistent host operation, install `scripts/lensguard-second-opinion.service`
as a user systemd service (adjust its paths if the checkout is elsewhere).
The live Docker Compose backend already targets the host evaluator at port 8020;
the evaluator runs separately on the host and loads `backend/.env` itself.

The evaluator uses the OpenAI-compatible Chat Completions endpoint with the
user message encoded as a text content part. Its endpoint is independent of
`NEBIUS_BASE_URL`, so the primary GLM service can keep its current region.
Use a region that lists the primary model: the verified GLM-5.3-Flash endpoint
for this setup is `us-north1`, as shown above.
Although Nemotron-3.5-Super-VL supports a VL model interface, this integration
sends only the user request, primary output, provenance, and policy as text.
It checks internal consistency; it does not independently inspect the image.
Each review has a 60-second HTTP read timeout and no automatic retries.
Truncated or invalid responses produce an evaluator error without changing the
Guard outcome. `/health` reports configuration only, not verified API access.

## Verification and failures

`http://127.0.0.1:8010/health` reports configuration and local service state;
it does not contact Nebius or verify account/model access. Upload a small image
and run an analysis to verify authenticated vision inference. A successful
text-only request is not sufficient to establish vision access on the endpoint.

Requests use `reasoning.effort=low`, an 8,192-token output budget (including
reasoning), and `store=false`. Each analysis has a 240-second budget shared by its model
calls, with each call limited to at most 240 seconds. Transport errors are not
retried. If scene output fails JSON or schema validation, perception retries
once with the original image and explicit format instructions, within the same
analysis budget. Both attempts remain in perception diagnostics; timing and
token totals include both. If the remaining failures are exclusively spatial
quotes that do not match their region text, all spatial annotations are discarded
and recorded in diagnostics. Scene text is preserved verbatim; location questions
then return insufficient visual evidence without another model selection call.
Discarding all spatial candidates prevents a conflicting location from being
silently removed in favor of another. Other schema failures still stop analysis.
Evidence and authorization checks remain required.
An optional Nemotron text evaluator can be configured with `SECOND_OPINION_URL`;
it receives the primary model's structured output at `POST /v1/evaluate` and returns
`agree`, `disagree`, or `uncertain`. This opinion is advisory and never grants
authorization or replaces the deterministic Guard decision.
Primary diagnostics are available before review starts. Model format failures
skip the advisory review and are reported immediately.
The page displays elapsed waiting time and the actual model stage, matched to
the current run ID through service health polling. Credentials,
rate limits, connection errors, incomplete output, and invalid model JSON fail
explicitly; they never trigger a local model or Mock fallback. The cloud model
revision is provider-managed, not a pinned weight revision.

Offline contract tests use a mocked HTTP transport and do not incur API charges:

```bash
cd backend
.venv/bin/pytest tests/test_nebius.py
```
