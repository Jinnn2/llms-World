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

#### B3.1: Artifact-Driven World View

Implemented through `src/digital_human_world/replay_export.py` and
`validate_v1.py`.

- The Python validation run now exports `world_view_replay.json` into the
  validation artifact directory.
- The same run refreshes `src/web/data/generatedReplay.json` for the Vite app.
- The frontend map still owns visual terrain/object decoration, but locations,
  road links, replay frames, acceptance status, and metrics come from the
  simulation export.
- The public frontend replay metadata omits local endpoint configuration.

Acceptance is covered by `tests/test_replay_export.py`.

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

Status: complete for the V1 demo.

Delivered:

- Added a replay exporter that converts `engine.event_history` and
  `engine.tick_history` into frontend-ready JSON.
- Replaced hand-authored replay frames with generated replay data.
- Preserved map asset interfaces for locations, roads, terrain, buildings,
  items, and people.
- Added a simple command that regenerates validation artifacts and frontend
  replay data together.

Acceptance:

- `python validate_v1.py` produces both validation artifacts and replay JSON.
- The World View shows the same final outcome as `summary.json`.
- No hand-edited event sequence is required for the V1 demo.

### B4: Small-Town Multi-Person Simulation

Goal: move from one autonomous individual to a 5-person town MVP.

Status: complete for the first deterministic town-day loop.

Delivered:

- Added `build_town_engine()` with 5 autonomous people plus a non-autonomous
  foreman.
- Added distinct homes, profile traits, basic hunger/fatigue state, and simple
  work obligations.
- Added town tasks for cleaning, farming, repair, cooking, and gathering.
- Generalized the heuristic policy for assigned tasks beyond `clean_square`.
- Kept the V1 `clean_square` learning path intact.
- Added graph-route movement for `GO`, so people advance through road nodes
  over time instead of teleporting at action completion.
- Added `events_for_person()` and `build_town_summary()` for per-person logs
  and B4 acceptance.
- Added `validate_b4.py` to write B4 artifacts under
  `artifacts/town_b4/<run-id>/`.

Acceptance:

- A full simulated day runs deterministically in heuristic mode.
- Each person maintains separate working memory and profile.
- No person can teleport or act at an invalid location.
- Event logs can be filtered by person.

Acceptance is covered by `tests/test_town_simulation.py`.

UI track:

- Status: complete for the first B4 town replay.
- B4 World View renders the 5-person town replay exported by
  `validate_b4.py`.
- It shows all autonomous people on the map at once, keeps click-to-inspect
  state bound to each person, and use the backend road graph for movement.
- The UI source of truth is `src/web/data/generatedTownReplay.json`, generated
  from B4 artifacts rather than hand-authored frames.

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

UI track:

- Add habit badges and before/after routine comparison in the person drawer.
- Timeline cards should mark habit-forming evidence and promoted habits.
- World View should expose per-person habit state without hiding the map.

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

UI track:

- Add skill bars or compact level indicators to each person profile.
- Show task duration or success changes caused by skill state.
- Visualize `LEARN` events distinctly from ordinary `DO` work.

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

UI track:

- Show local speech/listener propagation on the map.
- Add relationship and recent-contact panels per person.
- Timeline should support filtering by speaker, listener, and location.

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

UI track:

- Add run comparison for heuristic, prompted-model, and trained-model policies.
- Expose evaluation prompts, expected behaviors, and observed divergences.
- Keep training/export artifacts inspectable from the UI without making the UI
  responsible for model training.

## Immediate Recommended Batch

Start B5.

Reason: the project now has the first deterministic 5-person town loop. The
next mainline step is making repeated experience produce general habit changes,
instead of relying on fixed V1 consolidation rules.
