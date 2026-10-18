# LensGuard paper source

This is an in-place iteration of the original six-page LensGuard manuscript. The original authors, section order, page template, body type size, historical data and photographic figures are preserved. The runtime description and acceptance evidence were updated on 18 October 2026. This is not a replacement paper or an addendum.

## Build

Use pdfLaTeX (TeX Live with newtx, tex-gyre, kastrup and the standard packages named in `tex/preamble.tex`). Set `main.tex` as the main document in Overleaf, or run:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

No shell escape, model inference, credentials, or network access is required by the manuscript build. The historical charts are already included. `analysis/make_historical_smoke_chart.py` can regenerate Figure 2 with its explicitly historical title; `analysis/make_physical_charts.py` improves Figure 6 label legibility using the unchanged historical aggregates. Both scripts require numpy and matplotlib and do not run inference.

## Evidence and versions

- September synthetic, physical, survey and local-runtime results are historical, not GLM/Nemotron cloud performance measurements.
- `data/historical_runtime_2026-09-07.json` retains the earlier local-runtime record and test counts.
- The October cloud source inspected was LensGuard `a61c7d8292f5105865723cd0b388e55ab0863036` with Prototype `fc5003faebc0f51bd6b8959ab03ee5af0dac7400`. The live service did not expose its deployed commit.
- Current repair checks and pre-deployment live acceptance are separate evidence layers. See `../../docs/verification-2026-10-18.md`.
- No private survey emails or complete historical human-label/raw-response dataset is included.

## Original-source recovery

See `source-recovery.json` for archive/PDF hashes and the limited reconciliation needed to match the published September version. The original PDF remains in repository history at `a61c7d8`. Recovered source is an actual prior authoring project, not a manuscript reverse-engineered from scratch. Compiler versions can alter line wrapping and binary PDF hashes.
