# Live evaluation evidence

Both cohorts exercised the existing public deployment before the repair was deployed. They used synthetic images and fictional phone numbers; all calls were simulated.

- [Exploratory acceptance](exploratory-2026-10-18/LensGuard_Live_Acceptance_Report.md): 10 captured runs, including the original location-question abstentions. These prompted clearer sample wording.
- [Preregistered paired comparison](heldout-v1/LensGuard_Preregistered_Comparison_Report.md): eight frozen cases, 16 runs. Full-workflow expected outcomes matched ON8/8 and OFF7/8. The only difference was an ambiguous-target simulated call; both modes resisted the two explicit instruction-injection cases.

Do not pool the cohorts into an attack-success rate. The second compares complete ON/OFF workflows, not the isolated causal effect of the gate. Neither provides physical-camera efficacy, repeated-trial variance or a universal defense claim. Raw traces, exact requests, input hashes, failures and limits accompany the reports.

The optional runner defaults to offline verification. Live requests need an explicit flag and permission to test the target service; they may consume the deployment's inference quota. Provider response IDs/routing proof are absent from these old-deployment traces.
