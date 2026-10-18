# LensGuard preregistered 8-case comparison

This optional evaluation package is separate from the application and does not alter production code. It compares the complete deployed Guard ON and Guard OFF systems. It does not isolate a causal gate effect, estimate real-world security performance, or verify camera capture.

## Frozen inputs

manifest.json fixes eight synthetic images, exact requests, expected content and authority, denominators, paired run order, and the maximum of 16 POST requests. manifest.sha256 and per-image hashes protect the freeze. The initial 10 captured live runs remain a separate baseline and are not counted here. Cases were authored before execution without response-based revisions.

## Offline use

Run `python run_live.py` to validate the manifest and image hashes without network access. Run `python validate_evidence.py` to check collected result integrity and completeness. These checks do not declare model accuracy or authorization correctness.

Images are already included. `generate_fixtures.py` documents reproducible rendering and uses Pillow plus DejaVu Sans. Regeneration in a different font/library environment may change bytes and will fail the manifest hash check; do not replace frozen inputs. `freeze_manifest.py` is the original one-time preregistration script and refuses to overwrite an existing manifest.

## Live execution is opt-in

`python run_live.py --execute-live` submits images to the exact public Demo endpoint in the manifest. Use only with permission to test that service. The deployed service may incur its own inference costs. The script does not request, store, or transmit API keys and does not configure model providers. All tested calls are simulated; this package does not connect to telephony.

The runner writes a durable attempt marker before each POST, never retries an uncertain POST, and skips completed attempt markers. A submission error stops all later POSTs; rerunning with an unresolved error marker or without a valid terminal result also stops for inspection. GET polling can be retried safely for transient failures, within a 600-second observation window. Nonretryable HTTP 4xx (except 408/429) or an elapsed retrieval deadline writes an inconclusive observation artifact and stops the suite without more POSTs; it does not falsely label inference as failed. The original completed evidence is not overwritten by rerunning this script; use a separately preregistered evaluation if an actual fresh replication is intended. Do not delete markers to selectively rerun favorable or failed examples.

## Evidence and interpretation

runs/ holds exact terminal server JSON, initial responses, exact request metadata, and client wall times. Server per-stage timing is available in the terminal JSON. execution.log records chronological results. The final report and adjudication describe every case, including failures, abstentions, baseline successes, reviewer limitations, and absent provider-level routing proof.

Coverage omissions include physical scenes, actual camera permission/capture, repeated-trial variance, same-target multiple phone numbers, benign-looking malicious contact substitution, real ownership authentication, and a broader adaptive attack suite. Eight authored fixtures cannot establish universal protection.

`build_report.py` rebuilds the report for the archived, adjudicated Run IDs only. It verifies terminal-response hashes from adjudicated_response_hashes.json before applying the recorded semantic outcomes. It is not a generic accuracy scorer for new runs. A fresh replication requires fresh adjudication against the same preregistered criteria.
