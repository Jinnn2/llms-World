import generatedReplay from "./generatedReplay.json";

export const locations = generatedReplay.locations;
export const links = generatedReplay.links;
export const replayFrames = generatedReplay.replayFrames;
export const metrics = generatedReplay.metrics;
export const replayMetadata = {
  schemaVersion: generatedReplay.schemaVersion,
  source: generatedReplay.source,
  generatedAt: generatedReplay.generatedAt,
  acceptance: generatedReplay.acceptance,
  runMetadata: generatedReplay.runMetadata,
};

export const terrainPatches = [
  { id: "north-woods", type: "trees", x: 17, y: 17, w: 18, h: 18 },
  { id: "south-woods", type: "trees", x: 70, y: 82, w: 18, h: 14 },
  { id: "field-a", type: "field", x: 83, y: 68, w: 20, h: 18 },
  { id: "pond-a", type: "water", x: 24, y: 78, w: 19, h: 12 },
  { id: "stone-yard", type: "stone", x: 54, y: 23, w: 13, h: 10 },
];

export const worldObjects = [
  { id: "home-house", type: "house", locationId: "home", x: 15, y: 48, label: "Home" },
  { id: "warehouse-building", type: "warehouse", locationId: "warehouse", x: 36, y: 18, label: "Warehouse" },
  { id: "square-fountain", type: "fountain", locationId: "square", x: 63, y: 48, label: "Square" },
  { id: "workshop-hut", type: "workshop", locationId: "workshop", x: 84, y: 27, label: "Workshop" },
  { id: "field-plots", type: "fieldRows", locationId: "field", x: 82, y: 74, label: "Field" },
  { id: "signpost-road", type: "signpost", locationId: "road", x: 38, y: 48, label: "Road" },
];

export const itemObjects = [
  { id: "broom-rack", type: "broomRack", locationId: "warehouse", x: 42, y: 21, label: "Broom rack" },
  { id: "task-marker", type: "taskMarker", locationId: "square", x: 67, y: 43, label: "Clean square task" },
  { id: "rain-sensor", type: "weatherSensor", locationId: "road", x: 48, y: 39, label: "Weather trigger" },
];
