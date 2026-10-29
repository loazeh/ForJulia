# Observed issues and lessons

1. The first Docker/GitHub probes were blocked by the execution sandbox; access worked in the approved execution context. This was a tool-access issue, not an application failure.
2. Git initially waited on the credential manager despite GitHub CLI being authenticated. Configuring Git with `gh auth setup-git` enabled the repository push.
3. The initial test build passed 16 tests and failed the nonfinite-input test. JSON `1e999` parsed as infinity; validation rejected it, but the default error response tried to serialize infinity and raised ValueError. A custom validation handler now returns only type, location, and message, producing HTTP 422. The rerun passed all 17 tests.
4. The current Starlette test client reports an httpx deprecation warning. Tests pass; it concerns the development test transport, not the deployed API. A future dependency refresh should migrate the test transport together with its lockfile.

The most useful automation is the sequence of lint, tests, container build, scan, smoke test, and publication. Main's required checks prevent merging before that sequence succeeds. Model hashes identify loaded artifacts; fixed seeds and pinned dependencies support repeatable predictions but do not guarantee byte-identical files across all hardware.
