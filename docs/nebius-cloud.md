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
NEBIUS_BASE_URL=https://api.tokenfactory.us-north1.nebius.com/v1/
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
