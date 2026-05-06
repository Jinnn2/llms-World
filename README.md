# Digital Human World

This repository is a V1 prototype for the Digital Human World concept in
`Main Target.md`.

## Current Scope

V1 validates a controlled two-day loop:

- environment-triggered decisions
- actions with duration
- short-term working memory
- nightly consolidation into an explicit profile
- optional OpenAI-compatible policy with heuristic fallback

V1 does not yet implement online training, parameter memory, open-ended society,
or a UI.

## Commands

Run the deterministic demo:

```powershell
$env:DHW_POLICY_MODE = "heuristic"
python run_v1.py
```

Run the validation artifact writer:

```powershell
$env:DHW_POLICY_MODE = "heuristic"
python validate_v1.py
```

Run tests:

```powershell
python -m unittest discover -v
```

Validation artifacts are written under `artifacts/validation/<run-id>/`.
