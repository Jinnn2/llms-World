# Digital Human World

This repository is a prototype for the Digital Human World concept in
`Main Target.md`. The current implementation validates the V1 world loop,
adds a pluggable model-policy layer, and includes a React-based World View
replay interface.

## Current Scope

The simulation core currently validates a controlled two-day loop:

- environment-triggered decisions
- actions with duration
- short-term working memory
- nightly consolidation into an explicit profile
- optional OpenAI-compatible policy with heuristic fallback
- validation artifacts for event and tick inspection
- a 2D World View app for replaying the V1 behavior

The project does not yet implement online training, parameter memory,
open-ended society, or live frontend control of the Python simulation.

See `docs/development_batches.md` for the current development progress and
batch plan.

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

This writes validation artifacts under `artifacts/validation/<run-id>/` and
refreshes the frontend replay data at `src/web/data/generatedReplay.json`.

Run tests:

```powershell
python -m unittest discover -v
```

Run the B4 multi-person town validation:

```powershell
python validate_b4.py
```

Run the Simulation Lab app:

```powershell
npm install
npm run dev
```

The World View reads `src/web/data/generatedReplay.json`, which is generated
from the simulation rather than hand-authored event frames.

B4 town validation artifacts are written under `artifacts/town_b4/<run-id>/`.
