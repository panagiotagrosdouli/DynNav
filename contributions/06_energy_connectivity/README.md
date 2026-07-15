# Energy and Connectivity-Aware Planning

[![Module](https://img.shields.io/badge/DynNav-Contribution%2006-6f42c1)](.)
[![Topic](https://img.shields.io/badge/Topic-Resource--Aware%20Planning-0366d6)](.)
[![Status](https://img.shields.io/badge/Status-Research%20Prototype-2ea44f)](.)

**English** | [Ελληνικά](README_GR.md)

<p align="center">
  <img src="assets/energy_connectivity_pipeline.svg" alt="Conceptual energy and connectivity-aware mission-feasibility pipeline" width="100%" />
</p>

<p align="center"><em>Conceptual overview. The figure is not experimental evidence, a collision-safety guarantee, or a formal mission-assurance certificate.</em></p>

This contribution studies navigation under two operational constraints that geometric planners usually omit: **finite energy** and **limited communication quality**. It evaluates candidate routes using explicit resource margins and returns an auditable mission verdict rather than treating battery and connectivity as informal penalties.

---

## Research question

> **How should a navigation system classify and select routes when battery reserve and communication constraints determine mission feasibility?**

The contribution separates three questions:

1. Is the route feasible with the currently usable battery energy?
2. Does the route maintain the required minimum communication quality?
3. Can recharge or relay support repair an otherwise infeasible route?

---

## Problem formulation

For a candidate route \(\pi\), the current implementation estimates energy as

\[
E_{\mathrm{req}}(\pi)=d(\pi)c_E,
\]

where \(d(\pi)\) is route distance and \(c_E\) is a scalar energy cost per metre. Usable energy is

\[
E_{\mathrm{use}}=\max(0,E_{\mathrm{battery}}-E_{\mathrm{reserve}}),
\]

and the energy margin is

\[
m_E=E_{\mathrm{use}}-E_{\mathrm{req}}.
\]

For a route-level minimum connectivity estimate \(q_{\min}(\pi)\) and required threshold \(q_{\mathrm{req}}\), the connectivity margin is

\[
m_Q=q_{\min}(\pi)-q_{\mathrm{req}}.
\]

A direct route is feasible when \(m_E\geq0\) and \(m_Q\geq0\). Recharge and relay flags represent simplified mitigation options.

---

## Implemented mission verdicts

| Verdict | Interpretation |
|---|---|
| `DIRECT_FEASIBLE` | Energy and connectivity constraints are satisfied directly |
| `NEEDS_RECHARGE` | Energy feasibility depends on recharge support |
| `NEEDS_RELAY` | Connectivity feasibility depends on relay support |
| `NEEDS_RECHARGE_AND_RELAY` | Both support mechanisms are required |
| `INFEASIBLE` | Available support does not repair all resource violations |

The route selector first prefers lower-support verdicts, then shorter routes, and finally larger resource margins.

---

## Repository structure

```text
06_energy_connectivity/
├── README.md
├── README_GR.md
├── assets/
│   └── energy_connectivity_pipeline.svg
├── code/
│   └── resource_feasibility.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   ├── eval_energy_connectivity.py
│   └── eval_resource_feasibility.py
└── results/
    ├── c06_energy_connectivity_summary.csv
    ├── c06_energy_connectivity_summary.md
    └── c06_resource_feasibility.csv
```

---

## Reproducibility

Run all commands from the repository root.

### Energy/connectivity route demo

```bash
python contributions/06_energy_connectivity/experiments/eval_energy_connectivity.py
```

### Mission-feasibility benchmark

```bash
python contributions/06_energy_connectivity/experiments/eval_resource_feasibility.py
```

The second command writes:

```text
contributions/06_energy_connectivity/results/c06_resource_feasibility.csv
```

A reportable run should preserve the repository commit, configuration values, route definitions, thresholds, and random seed where applicable.

---

## Evaluation protocol

The benchmark compares candidate routes representing different operational cases, including:

- a short route with weak link quality;
- a longer route with stronger connectivity;
- a route that uses recharge support;
- a route that uses a communication relay;
- a route requiring both support mechanisms; and
- an unrepaired infeasible route.

Primary outputs are energy required, usable energy, energy margin, minimum connectivity, connectivity margin, support flags, feasibility, and mission verdict.

---

## Interpretation

C06 should be interpreted as a **resource-feasibility layer**. It makes mission assumptions explicit and allows the planner or supervisor to distinguish direct execution, supported execution, and rejection.

It does not establish that the selected route is collision-free, dynamically feasible, cyber-secure, or formally safe. Those properties require separate planning and safety modules.

---

## Limitations

1. Energy consumption is modeled as distance multiplied by a scalar coefficient.
2. Terrain, payload, acceleration, turning, sensing, computation, and battery dynamics are omitted.
3. Connectivity is represented by route-level summary values rather than packet-level network behavior.
4. Recharge and relay are Boolean route attributes, not scheduling or allocation decisions.
5. Communication latency, packet loss, ROS 2 QoS, interference, and multi-hop topology are not modeled.
6. Resource feasibility does not replace collision avoidance or formal safety verification.

---

## Research directions

Relevant extensions include energy models conditioned on terrain and velocity, probabilistic connectivity fields, relay assignment, charger scheduling, joint resource-risk optimization, online battery estimation, and dynamic replanning before resource margins become negative.

A stronger future objective could optimize

\[
J(\pi)=w_L L(\pi)+w_E E(\pi)+w_Q Q_{\mathrm{loss}}(\pi)
\]

subject to explicit reserve and link-quality constraints.

---

## Scientific claims

The implementation supports the following limited claims:

- route energy and connectivity margins are computed explicitly;
- candidate routes are assigned auditable mission-feasibility verdicts;
- simplified recharge and relay support can be represented in the decision layer; and
- feasible routes can be ranked using support requirements, distance, and margins.

It does **not** support unrestricted claims of realistic battery prediction, guaranteed network availability, optimal support scheduling, or certified mission safety.

---

## Role within DynNav

C06 provides resource constraints to risk-aware planning, safe-mode supervision, multi-robot relay coordination, and active exploration. It is particularly relevant when a geometrically valid mission would become operationally fragile because of low battery reserve or communication loss.

---

## Citation and reproducibility

When using this module academically, report the exact commit, route definitions, battery budget, reserve requirement, energy coefficient, connectivity threshold, support assumptions, and benchmark command.