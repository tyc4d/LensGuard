# Nebius GLM-5.3-Flash cloud inference

All model stages use `zai-org/GLM-5.3-Flash` through Nebius Responses API:
user-only task parsing, image perception, and citation selection. Guard OFF
sends one independent image-and-task request to the same model. The existing
deterministic citation and authorization checks remain in the Prototype service.
No CUDA, PyTorch, model weights, or local GPU is required. Uploaded images and
task text are sent to Nebius; this mode is not offline.

## Setup

The `prototype/` submodule must contain the cloud adapter changes as well as
the Demo changes. A checkout of the previous pinned Prototype commit does not
include them. Do not discard its working-tree changes when switching versions.

From the Demo root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-cloud.txt
```

Set these values in `backend/.env` (keep any existing unrelated settings):

```dotenv
LENSGUARD_RUNTIME=prototype
PROTOTYPE_RUNTIME_URL=http://127.0.0.1:8010
INFERENCE_TIMEOUT_SECONDS=300
NEBIUS_API_KEY=your_private_key
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_MODEL=zai-org/GLM-5.3-Flash
```

Keep the key server-side and out of Git and frontend environment variables.
The cloud gateway loads `backend/.env` first, then the root `.env` for missing
values; existing process environment variables take precedence over both.
Start the cloud service instead of the NVIDIA local gateway:

```bash
backend/.venv/bin/python backend/cloud_gateway.py
```

In another terminal, start the Demo backend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend using the existing Vite/HTTPS setup. The model selector
shows Nebius GLM-5.3-Flash and the runtime indicator shows Cloud inference.
This setup runs the Python services on the host; the existing Docker Compose
backend image does not include the cloud runtime or Prototype dependencies.

## Verification and failures

`http://127.0.0.1:8010/health` reports configuration and local service state;
it does not contact Nebius or verify account/model access. Upload a small image
and run an analysis to verify authenticated vision inference. A successful
text-only request is not sufficient to establish vision access on the endpoint.

Requests use `reasoning.effort=low`, an 8,192-token output budget (including
reasoning), and `store=false`. Each analysis has a 240-second budget shared by its model
calls, with each call limited to at most 240 seconds and no automatic retries.
An optional independent text evaluator can be configured with `SECOND_OPINION_URL`;
it receives the primary model's structured output at `POST /v1/evaluate` and returns
`agree`, `disagree`, or `uncertain`. This opinion is advisory and never grants
authorization or replaces the deterministic Guard decision.
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
