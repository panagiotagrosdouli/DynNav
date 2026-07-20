# DynNav-R Literature Review Protocol

## Objective

Determine whether DynNav-R offers a defensible research contribution beyond existing work on risk-aware navigation, safe-return constraints, reachability and viability, irreversible decisions, recovery policies, and runtime safety supervision.

The review must not attempt to prove that no related method exists. Its purpose is to identify the closest prior art, define the exact overlap, and formulate claims that remain supported after comparison.

## Research questions

1. How is recoverability, returnability, reversibility, or retained future feasibility represented in robot planning?
2. Is this quantity treated as a binary feasibility constraint, a probability, a value function, or a continuous route-level objective?
3. Which methods combine collision or traversability risk with return or recovery reasoning?
4. Which methods connect planning-time recovery estimates to a runtime supervisor or recovery policy?
5. How are irreversible commitments evaluated experimentally?
6. Which metrics and baselines are necessary for a credible DynNav-R evaluation?

## Search concept groups

### A. Recoverability and return

- recoverability-aware robot navigation
- returnability robot planning
- safe-return constraint robot planning
- recovery-aware path planning
- return policy mobile robot

### B. Irreversibility and retained options

- irreversible decision robot planning
- reversibility-aware planning robotics
- retained future feasibility robot navigation
- bottleneck commitment path planning
- viability-aware robot planning

### C. Risk and uncertainty

- risk-aware robot navigation
- CVaR motion planning
- tail-risk path planning
- belief-space navigation risk
- uncertainty-aware traversability planning

### D. Runtime supervision

- runtime safety supervisor robot navigation
- recovery policy switching robot navigation
- reach-avoid safety filter robotics
- safe mode autonomous navigation
- runtime assurance mobile robot

## Sources

Prioritize primary sources:

- conference and journal proceedings;
- publisher pages;
- official author manuscripts or arXiv versions;
- official project pages when they supplement a paper.

Target venues include RSS, ICRA, IROS, CoRL, RA-L, TRO, IJRR, Autonomous Robots, IEEE TAC, CDC, L4DC, NeurIPS, ICML, and formal-methods venues relevant to planning and runtime assurance.

## Inclusion criteria

Include a work when it satisfies at least one of the following:

1. plans robot motion under explicit risk or uncertainty;
2. requires or evaluates return to a safe or home state;
3. represents recoverability, reach-avoid feasibility, viability, or reversibility;
4. avoids irreversible commitments;
5. switches between nominal and recovery or safety policies at runtime;
6. evaluates route invalidation, degraded operation, or recovery after disturbance.

## Exclusion criteria

Exclude:

- papers that use “recovery” only for estimator reset, data recovery, or fault repair unrelated to navigation decisions;
- purely medical uses of “irreversible navigation”;
- papers without sufficient methodological information;
- duplicate preprint and final versions, retaining the final version where available;
- generic obstacle avoidance papers with no relevant risk, return, recovery, viability, or supervision component.

## Extraction fields

For each included paper record:

- citation key;
- title, authors, year, venue, DOI or stable identifier;
- robot and environment type;
- planning model;
- risk representation;
- return or recovery representation;
- binary versus continuous recovery quantity;
- route-level versus state-level quantity;
- whether recovery affects planning objective or only feasibility;
- runtime supervisor or policy switching;
- formal guarantees;
- experimental scale and platform;
- reported metrics;
- closest overlap with DynNav-R;
- remaining distinction;
- required baseline or citation role.

## Screening process

1. Title and abstract screening.
2. Full-text screening for close papers.
3. Backward citation chaining from the closest papers.
4. Forward citation chaining for later extensions.
5. Author and terminology search to catch papers using different vocabulary.
6. Re-screen the novelty statement after every ten close papers.

## Evidence labels

- **Core comparator:** method overlaps directly with the main DynNav-R claim.
- **Component prior art:** establishes one part, such as CVaR planning or runtime recovery switching.
- **Conceptual foundation:** viability, reachability, reversibility, or runtime assurance theory.
- **Evaluation precedent:** useful primarily for scenarios, metrics, baselines, or statistical design.
- **Peripheral:** relevant context but not a direct comparator.

## Claim policy

Do not write “first,” “novel,” or “has not been studied” unless the completed review provides unusually strong evidence. Prefer bounded claims such as:

> We study an interpretable continuous route-level recoverability signal that complements tail-risk estimates and drives both route selection and an auditable runtime supervisor.

Any final novelty claim must explicitly distinguish DynNav-R from:

- CVaR and traversability-risk planners;
- safe-return constrained MDP planning;
- viability and reach-avoid safety methods;
- approaches that avoid irreversible decisions;
- nominal/recovery policy switching;
- returnability-aware exploration.

## Review stopping condition

The initial review phase is complete only when:

1. at least 40 relevant papers have been screened;
2. at least 15 have received full-text comparison;
3. all core comparators have backward and forward citation chaining;
4. the evidence matrix contains no unsupported novelty statements;
5. the method and experiment plan have been revised in response to the closest prior art.
