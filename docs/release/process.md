# BIMoryn — Release Process

## Overview

Releases follow semantic versioning (`MAJOR.MINOR.PATCH`). Every tagged release
automatically triggers the release pipeline: Docker image build, push to GHCR,
and a GitHub release with auto-generated changelog.

## CI/CD Architecture

```
PR opened
  └─ ci.yml
       ├─ lint (ruff)
       ├─ tests (py3.11 + py3.12, coverage ≥ 70%)
       └─ docker build smoke-test

Merge to main
  ├─ ci.yml (same checks)
  └─ benchmark.yml
       ├─ generate fixtures (small + medium)
       ├─ run benchmarks (2 repeats)
       └─ regression check vs committed baseline (20% threshold)

Tag push  v*.*.*
  └─ release.yml
       ├─ generate changelog (git log since previous tag)
       ├─ docker buildx build + push → ghcr.io (semver + latest tags)
       └─ create GitHub release with changelog
```

## How to Cut a Release

1. **Ensure main is green** — CI and benchmark must pass.

2. **Update version** in `pyproject.toml`:
   ```
   version = "X.Y.Z"
   ```

3. **Commit the version bump**:
   ```bash
   git commit -am "chore: bump version to X.Y.Z"
   git push origin main
   ```

4. **Tag the release**:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. The release pipeline runs automatically. Monitor it on GitHub Actions.

6. **Verify the release**:
   - GitHub release page shows the changelog
   - `ghcr.io/<org>/bimoryn:X.Y.Z` is available
   - `ghcr.io/<org>/bimoryn:latest` points to the new image

## Docker Image

The image is published to GitHub Container Registry (GHCR):

```bash
docker pull ghcr.io/<org>/bimoryn:latest
docker run --rm -v /path/to/model.ifc:/model.ifc ghcr.io/<org>/bimoryn:latest validate /model.ifc
```

Tags published per release:
- `vX.Y.Z` — exact version
- `X.Y` — minor alias (updated on every patch)
- `latest` — always points to the most recent release

## Benchmark Baseline Update

After a release that intentionally improves or changes performance, update the
committed baseline so future regression checks compare against the new reality:

```bash
# Run benchmarks locally
python benchmarks/run_benchmarks.py --sizes small medium --repeats 3

# The output is written to benchmarks/results/latest.json
# Commit it as the new baseline
git add benchmarks/results/latest.json
git commit -m "chore: update benchmark baseline for vX.Y.Z"
git push origin main
```

## Environment Variables Required in GitHub

| Secret                | Purpose                                  |
|-----------------------|------------------------------------------|
| `GITHUB_TOKEN`        | Auto-injected — GHCR push + releases     |

No additional secrets needed for the default setup (GHCR uses the built-in token).

## Staging Deploy (Pilot)

Staging auto-deploy from `main` is pending board approval for infrastructure
access. Once authorized, add a `deploy-staging.yml` workflow that SSH-deploys
the `latest` image to the pilot environment after benchmark passes.

Current pilot access: provide the pilot customer with the `latest` Docker image
tag and the `onboard.sh` script from the repo root.
