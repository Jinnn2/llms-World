import {
  Brain,
  CalendarDays,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CloudRain,
  Database,
  ListTree,
  Map as MapIcon,
  Package,
  Pause,
  Play,
  RotateCcw,
  Settings2,
  SkipBack,
  SkipForward,
  Sun,
  UserRound,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  itemObjects,
  links,
  locations,
  replayFrames,
  terrainPatches,
  worldObjects,
} from "./data/replay.js";

const WORLD_SIZE = { width: 2800, height: 1900 };

const eventLabels = {
  task: "Task",
  action: "Action",
  failure: "Failure",
  tool: "Tool",
  interrupt: "Interrupt",
  weather: "Weather",
  complete: "Complete",
  memory: "Memory",
  decision: "Decision",
};

const drawerDefaults = {
  controls: false,
  person: false,
  timeline: false,
};

export function App() {
  const [index, setIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(900);
  const [dayFilter, setDayFilter] = useState("all");
  const [panX, setPanX] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [drawers, setDrawers] = useState(drawerDefaults);
  const [characterOpen, setCharacterOpen] = useState(true);

  const frame = replayFrames[index];
  const nextFrame = replayFrames[(index + 1) % replayFrames.length];
  const characterPosition = interpolateLocation(frame, nextFrame, progress);
  const displayTime = formatContinuousTime(frame, nextFrame, progress);
  const displayLocation = formatDisplayLocation(frame, nextFrame, progress);
  const isMoving = playing && locationsDiffer(frame, nextFrame);
  const filteredFrames = useMemo(() => {
    const frames = replayFrames.map((item, sourceIndex) => ({ ...item, sourceIndex }));
    if (dayFilter === "all") return frames;
    return frames.filter((item) => String(item.day) === dayFilter);
  }, [dayFilter]);

  useEffect(() => {
    if (!playing) return undefined;

    let previousTime = performance.now();
    let animationFrame = 0;
    const tick = (now) => {
      const delta = now - previousTime;
      previousTime = now;
      setProgress((current) => {
        const nextProgress = current + delta / frameDuration(replayFrames[index], speed);
        if (nextProgress >= 1) {
          setIndex((currentIndex) => (currentIndex + 1) % replayFrames.length);
          return nextProgress % 1;
        }
        return nextProgress;
      });
      animationFrame = window.requestAnimationFrame(tick);
    };

    animationFrame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(animationFrame);
  }, [index, playing, speed]);

  function moveView(delta) {
    setPanX((current) => clamp(current + delta, -900, 900));
  }

  function zoomView(delta) {
    setZoom((current) => clamp(Number((current + delta).toFixed(2)), 0.58, 1.55));
  }

  function handleWheel(event) {
    event.preventDefault();
    const delta = event.deltaY > 0 ? -0.08 : 0.08;
    zoomView(delta);
  }

  function setDrawer(name, value) {
    setDrawers((current) => ({ ...current, [name]: value }));
  }

  function selectFrame(sourceIndex) {
    setIndex(sourceIndex);
    setProgress(0);
    setPlaying(false);
    setCharacterOpen(true);
  }

  function step(delta) {
    setPlaying(false);
    setProgress(0);
    setIndex((current) => (current + replayFrames.length + delta) % replayFrames.length);
    setCharacterOpen(true);
  }

  function resetReplay() {
    setPlaying(false);
    setProgress(0);
    setIndex(0);
    setCharacterOpen(true);
  }

  return (
    <main className={`gameShell weather-${frame.weather}`}>
      <WorldHud
        displayTime={displayTime}
        frame={frame}
        index={index}
        playing={playing}
        onReset={resetReplay}
        onStep={step}
        onTogglePlay={() => setPlaying((value) => !value)}
      />

      <DrawerRail drawers={drawers} onToggle={(name) => setDrawer(name, !drawers[name])} />

      <section className="worldView" aria-label="2D world view">
        <div className="mapViewport" onWheel={handleWheel}>
          <div
            className="mapCanvas"
            style={{
              width: WORLD_SIZE.width,
              height: WORLD_SIZE.height,
              transform: cameraTransform(characterPosition, panX, zoom),
            }}
          >
            <FarmlandTiles />
            <RoadNetwork />
            {terrainPatches.map((patch) => (
              <TerrainPatch key={patch.id} patch={patch} />
            ))}
            {worldObjects.map((object) => (
              <WorldObject key={object.id} object={object} />
            ))}
            {itemObjects.map((object) => (
              <WorldItem key={object.id} object={object} />
            ))}
            <Character
              displayLocation={displayLocation}
              frame={frame}
              moving={isMoving}
              open={characterOpen}
              position={characterPosition}
              onToggle={() => setCharacterOpen((value) => !value)}
            />
          </div>
        </div>

        <div className="viewControls" aria-label="Map view controls">
          <button aria-label="Move view left" onClick={() => moveView(180)} type="button">
            <ChevronLeft size={18} />
          </button>
          <button aria-label="Zoom out" onClick={() => zoomView(-0.1)} type="button">
            <ZoomOut size={18} />
          </button>
          <span>{Math.round(zoom * 100)}%</span>
          <button aria-label="Zoom in" onClick={() => zoomView(0.1)} type="button">
            <ZoomIn size={18} />
          </button>
          <button aria-label="Move view right" onClick={() => moveView(-180)} type="button">
            <ChevronRight size={18} />
          </button>
        </div>

        <div className="eventToast" aria-live="polite">
          <span className={`eventType event-${frame.eventType}`}>{eventLabels[frame.eventType]}</span>
          <p>{frame.event}</p>
        </div>
      </section>

      <Drawer
        side="left"
        title="Simulation Controls"
        icon={<Settings2 size={18} />}
        open={drawers.controls}
        onClose={() => setDrawer("controls", false)}
      >
        <ControlPanel
          dayFilter={dayFilter}
          frame={frame}
          playing={playing}
          speed={speed}
          onDayFilter={setDayFilter}
          onReset={resetReplay}
          onSpeed={setSpeed}
          onStep={step}
          onTogglePlay={() => setPlaying((value) => !value)}
        />
      </Drawer>

      <Drawer
        side="right"
        title="Lin State"
        icon={<UserRound size={18} />}
        open={drawers.person}
        onClose={() => setDrawer("person", false)}
      >
        <PersonPanel frame={frame} displayLocation={displayLocation} />
      </Drawer>

      <Drawer
        side="bottom"
        title="Event Timeline"
        icon={<ListTree size={18} />}
        open={drawers.timeline}
        onClose={() => setDrawer("timeline", false)}
      >
        <Timeline frames={filteredFrames} activeIndex={index} onSelect={selectFrame} />
      </Drawer>
    </main>
  );
}

function WorldHud({ displayTime, frame, index, playing, onTogglePlay, onStep, onReset }) {
  return (
    <header className="worldHud">
      <div className="brandBlock">
        <span>Digital Human World</span>
        <strong>2D World</strong>
      </div>
      <div className="hudStats" aria-label="Current world state">
        <HudItem icon={<CalendarDays size={16} />} label="Clock" value={displayTime} />
        <HudItem icon={weatherIcon(frame.weather)} label="Weather" value={frame.weather} />
        <HudItem icon={<Database size={16} />} label="Frame" value={`${index + 1}/${replayFrames.length}`} />
      </div>
      <div className="hudTransport">
        <button aria-label="Previous frame" onClick={() => onStep(-1)} type="button">
          <SkipBack size={18} />
        </button>
        <button className="hudPrimary" aria-label={playing ? "Pause replay" : "Play replay"} onClick={onTogglePlay} type="button">
          {playing ? <Pause size={19} /> : <Play size={19} />}
        </button>
        <button aria-label="Next frame" onClick={() => onStep(1)} type="button">
          <SkipForward size={18} />
        </button>
        <button aria-label="Reset replay" onClick={onReset} type="button">
          <RotateCcw size={18} />
        </button>
      </div>
    </header>
  );
}

function DrawerRail({ drawers, onToggle }) {
  const items = [
    ["controls", <Settings2 size={19} />, "Controls"],
    ["person", <UserRound size={19} />, "Person"],
    ["timeline", <ListTree size={19} />, "Timeline"],
  ];
  return (
    <nav className="drawerRail" aria-label="World drawers">
      {items.map(([name, icon, label]) => (
        <button
          className={drawers[name] ? "active" : ""}
          key={name}
          onClick={() => onToggle(name)}
          type="button"
          aria-label={`Toggle ${label} drawer`}
        >
          {icon}
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}

function Drawer({ children, icon, onClose, open, side, title }) {
  return (
    <aside className={`drawer drawer-${side} ${open ? "open" : ""}`} aria-hidden={!open}>
      <div className="drawerHeader">
        <span>
          {icon}
          {title}
        </span>
        <button aria-label={`Close ${title}`} onClick={onClose} type="button">
          {side === "bottom" ? <ChevronDown size={18} /> : <X size={18} />}
        </button>
      </div>
      <div className="drawerBody">{children}</div>
    </aside>
  );
}

function ControlPanel({
  dayFilter,
  frame,
  playing,
  speed,
  onDayFilter,
  onReset,
  onSpeed,
  onStep,
  onTogglePlay,
}) {
  return (
    <div className="drawerStack">
      <div className="compactTransport">
        <button aria-label="Previous frame" onClick={() => onStep(-1)} type="button">
          <SkipBack size={18} />
        </button>
        <button className="controlPrimary" aria-label={playing ? "Pause replay" : "Play replay"} onClick={onTogglePlay} type="button">
          {playing ? <Pause size={20} /> : <Play size={20} />}
        </button>
        <button aria-label="Next frame" onClick={() => onStep(1)} type="button">
          <SkipForward size={18} />
        </button>
        <button aria-label="Reset replay" onClick={onReset} type="button">
          <RotateCcw size={18} />
        </button>
      </div>

      <Segmented
        label="Replay speed"
        options={[
          [1200, "1x"],
          [900, "1.5x"],
          [520, "2x"],
        ]}
        value={speed}
        onChange={onSpeed}
      />
      <Segmented
        label="Day filter"
        options={[
          ["all", "All"],
          ["1", "Day 1"],
          ["2", "Day 2"],
        ]}
        value={dayFilter}
        onChange={onDayFilter}
      />

      <div className="drawerMetric">
        <span>Current Event</span>
        <strong>{frame.event}</strong>
      </div>
      <div className="drawerMetric">
        <span>Map Mode</span>
        <strong>Pure 2D top-down map. Wheel zooms, side buttons pan, and Lin moves only along roads.</strong>
      </div>
    </div>
  );
}

function PersonPanel({ displayLocation, frame }) {
  return (
    <div className="drawerStack">
      <div className="personHero">
        <div className="portraitMini">
          <Brain size={28} />
        </div>
        <div>
          <span>Proto-human</span>
          <strong>Lin</strong>
          <p>{frame.intent}</p>
        </div>
      </div>
      <StateGroup title="Bound To Character">
        <KeyValue label="location" value={displayLocation} />
        <KeyValue label="action" value={frame.action} />
        <KeyValue label="active_goal" value={frame.activeGoal ?? "none"} />
      </StateGroup>
      <StateGroup title="Working Memory">
        <NoteList notes={frame.workingNotes} />
      </StateGroup>
      <StateGroup title="Profile">
        <TokenList empty="No learned rules yet" items={frame.profileRules} tone="amber" />
        <TokenList empty="No stable preferences yet" items={frame.profilePreferences} tone="teal" />
      </StateGroup>
      <StateGroup title="Inventory">
        <TokenList empty="Empty" items={frame.inventory} tone="green" />
      </StateGroup>
    </div>
  );
}

function Timeline({ frames, activeIndex, onSelect }) {
  return (
    <div className="timelineStrip">
      {frames.map((item) => (
        <button
          className={`timelineCard ${item.sourceIndex === activeIndex ? "active" : ""}`}
          key={`${item.time}-${item.event}`}
          onClick={() => onSelect(item.sourceIndex)}
          type="button"
        >
          <span className={`timelinePin event-${item.eventType}`} />
          <strong>{item.time}</strong>
          <small>{item.event}</small>
        </button>
      ))}
    </div>
  );
}

function FarmlandTiles() {
  const tiles = [];
  for (let row = 0; row < 10; row += 1) {
    for (let col = 0; col < 14; col += 1) {
      tiles.push({ id: `${row}-${col}`, row, col });
    }
  }
  return (
    <div className="farmlandTiles" aria-hidden="true">
      {tiles.map((tile) => (
        <span
          className={`farmTile farmTile-${(tile.row + tile.col) % 4}`}
          key={tile.id}
          style={{
            left: tile.col * 210,
            top: tile.row * 190,
          }}
        />
      ))}
    </div>
  );
}

function TerrainPatch({ patch }) {
  return (
    <div
      className={`terrainPatch terrain-${patch.type}`}
      style={{
        left: px(patch.x, "x"),
        top: px(patch.y, "y"),
        width: px(patch.w, "x"),
        height: px(patch.h, "y"),
      }}
    />
  );
}

function RoadNetwork() {
  return (
    <svg className="roadNetwork" viewBox={`0 0 ${WORLD_SIZE.width} ${WORLD_SIZE.height}`} aria-hidden="true">
      <path d={roadPath(["home", "road", "square"])} />
      <path d={roadPath(["road", "warehouse"])} />
      <path d={roadPath(["road", "workshop"])} />
      <path d={roadPath(["road", "field"])} />
      <path className="roadCenter" d={roadPath(["home", "road", "square"])} />
      <path className="roadCenter" d={roadPath(["road", "warehouse"])} />
      <path className="roadCenter" d={roadPath(["road", "workshop"])} />
      <path className="roadCenter" d={roadPath(["road", "field"])} />
    </svg>
  );
}

function WorldObject({ object }) {
  return (
    <button
      className={`worldObject object-${object.type}`}
      style={{ left: px(object.x, "x"), top: px(object.y, "y") }}
      type="button"
      aria-label={`${object.label} environment object`}
    >
      <ObjectSprite type={object.type} />
      <span className="objectLabel">{object.label}</span>
    </button>
  );
}

function WorldItem({ object }) {
  return (
    <button
      className={`worldItem item-${object.type}`}
      style={{ left: px(object.x, "x"), top: px(object.y, "y") }}
      type="button"
      aria-label={`${object.label} item`}
    >
      <span>{itemIcon(object.type)}</span>
      <small>{object.label}</small>
    </button>
  );
}

function ObjectSprite({ type }) {
  if (type === "house") {
    return (
      <span className="spriteHouse">
        <span className="roof" />
        <span className="door" />
      </span>
    );
  }
  if (type === "warehouse") {
    return (
      <span className="spriteWarehouse">
        <span className="door" />
      </span>
    );
  }
  if (type === "fountain") {
    return <span className="spriteFountain" />;
  }
  if (type === "workshop") {
    return (
      <span className="spriteWorkshop">
        <span className="chimney" />
      </span>
    );
  }
  if (type === "fieldRows") {
    return <span className="spriteFieldRows" />;
  }
  return <span className="spriteSignpost" />;
}

function Character({ displayLocation, frame, moving, onToggle, open, position }) {
  return (
    <div className="characterMount" style={{ left: px(position.x, "x"), top: px(position.y, "y") }}>
      <button
        className={`characterButton ${moving ? "moving" : ""}`}
        aria-label={`Lin at ${displayLocation}. Current action ${frame.action}`}
        onClick={onToggle}
        type="button"
      >
        <span className="characterShadow" />
        <span className="characterSprite">
          <span className="characterHead" />
          <span className="characterBody" />
          <span className="characterArm armLeft" />
          <span className="characterArm armRight" />
          <span className="characterLeg legLeft" />
          <span className="characterLeg legRight" />
        </span>
        <span className="characterName">Lin</span>
      </button>

      {open ? (
        <div className="characterPopup" role="dialog" aria-label="Lin character details">
          <div className="popupTitle">
            <UserRound size={16} />
            <strong>Lin</strong>
          </div>
          <KeyValue label="Location" value={displayLocation} />
          <KeyValue label="Action" value={frame.action} />
          <KeyValue label="Intent" value={frame.intent} />
        </div>
      ) : null}
    </div>
  );
}

function HudItem({ icon, label, value }) {
  return (
    <div className="hudItem">
      <span>{icon}</span>
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

function Segmented({ label, onChange, options, value }) {
  return (
    <div className="segmentedBlock">
      <span>{label}</span>
      <div>
        {options.map(([optionValue, optionLabel]) => (
          <button
            className={value === optionValue ? "selected" : ""}
            key={String(optionValue)}
            onClick={() => onChange(optionValue)}
            type="button"
          >
            {optionLabel}
          </button>
        ))}
      </div>
    </div>
  );
}

function StateGroup({ title, children }) {
  return (
    <section className="stateGroup">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function KeyValue({ label, value }) {
  return (
    <div className="keyValue">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function NoteList({ notes }) {
  return (
    <ul className="noteList">
      {notes.map((note) => (
        <li key={note}>{note}</li>
      ))}
    </ul>
  );
}

function TokenList({ empty, items, tone }) {
  if (!items.length) {
    return <p className="emptyText">{empty}</p>;
  }
  return (
    <div className="tokenList">
      {items.map((item) => (
        <span className={`token token-${tone}`} key={item}>
          {item}
        </span>
      ))}
    </div>
  );
}

function weatherIcon(weather) {
  return weather === "rain" ? <CloudRain size={16} /> : <Sun size={16} />;
}

function itemIcon(type) {
  if (type === "broomRack") return <Package size={15} />;
  if (type === "taskMarker") return <MapIcon size={15} />;
  return <CloudRain size={15} />;
}

function locationById(id) {
  return locations.find((location) => location.id === id) ?? locations[0];
}

function locationPoint(id) {
  const location = locationById(id);
  return { x: px(location.x, "x"), y: px(location.y, "y") };
}

function px(value, axis) {
  return Math.round((value / 100) * (axis === "x" ? WORLD_SIZE.width : WORLD_SIZE.height));
}

function roadPath(ids) {
  const points = ids.map(locationPoint);
  if (points.length === 2) {
    const [start, end] = points;
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2;
    return `M ${start.x} ${start.y} Q ${midX} ${midY} ${end.x} ${end.y}`;
  }
  const [first, ...rest] = points;
  return `M ${first.x} ${first.y} ` + rest.map((point) => `L ${point.x} ${point.y}`).join(" ");
}

function cameraTransform(position, panX, zoom) {
  const x = Math.round(px(position.x, "x") * zoom);
  const y = Math.round(px(position.y, "y") * zoom);
  return `translate(calc(50vw - ${x}px + ${panX}px), calc(50dvh - ${y}px)) scale(${zoom})`;
}

function locationsDiffer(current, next) {
  return current.locationId !== next.locationId;
}

function interpolateLocation(current, next, progress) {
  if (!locationsDiffer(current, next)) {
    return locationById(current.locationId);
  }

  const route = routeBetween(current.locationId, next.locationId).map(locationById);
  const points = route.map((location) => ({
    x: px(location.x, "x"),
    y: px(location.y, "y"),
  }));
  const point = pointOnPolyline(points, smoothStep(progress));
  return {
    x: (point.x / WORLD_SIZE.width) * 100,
    y: (point.y / WORLD_SIZE.height) * 100,
  };
}

function smoothStep(value) {
  const t = Math.min(1, Math.max(0, value));
  return t * t * (3 - 2 * t);
}

function formatDisplayLocation(current, next, progress) {
  if (!locationsDiffer(current, next) || progress < 0.08 || progress > 0.92) {
    const start = locationById(current.locationId);
    const end = locationById(next.locationId);
    return progress > 0.92 ? end.name : start.name;
  }
  const route = routeBetween(current.locationId, next.locationId);
  const routeIndex = Math.min(
    route.length - 2,
    Math.max(0, Math.floor(progress * (route.length - 1))),
  );
  return `${locationById(route[routeIndex]).name} -> ${locationById(route[routeIndex + 1]).name}`;
}

function formatContinuousTime(current, next, progress) {
  const start = parseClockSeconds(current.time);
  const end = parseClockSeconds(next.time);
  const normalizedEnd = end <= start ? end + 24 * 60 * 60 : end;
  return formatClockSeconds(start + (normalizedEnd - start) * progress);
}

function parseClockSeconds(label) {
  const match = label.match(/(Day\s+(\d+)|Night)\s+(\d{2}):(\d{2}):(\d{2})/);
  if (!match) return 0;
  const day = match[1] === "Night" ? 1 : Number(match[2]);
  const hours = Number(match[3]);
  const minutes = Number(match[4]);
  const seconds = Number(match[5]);
  return (day - 1) * 24 * 60 * 60 + hours * 60 * 60 + minutes * 60 + seconds;
}

function formatClockSeconds(value) {
  const rounded = Math.floor(value);
  const day = Math.floor(rounded / (24 * 60 * 60)) + 1;
  const secondsInDay = ((rounded % (24 * 60 * 60)) + 24 * 60 * 60) % (24 * 60 * 60);
  const hours = Math.floor(secondsInDay / 3600);
  const minutes = Math.floor((secondsInDay % 3600) / 60);
  const seconds = secondsInDay % 60;
  const prefix = day === 1 && hours >= 21 ? "Night" : `Day ${day}`;
  return `${prefix} ${pad2(hours)}:${pad2(minutes)}:${pad2(seconds)}`;
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

function frameDuration(frame, speed) {
  const base = frame.durationMs ?? 900;
  return base * (speed / 900);
}

function routeBetween(startId, endId) {
  if (startId === endId) return [startId];

  const neighbors = new Map();
  for (const [from, to] of links) {
    if (!neighbors.has(from)) neighbors.set(from, []);
    if (!neighbors.has(to)) neighbors.set(to, []);
    neighbors.get(from).push(to);
    neighbors.get(to).push(from);
  }

  const queue = [[startId]];
  const visited = new Set([startId]);
  while (queue.length) {
    const path = queue.shift();
    const current = path[path.length - 1];
    for (const next of neighbors.get(current) ?? []) {
      if (visited.has(next)) continue;
      const nextPath = [...path, next];
      if (next === endId) return nextPath;
      visited.add(next);
      queue.push(nextPath);
    }
  }

  return [startId, endId];
}

function pointOnPolyline(points, progress) {
  if (points.length <= 1) return points[0] ?? { x: 0, y: 0 };

  const segments = [];
  let totalLength = 0;
  for (let index = 0; index < points.length - 1; index += 1) {
    const start = points[index];
    const end = points[index + 1];
    const length = Math.hypot(end.x - start.x, end.y - start.y);
    totalLength += length;
    segments.push({ start, end, length });
  }

  let distance = totalLength * clamp(progress, 0, 1);
  for (const segment of segments) {
    if (distance > segment.length) {
      distance -= segment.length;
      continue;
    }
    const t = segment.length === 0 ? 0 : distance / segment.length;
    return {
      x: segment.start.x + (segment.end.x - segment.start.x) * t,
      y: segment.start.y + (segment.end.y - segment.start.y) * t,
    };
  }
  return points[points.length - 1];
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
