# Digital Human World Development Batches

This document maps the project concept in `Main Target.md` to the current
repository state and the next implementation batches.

## Current Progress

### Completed

#### B0: Project Definition and V1 Contract

- Source of truth: `Main Target.md`
- V1 design freeze: `docs/v1_design.md`
- Core thesis fixed: individuals propose intentions, environment determines
  reality updates.

#### B1: V1 World Loop

Implemented in `src/digital_human_world`.

- Unified tick clock with 10-second steps.
- World state with locations, weather, tasks, tools, people, and active actions.
- Inspector and observation diff.
- Environment-triggered decisions instead of every-tick replanning.
- Actions with duration, completion, failure, and interruption.
- Working memory for daytime continuity.
- Night consolidation into explicit profile rules and preferences.
- Two-day demo scenario proving behavior changes after consolidation.

Acceptance is covered by `tests/test_simulation.py`.

#### B2: Pluggable Policy Layer

Implemented in `src/digital_human_world/llm_policy.py`.

- Heuristic policy remains the deterministic baseline.
- OpenAI-compatible chat policy can be enabled through environment variables.
- Invalid model output falls back to the heuristic policy.
- Model actions are still validated and resolved by the environment.

Acceptance is covered by `tests/test_llm_policy.py`.

#### B3: World View Replay Prototype

Implemented in `src/web`.

- Vite + React app.
- Pure 2D top-down world map.
- Continuous replay timeline.
- Road-constrained character movement.
- Horizontal panning and wheel zoom.
- Drawer-style auxiliary UI.
- Clickable character status popup.
- Separate frontend data interfaces for locations, roads, terrain, objects,
  items, and replay frames.

Current limitation: the frontend replay is hand-authored data in
`src/web/data/replay.js`; it is not yet generated from the Python simulation
artifacts.

## Mainline Assessment

The backend is at a validated V1/V2 foundation stage. It already proves the
first research loop:

Experience -> short-term continuity -> consolidation -> changed next-day
behavior.

The frontend is a useful presentation layer, but it is currently ahead of the
simulation integration. It should be treated as an observability and demo
surface, not as the source of world truth.

The next development priority is not more visual polish alone. The mainline
needs the simulation core and World View to share one replay/artifact contract,
then expand the world from one autonomous person to a small town.

## Next Batches

### B3.1: Artifact-Driven World View

Goal: make the frontend replay consume real simulation output.

Deliverables:

- Add a replay exporter that converts `engine.event_history` and
  `engine.tick_history` into frontend-ready JSON.
- Replace or supplement `src/web/data/replay.js` with generated replay data.
- Preserve map asset interfaces for locations, roads, terrain, buildings,
  items, and people.
- Add a simple command that regenerates validation artifacts and frontend
  replay data together.

Acceptance:

- `python validate_v1.py` produces both validation artifacts and replay JSON.
- The World View shows the same final outcome as `summary.json`.
- No hand-edited event sequence is required for the V1 demo.

### B4: Small-Town Multi-Person Simulation

Goal: move from one autonomous individual to a 5-person town MVP.

Deliverables:

- Add 5 autonomous people with distinct homes, profiles, and starting roles.
- Add basic needs: hunger, fatigue, shelter, and simple work obligations.
- Add location occupancy and proximity-based observations.
- Add per-person task assignment and independent action scheduling.
- Keep environment validation authoritative for all actions.

Acceptance:

- A full simulated day runs deterministically in heuristic mode.
- Each person maintains separate working memory and profile.
- No person can teleport or act at an invalid location.
- Event logs can be filtered by person.

### B5: Habit Formation

Goal: make repeated experience produce stable behavior beyond one hard-coded
weather/tool rule.

Deliverables:

- Generalize consolidation from fixed cases to typed experience records.
- Add habit candidates with frequency, reward, and context.
- Promote stable habits into profile after repeated evidence.
- Add regression tests for at least two habits.

Acceptance:

- A repeated routine changes future action ordering.
- A bad repeated outcome suppresses a future action.
- Habit changes are visible in validation summary and World View.

### B6: Skill Learning

Goal: give `LEARN` and skill profiles operational meaning.

Deliverables:

- Define skill schema with level, confidence, source, and decay or stability.
- Implement observation-based learning and instruction-based learning.
- Let skills affect action success, duration, or available action choices.
- Add at least one task that cannot be completed efficiently without learning.

Acceptance:

- Skill level changes after repeated observation or instruction.
- Skill state changes task outcome or duration.
- Tests prove the environment, not the policy, determines success.

### B7: Social Layer

Goal: start forming social digital humans rather than isolated agents.

Deliverables:

- Implement `SPEAK` events with listeners, messages, and local propagation.
- Add relationship state between people.
- Let instruction, warning, and cooperation influence memory.
- Add simple cooperative tasks.

Acceptance:

- One person can warn or instruct another through an environment event.
- The listener's working memory changes immediately.
- Consolidation can preserve a social preference or learned rule.

### B8: Parametric Memory Research Track

Goal: prepare for the project-book target of long-term memory in model
parameters.

Deliverables:

- Treat explicit profile consolidation as the training-data bridge.
- Export experience/profile pairs suitable for later fine-tuning or adapter
  training.
- Define evaluation prompts and behavior checks for before/after consolidation.
- Keep runtime simulation independent from any specific training backend.

Acceptance:

- The system can produce clean training/evaluation records from simulation.
- The same scenario can compare heuristic, prompted-model, and trained-model
  policies through one validation harness.

## Immediate Recommended Batch

Start with B3.1.

Reason: the World View is now the user's primary demonstration surface, but it
is not connected to the backend source of truth. Connecting it to generated
simulation artifacts will prevent UI drift and create a stable base before
expanding to multiple people in B4.
