from __future__ import annotations

from datetime import datetime

from .engine import ScheduledWorldEvent, SimulationEngine
from .models import (
    Event,
    EventPriority,
    EventType,
    Location,
    LocationKind,
    Person,
    Profile,
    Weather,
    WorldState,
    WorldTask,
)
from .policy import DecisionPolicy, HeuristicProtoHumanPolicy


def build_demo_engine(
    policy: DecisionPolicy | None = None,
) -> tuple[SimulationEngine, datetime]:
    start_time = datetime(2026, 4, 8, 7, 59, 50)
    world = WorldState(
        current_time=start_time,
        weather=Weather.CLEAR,
        locations={
            "home": Location(
                id="home",
                name="Home",
                kind=LocationKind.INDOOR,
                neighbors=["road"],
            ),
            "road": Location(
                id="road",
                name="Road",
                kind=LocationKind.OUTDOOR,
                neighbors=["home", "warehouse", "square", "workshop", "field"],
            ),
            "warehouse": Location(
                id="warehouse",
                name="Warehouse",
                kind=LocationKind.INDOOR,
                neighbors=["road"],
                tools=["broom", "broom"],
            ),
            "square": Location(
                id="square",
                name="Square",
                kind=LocationKind.OUTDOOR,
                neighbors=["road"],
            ),
            "workshop": Location(
                id="workshop",
                name="Workshop",
                kind=LocationKind.INDOOR,
                neighbors=["road"],
            ),
            "field": Location(
                id="field",
                name="Field",
                kind=LocationKind.OUTDOOR,
                neighbors=["road"],
            ),
        },
        people={
            "lin": Person(
                id="lin",
                name="Lin",
                location_id="home",
                home_id="home",
                profile=Profile(
                    identity="Lin",
                    stable_traits=["diligent", "cautious"],
                    skills={
                        "navigation": {"level": 1, "status": "known", "notes": "Can move between known places."},
                        "tool_use": {"level": 1, "status": "known", "notes": "Can pick up and carry simple tools."},
                        "cleaning": {"level": 0, "status": "novice", "notes": "Needs task-specific guidance."},
                        "weather_response": {"level": 0, "status": "novice", "notes": "Rain avoidance is not yet consolidated."},
                    },
                ),
            ),
            "foreman": Person(
                id="foreman",
                name="Foreman",
                location_id="workshop",
                home_id="workshop",
                autonomous=False,
                profile=Profile(identity="Foreman"),
            ),
            "villager": Person(
                id="villager",
                name="Villager",
                location_id="field",
                home_id="field",
                autonomous=False,
                profile=Profile(identity="Villager"),
            ),
        },
        tasks={
            "clean_square": WorldTask(
                id="clean_square",
                name="Clean the town square",
                kind="cleaning",
                location_id="square",
                required_tool="broom",
            )
        },
    )

    schedule = [
        ScheduledWorldEvent(
            at=datetime(2026, 4, 8, 8, 0, 0),
            name="assign_day1_cleaning",
            callback=_assign_clean_square,
        ),
        ScheduledWorldEvent(
            at=datetime(2026, 4, 8, 8, 2, 0),
            name="rain_day1",
            callback=_make_rain_start,
        ),
        ScheduledWorldEvent(
            at=datetime(2026, 4, 8, 8, 5, 0),
            name="clear_day1",
            callback=_make_weather_clear,
        ),
        ScheduledWorldEvent(
            at=datetime(2026, 4, 9, 7, 59, 50),
            name="rain_day2",
            callback=_make_rain_start,
        ),
        ScheduledWorldEvent(
            at=datetime(2026, 4, 9, 8, 0, 0),
            name="assign_day2_cleaning",
            callback=_assign_clean_square,
        ),
        ScheduledWorldEvent(
            at=datetime(2026, 4, 9, 8, 3, 0),
            name="clear_day2",
            callback=_make_weather_clear,
        ),
    ]

    engine = SimulationEngine(
        world=world,
        policy=policy or HeuristicProtoHumanPolicy(),
        scheduled_events=schedule,
    )
    end_time = datetime(2026, 4, 9, 8, 10, 0)
    return engine, end_time


def build_town_engine(
    policy: DecisionPolicy | None = None,
) -> tuple[SimulationEngine, datetime]:
    start_time = datetime(2026, 4, 10, 7, 59, 50)
    world = WorldState(
        current_time=start_time,
        weather=Weather.CLEAR,
        locations={
            "home": Location("home", "Lin Home", LocationKind.INDOOR, ["road"]),
            "farm_house": Location("farm_house", "Farm House", LocationKind.INDOOR, ["road"]),
            "craft_house": Location("craft_house", "Craft House", LocationKind.INDOOR, ["road"]),
            "cottage": Location("cottage", "Cottage", LocationKind.INDOOR, ["road"]),
            "lodge": Location("lodge", "Lodge", LocationKind.INDOOR, ["road"]),
            "road": Location(
                "road",
                "Main Road",
                LocationKind.OUTDOOR,
                ["home", "farm_house", "craft_house", "cottage", "lodge", "warehouse", "square", "workshop", "field", "grove"],
            ),
            "warehouse": Location(
                "warehouse",
                "Warehouse",
                LocationKind.INDOOR,
                ["road"],
                tools=["broom", "hoe", "hammer"],
            ),
            "square": Location("square", "Square", LocationKind.OUTDOOR, ["road"]),
            "workshop": Location("workshop", "Workshop", LocationKind.INDOOR, ["road"]),
            "field": Location("field", "Field", LocationKind.OUTDOOR, ["road"]),
            "grove": Location("grove", "Herb Grove", LocationKind.OUTDOOR, ["road"]),
        },
        people={
            "lin": _town_person("lin", "Lin", "home", ["diligent", "cautious"]),
            "mara": _town_person("mara", "Mara", "farm_house", ["patient", "practical"]),
            "tao": _town_person("tao", "Tao", "craft_house", ["focused", "hands-on"]),
            "nia": _town_person("nia", "Nia", "cottage", ["careful", "social"]),
            "omar": _town_person("omar", "Omar", "lodge", ["observant", "curious"]),
            "foreman": Person(
                id="foreman",
                name="Foreman",
                location_id="workshop",
                home_id="workshop",
                autonomous=False,
                profile=Profile(identity="Foreman"),
            ),
        },
        tasks={
            "clean_square": WorldTask(
                "clean_square",
                "Clean the town square",
                "cleaning",
                "square",
                required_tool="broom",
            ),
            "tend_field": WorldTask(
                "tend_field",
                "Tend the north field",
                "farming",
                "field",
                required_tool="hoe",
            ),
            "repair_cart": WorldTask(
                "repair_cart",
                "Repair the supply cart",
                "repair",
                "workshop",
                required_tool="hammer",
            ),
            "cook_meal": WorldTask(
                "cook_meal",
                "Cook a shared meal",
                "cooking",
                "cottage",
            ),
            "gather_herbs": WorldTask(
                "gather_herbs",
                "Gather herbs near the grove",
                "gathering",
                "grove",
            ),
        },
    )

    schedule = [
        ScheduledWorldEvent(
            at=datetime(2026, 4, 10, 8, 0, 0),
            name="assign_town_morning_work",
            callback=_assign_town_morning_work,
        ),
    ]

    engine = SimulationEngine(
        world=world,
        policy=policy or HeuristicProtoHumanPolicy(),
        scheduled_events=schedule,
    )
    end_time = datetime(2026, 4, 10, 10, 0, 0)
    return engine, end_time


def _assign_clean_square(world: WorldState) -> list[Event]:
    task = world.tasks["clean_square"]
    task.completed = False
    task.active = True
    task.progress = 0
    return [
        Event(
            event_type=EventType.TASK_ASSIGNED,
            timestamp=world.current_time,
            message="Foreman assigned Lin to clean the square",
            actor_id="foreman",
            target_ids=["lin"],
            payload={"task_id": "clean_square"},
        )
    ]


def _town_person(person_id: str, name: str, home_id: str, traits: list[str]) -> Person:
    return Person(
        id=person_id,
        name=name,
        location_id=home_id,
        home_id=home_id,
        hunger=18,
        fatigue=12,
        profile=Profile(
            identity=name,
            stable_traits=traits,
            skills={
                "navigation": 1,
                "tool_use": 1,
            },
        ),
    )


def _assign_town_morning_work(world: WorldState) -> list[Event]:
    assignments = [
        ("lin", "clean_square"),
        ("mara", "tend_field"),
        ("tao", "repair_cart"),
        ("nia", "cook_meal"),
        ("omar", "gather_herbs"),
    ]
    events: list[Event] = []
    for person_id, task_id in assignments:
        task = world.tasks[task_id]
        task.completed = False
        task.active = True
        task.progress = 0
        events.append(
            Event(
                event_type=EventType.TASK_ASSIGNED,
                timestamp=world.current_time,
                message=f"Foreman assigned {world.people[person_id].name} to {task.name}",
                actor_id="foreman",
                target_ids=[person_id],
                payload={"task_id": task_id},
            )
        )
    return events


def _make_rain_start(world: WorldState) -> list[Event]:
    world.weather = Weather.RAIN
    events: list[Event] = []
    for person in world.people.values():
        if not person.autonomous:
            continue
        payload = {"weather": "rain", "outdoor_exposure": world.is_outdoors(person)}
        message = "Rain started."
        priority = EventPriority.NORMAL
        if world.is_outdoors(person):
            message = "Rain started while you were outdoors."
            priority = EventPriority.HIGH
        events.append(
            Event(
                event_type=EventType.WEATHER_CHANGED,
                timestamp=world.current_time,
                message=message,
                actor_id=None,
                target_ids=[person.id],
                location_id=person.location_id,
                priority=priority,
                payload=payload,
            )
        )
    return events


def _make_weather_clear(world: WorldState) -> list[Event]:
    world.weather = Weather.CLEAR
    return [
        Event(
            event_type=EventType.WEATHER_CHANGED,
            timestamp=world.current_time,
            message="Rain stopped and the weather turned clear.",
            target_ids=["lin"],
            payload={"weather": "clear", "outdoor_exposure": False},
        )
    ]
