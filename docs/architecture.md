# LensGuard architecture

## Execution boundary

The React client freezes an image, user request and model selection. The Demo API stores a bounded in-memory run and streams immutable snapshots through SSE. It talks to the Prototype over a versioned HTTP contract; the Prototype remains a separately pinned repository.

In **cloud mode**, `backend/cloud_gateway.py` imports that pinned Prototype runtime and supplies its Nebius adapter. GLM-5.3-Flash handles three independent Guard ON conversations:

1. Parse the user request without seeing the image.
2. Observe the image and transcribe scene text.
3. Select quotations from those existing records.

Deterministic code then checks task scope, exact citations and complete values. It returns an informational answer, a simulated action or a stop. Citation consistency does not establish the authenticity of a sign or ownership of a phone number. See [task boundary](task-boundary.md).

The optional `second_opinion_gateway.py` sends the structured primary result and citations to a configured NVIDIA Nemotron through Nebius Token Factory. This is **text-only advisory review**. It does not receive the image and cannot alter the deterministic authorization decision. The UI retains agreement, disagreement, uncertainty and failures.

In **local GPU mode**, `model_gateway.py` owns one Nemotron Nano VL or Cosmos worker at a time. It stops only its own previous worker before switching models, preserves GPU ownership during client cancellation, and rejects a response from another selected model. See [local operation](nvidia-demo.md).

In **Mock mode**, fixed JSON scenarios supply all results. Model failures never switch modes automatically.

## Presentation and comparison

The four stages are Observe, Distinguish, Decide and Protect. Presentation adapters consume run state; they do not make authorization decisions. Selected evidence and rejected instructions are shown with their actual model-derived content. Missing coordinates do not become fabricated detection boxes.

Guard ON/OFF share a frozen image, request and primary model choice but make separate inferences. Guard OFF preserves the original proposal. Matching answers, abstentions and errors remain visible; the UI does not infer a successful attack from a scenario label. Calls and every other external action remain simulated.

Replay uses existing results without another model call. Reset clears client state and disconnects the stream; it does not cancel in-flight provider generation. SSE reconnect resumes the existing run.

## Storage, privacy and resource limits

There is no database. Completed runs are evicted oldest-first at the configured capacity and cleared on process restart. Uploaded bytes are used for one inference; the Prototype removes its temporary file afterward. Raw output and metadata remain in bounded in-memory history and can contain personal information, so use synthetic or publishable material for judging.

Request-body limits apply while receiving, before an oversized upload can fully spool, including chunked bodies. Per-image and decoded-pixel limits still apply independently. Concurrent runs are bounded, but the research demo has no account authentication, tenant isolation or global provider-spend quota. Keep model gateways on loopback and use an appropriate access-controlled proxy before exposing an unattended service.

Provider endpoint settings come only from server configuration, not image/model output. No proposed URL is fetched and no proposed phone number is dialed. Responses do not follow redirects. Failure diagnostics expose status/type, not arbitrary transport errors. Successful model/parser evidence is preserved for inspection.

[Cloud setup](nebius-cloud.md) · [API fields and limits](api-contract.md) · [Operations and HTTPS](development.md) · [Verification](verification-2026-10-18.md)
