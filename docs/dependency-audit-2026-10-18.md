# Dependency audit — 2026-10-18

The scan checked installed Python release versions against the public PyPI vulnerability records, and the frontend lockfile with `npm audit`. Duplicate CVE/PYSEC aliases are not counted as separate defects. An advisory match is not proof that its vulnerable feature was reachable in LensGuard.

| Package | Before | Pinned repair | Evidence and scope |
| --- | --- | --- | --- |
| Starlette | 0.47.3 | 1.3.1 | [Form-parser limits](https://github.com/Kludex/starlette/security/advisories/GHSA-82w8-qh3p-5jfq), fixed in 1.3.1; also includes fixes for host/path parsing and older FileResponse advisories. LensGuard does not serve files through Starlette. |
| FastAPI | 0.116.1 | 0.135.1 | Compatibility update: the old pin excludes patched Starlette releases; the new version supports the selected Starlette and existing Pydantic. No FastAPI advisory was returned for this version. |
| python-multipart | 0.0.22 | 0.0.31 | [Upstream advisories](https://github.com/Kludex/python-multipart/security/advisories), including GHSA-mj87-hwqh-73pj (0.0.26), GHSA-pp6c-gr5w-3c5g (0.0.27), GHSA-5rvq-cxj2-64vf/GHSA-6jv3-5f52-599m (0.0.30), and [GHSA-v9pg-7xvm-68hf](https://github.com/Kludex/python-multipart/security/advisories/GHSA-v9pg-7xvm-68hf) (0.0.31). The last affects direct parse_form callers, which FastAPI/Starlette are not. |
| python-dotenv | 1.1.1 | 1.2.2 | [GHSA-mf9w-mj56-hr94](https://github.com/theskumar/python-dotenv/security/advisories/GHSA-mf9w-mj56-hr94), fixed in 1.2.2. LensGuard reads environment files; it does not use the vulnerable set_key writer. |
| pytest | 8.4.1 | 9.0.3 | [PyPI advisory metadata](https://pypi.org/pypi/pytest/8.4.1/json): GHSA-6w46-j5rx-g56g, fixed in 9.0.3. Test dependency, not an inference capability. |
| source-map-js | 1.2.1 | 1.2.2 | [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q), fixed in 1.2.2. Lockfile-only compatible update. |

The local audit virtual environment initially had pip 25.0.1. Only the project virtual environment, documented clean-install step and Docker build bootstrap use pip 26.2.1; no machine-global pip was changed. The pip bootstrap is tooling, separate from application dependencies.

After repair, all **30 installed Python packages** returned no known advisories in the queried PyPI release records, with no query errors. Frontend `npm audit` returned **0 vulnerabilities**. These are dated database checks, not a guarantee against unknown vulnerabilities or a claim about already-deployed server packages.

Compatibility: the repaired backend suite passes on the updated stack, and frontend build/data checks pass after the lockfile update. Exact revision-specific totals and fresh-copy/browser results are in the [verification report](verification-2026-10-18.md). GPU model environments and the pinned Prototype source are unchanged. Docker engine execution is not available in this cloud workspace, so a rebuilt container has not been runtime-tested here.
