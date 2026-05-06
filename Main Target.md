
# Digital Human World: Project Concept Document

## I. Project Definition

“Digital Human World” is neither a traditional multi-agent system nor a modular agent platform based on “external memory + planner + tool calling.”

Its goal is to construct a **continuously running digital social environment**, within which a group of “proto-humans” are placed—namely, **neural individuals with limited initial capabilities, internally generated memory, and behaviors directly produced by compact models**.

These individuals continuously perceive the environment, take actions, receive feedback, and accumulate experience, gradually evolving from “proto-humans” into “intelligent humans” with skills, habits, preferences, social relationships, and long-term memory.

In other words, the focus of this project is not merely:

> **How agents complete tasks**,

but rather:

> **How a neural individual with endogenous memory grows into a stable, social digital human within a persistent world.**

Therefore, the core of this project lies not in *external orchestration*, but in *internal formation*:

* How memory is formed
* How skills emerge
* How behavior stabilizes
* How social relationships accumulate
* How individuals evolve continuously through interaction with the environment and others

---

## II. Core Ideas

This project is built on three key ideas.

### 1. Individuals Are Neural Entities, Not Agent Shells

Each individual is not a combination of “LLM + memory database + tool caller,” but a **compact neural model that directly receives environmental descriptions and outputs actions**.

Inputs include:

* Textual descriptions of vision
* Textual descriptions of sound
* Self state and local context
* Previous short-term internal state

Outputs include:

* THINK (optional internal cognition)
* Actions such as DO / GO / USE / SPEAK / LEARN

Core abilities, long-term preferences, and stable skills are primarily stored in **model parameters**, rather than external knowledge bases.

---

### 2. Memory: Short-Term Implicit State + Long-Term Parametric Memory

A dual-layer memory structure is adopted:

* **Short-term memory**:
  Exists in hidden states or temporary internal context, carrying current situations, recent experiences, and immediate goals.

* **Long-term memory**:
  Stored in model weights via training and consolidation, representing skills, habits, preferences, and stable knowledge.

Thus, growth is not just “storing more records,” but:

* Recent experiences influence current state
* Repeated and valuable experiences reshape long-term behavior

---

### 3. Environment as the Sole Reality Layer

Individuals output actions, but **the environment determines reality updates**.

The environment is responsible for:

* Receiving actions
* Validating feasibility
* Updating world state (buildings, resources, weather, positions, interactions)
* Feeding updated perceptions back to individuals

Thus:

> **Individuals propose intentions; the environment determines reality.**

---

## III. Overall Architecture

The system consists of three layers:

### 3.1 World Layer

The objective reality of the digital society:

* Maps and spatial layout
* Buildings, homes, workplaces
* Weather, time, seasons
* Resource distribution
* Individual positions and proximity
* Event logs and evolution

It handles **facts, not cognition**.

---

### 3.2 Individual Layer (Neural Person)

Each individual is a continuously running neural unit with:

* Perception interface
* Short-term state
* Long-term parametric memory
* Action generation
* Learning capability

It is a **developing neural entity**, not a rule-based system.

---

### 3.3 Development Layer

Responsible for growth:

* Experience accumulation
* Short-term updates
* Long-term consolidation
* Skill acquisition
* Individual differentiation
* Social feedback

This layer focuses on **long-term developmental trajectories**.

---

## IV. Structure of a Digital Individual

### 4.1 Inputs

At time (t), inputs include:

#### (1) Vision

Text descriptions like:

* “A house ahead, farmland on the left, two people carrying wood in the distance”

#### (2) Sound

* “You hear hammering”
* “A says: It’s raining, go inside”

#### (3) Self State

* Hunger
* Fatigue
* Emotion
* Location
* Tools held

#### (4) Hidden State

* “I’m going home”
* “A warned me about rain”

---

### 4.2 Outputs

#### THINK (optional)

* “Need to go home before rain gets stronger”

#### ACTION

* GO home
* DO cleaning
* USE hammer
* SPEAK "Come help me"
* LEARN observe_carpentry
* REST

---

### 4.3 Short-Term Memory

* Limited capacity
* Short lifespan
* Maintains continuity

---

### 4.4 Long-Term Memory

Stored in parameters:

* Skills
* Preferences
* Habits
* Personality

Example:

* Learned carpentry
* Prefers going home before rain

---

## V. Environment Design

### Responsibilities

1. State maintenance
2. Perception generation
3. Action validation
4. Event propagation
5. Feedback loop

---

### Inspector Module

Converts environment into structured text perception.

---

### Dynamic Systems

* Weather
* Buildings
* Work tasks
* Social propagation

---

## VI. Learning and Growth

### 6.1 Growth Mechanism

> Experience → Short-term change → Accumulation → Consolidation → Parameter update

---

### 6.2 Dual Timescale Learning

* High-frequency: short-term updates
* Low-frequency: consolidation

---

### 6.3 Learning Sources

1. Instruction
2. Observation
3. Trial and error

---

### 6.4 LEARN Action

Represents **learning intent**, not immediate training.

---

## VII. System Loop

1. Environment update
2. Perception generation
3. Model inference
4. Action validation
5. World update
6. Short-term update
7. Long-term consolidation

---

## VIII. Research Focus

* Memory formation
* Individual continuity
* Growth mechanisms
* Social emergence

---

## IX. Differences from Traditional Agents

* Endogenous vs external
* Growth vs execution
* Development vs function
* Personality vs modularity

---

## X. Technical Challenges

* Stable long-term memory
* Short-term continuity
* Decoupling learning and inference
* Multi-agent scalability
* Interpretability

---

## XI. MVP Recommendation

### Setup

* Small town
* 5–20 individuals
* Basic actions and tasks

### Goals

1. Continuous operation
2. Short-term continuity
3. Long-term behavioral differentiation

---

## XII. Development Roadmap

1. Survival agents
2. Habitual agents
3. Skill-learning agents
4. Social agents
5. Emergent society

---

## XIII. One-Sentence Summary

> **A developmental multi-agent system where neural individuals with endogenous memory evolve through experience within a persistent environment.**

---

## XIV. Conclusion

The goal is not:

* Running models in a map

But:

* True continuity
* Internalized experience
* Behavior as growth outcome
* Emergent digital society

Ultimately, this project explores:

> **How neural individuals become human within a world.**
