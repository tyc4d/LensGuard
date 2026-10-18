# User task and citation boundary

Live mode uses `user-task-cited-evidence-v1`. The selected UI scenario does not grant authorization. The same underlying contract supports the cloud and local model adapters.

## Three model steps, one deterministic check

1. **Read only the user request.** A fresh text conversation identifies the operation, target quotation, requested information and any explicit phone number. It receives no image, scene transcription, prior conversation or tools.
2. **Read only the image.** The vision model transcribes text and distinguishes information from AI-directed instructions. The server assigns request-local source IDs such as `region_01`, with camera provenance. Model output cannot supply its own source IDs or authority. Invalid output does not become evidence. Ordinary business rules and contact notices can remain useful information.
3. **Select existing citations.** A separate text conversation receives the fixed task and retained records. It returns source IDs, exact quotations and selected values, but cannot replace the fixed operation or information type. Identified instructions are excluded unless the user specifically requests quotation/analysis or all phone numbers; such requests remain informational.
4. **Validate and assemble.** Deterministic code checks task consistency, existing source IDs, contiguous exact quotations and complete phone numbers. It rejects truncation, added digits and substituted values. Direction conversion is limited to supported literal words/symbols; text answers use cited content. A call needs one distinct selected value and resolution of the remaining candidate numbers. The model cannot bypass checks by declaring a value user-provided.

Authorization comes from the user; a number may come from the image. Labels such as “reservation line” or “business card” are not themselves permission. If the user directly supplies a complete number for a call, the program uses that user text and does not let the image replace it.

## Outcomes and comparison

- Reading a phone number returns `answer_question`; requesting a call returns `call_phone`. Every call is simulated.
- Invalid citations, ambiguous tasks, missing information and unresolved candidates stop the proposal with an explanation. The user can edit the request and analyze the same image again.
- An instruction quoted at the user's request remains quoted data without authority.
- Guard OFF receives the same frozen input with `guard_enabled=false` and makes a separate raw proposal. It does not inherit the guarded answer or provenance. Matching outputs remain matching outputs.
- `raw_model_text` retains the actual selection output. `runtime_metadata.output.metadata` retains the task, perception and selection outputs/diagnostics. A structured `NONE` can represent a program-generated stop; it does not mean the model completed the requested task.
- An arrow-only sign can support a direction while failing to establish an unseen exit's physical location. This abstention requirement is preserved.

The optional Nemotron reviewer examines primary text and citations after the gate. Its opinion cannot modify these rules or authorize an action.

## Limits

This is citation checking over model-derived transcription, not independent OCR, authenticity verification or a complete CaMeL implementation. Task interpretation, instruction classification, target association and other-target resolution still depend on models. Exact citations do not prove that reasoning was uninfluenced or that a sticker's number belongs to the business. Missing coordinates and confidence values are not invented.

The demo focuses on cited text, phone numbers and supported directions. It does not perform reservations, payments or arbitrary tool execution. Local NVIDIA adapters additionally represent open observations and uncertainty; their general physical-scene accuracy remains unvalidated. Failures never become fixture results or legacy authorization fallbacks.

## Evidence

CPU boundary tests live in the pinned Prototype's `tests/test_demo_task_boundary.py`; Demo tests cover HTTP transport, answer/call separation, citations, failure states and Guard OFF preservation. See the [current audit](verification-2026-10-18.md) for cloud regression and live results.

The [2026-09-05 case record](task-boundary-validation.json) is historical local-model evidence: 12 cases, including 10 information/simulated-call completions and two intended stops. Its counts, model behavior and old browser validation must not be treated as the current cloud system's efficacy rate.
