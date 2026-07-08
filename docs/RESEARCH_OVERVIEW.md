# DynNav Research Overview

DynNav studies dynamic navigation and online rerouting in unknown or partially observed environments. The central setting is a robot that must reach a goal while reasoning about uncertain occupancy, localization error, dynamic obstacles, recoverability, and mission-level safety.

## Research question

How can an autonomous robot reroute online when its map, localization, and obstacle predictions are uncertain, while preserving a feasible recovery route and exposing interpretable safety signals?

## Scientific motivation

Shortest-path navigation is insufficient when map belief and robot state are uncertain. A geometrically short trajectory can pass through high-entropy regions, enter narrow passages with poor escape options, or continue after runtime evidence shows that the mission risk has changed. DynNav therefore treats risk, uncertainty, and recoverability as first-class quantities in the planning loop.

## Engineering motivation

The repository is organized as research software rather than a single demo. Core algorithms live in the Python package; experiments are deterministic and configuration-driven; generated artifacts are separated into `assets/` and `results/`; ROS2 and website components are explicit integration layers.

## Current evidence

Implemented or directly supported by code:

- typed navigation primitives for grid maps, poses, trajectories, and path evaluations;
- risk-aware A* planning with returnability penalties;
- dynamic rerouting, planner switching, and runtime monitoring;
- uncertainty propagation and bounded risk-field estimation;
- recoverability and returnability scoring;
- mission-risk reports and safe-mode supervision;
- deterministic benchmarking, CSV outputs, and visualization scaffolds.

Prototype or scaffolded components:

- ROS2/Nav2 integration, pending workspace-level build and robot logs;
- formal safety constraints, pending proofs and runtime certificates;
- learning-augmented policies, pending trained models and ablation studies;
- website and demo media, generated from deterministic synthetic scenarios.

## Claim discipline

DynNav should not be described as a certified autonomy stack. It is a reproducible research prototype whose claims must be traceable to code, tests, configurations, figures, or explicit future-work notes.
