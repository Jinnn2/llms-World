import generatedReplay from "./generatedReplay.json";
import generatedTownReplay from "./generatedTownReplay.json";

const activeReplay = generatedTownReplay;

export const locations = activeReplay.locations;
export const links = activeReplay.links;
export const people = activeReplay.people ?? [];
export const replayFrames = activeReplay.replayFrames;
export const metrics = activeReplay.metrics;
export const replayMetadata = {
  schemaVersion: activeReplay.schemaVersion,
  source: activeReplay.source,
  generatedAt: activeReplay.generatedAt,
  acceptance: activeReplay.acceptance,
  runMetadata: activeReplay.runMetadata,
};
export const availableReplays = {
  v1: generatedReplay,
  town: generatedTownReplay,
};

export const terrainPatches = [
  { id: "north-woods", type: "trees", x: 17, y: 17, w: 18, h: 18 },
  { id: "south-woods", type: "trees", x: 70, y: 82, w: 18, h: 14 },
  { id: "field-a", type: "field", x: 83, y: 68, w: 20, h: 18 },
  { id: "pond-a", type: "water", x: 24, y: 78, w: 19, h: 12 },
  { id: "stone-yard", type: "stone", x: 54, y: 23, w: 13, h: 10 },
];

export const worldObjects = locations.map((location) => ({
  id: `${location.id}-object`,
  type: objectTypeForLocation(location),
  locationId: location.id,
  x: location.x,
  y: location.y,
  label: location.name,
}));

export const itemObjects = [
  { id: "broom-rack", type: "broomRack", locationId: "warehouse", x: 42, y: 21, label: "Broom rack" },
  { id: "task-marker", type: "taskMarker", locationId: "square", x: 67, y: 43, label: "Clean square task" },
  { id: "rain-sensor", type: "weatherSensor", locationId: "road", x: 48, y: 39, label: "Weather trigger" },
];

function objectTypeForLocation(location) {
  if (location.id === "warehouse") return "warehouse";
  if (location.id === "square") return "fountain";
  if (location.id === "workshop") return "workshop";
  if (location.id === "field") return "fieldRows";
  if (location.id.includes("house") || location.id === "home" || location.id === "cottage" || location.id === "lodge") {
    return "house";
  }
  return "signpost";
}
