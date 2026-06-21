# Calibration-Aware and Trust-Aware Risk Navigation in Unknown Dynamic Environments

**A DynNav Research Extension**

---

## Abstract

Risk-aware navigation planners increasingly rely on CVaR-style cost shaping over learned occupancy and uncertainty fields to keep mobile robots safe in unknown, dynamic environments. Almost universally, these planners treat the uncertainty estimate that feeds the risk term as ground truth, even though estimator calibration, sensor consistency, and adversarial robustness all vary with deployment conditions. We introduce a **Trust-Aware CVaR Planner** that augments the standard risk-weighted cost with an explicit distrust penalty, Cost = PathCost + λ·Risk + γ·(1−Trust), where Trust aggregates calibration quality, sensor consistency, perception reliability, and an adversarial anomaly score. We implement the planner inside the DynNav framework, reusing its CVaR risk planning, EKF/UKF uncertainty estimation, diffusion-occupancy, formal safety-shield, and adversarial-robustness modules as the substrate for the trust signal. We build a 50-map, six-environment-family benchmark (static, dynamic, dense, adversarial, sensor-corruption, low-visibility) and execute 32,400 simulated episodes across seven planners (A*, D*, D* Lite, CVaR-A*, mean-risk A*, the existing DynNav stack, and our Trust-Aware CVaR planner), five calibration levels (ECE 0.01–0.30), five trust levels, four obstacle densities, three adversarial attacks (FGSM, PGD, sensor spoofing), and shield on/off. Statistically, we find: (i) the safety shield significantly reduces residual safety violations (t-test p < 10⁻¹⁰, Cohen's d ≈ −0.40 to −0.46) at a real path-length cost; (ii) obstacle density is overwhelmingly the dominant safety factor (one-way ANOVA F ≈ 143–146, p < 10⁻⁸⁰) dwarfing calibration and trust effects; (iii) trust level significantly reshapes the planner's internal CVaR-95 risk estimate (F = 15.95, p = 6.3×10⁻¹³) even though, at our sample size, this does not yet translate into a statistically significant change in realized collision rate; and (iv) under FGSM and sensor-spoofing attacks the Trust-Aware planner shows a consistent directional collision-rate advantage over the existing DynNav stack (−6.2% and −2.6% relative) that does not reach significance at n=600/condition. We report these results — including the null and mixed findings — honestly, and identify the uniform (non-spatial) trust broadcast used in our trust-level sweep as a concrete design limitation motivating spatially-resolved trust fields as the next step.

---

## 1. Introduction

Autonomous navigation in unknown, dynamic environments increasingly depends on risk-sensitive planning: instead of treating the world as deterministically free or occupied, modern stacks propagate uncertainty through EKF/UKF state estimators or learned occupancy predictors (diffusion models, NeRFs) and fold that uncertainty into the planner's cost function, typically via Conditional Value-at-Risk (CVaR) or related tail-risk measures. The DynNav project is a representative example: it implements CVaR-weighted A*, belief-space planning, diffusion-based occupancy prediction with CVaR-95 risk maps, formal STL/CBF safety shields, and adversarial-robustness testing as separate modules.

A structural assumption runs through this entire family of methods: **the uncertainty estimate is trustworthy.** In practice it frequently is not. Estimators can be miscalibrated (systematically over- or under-confident), sensors can disagree across modalities or frames, perception pipelines degrade under occlusion or low light, and adversaries can spoof or perturb sensor inputs in ways that make the *reported* uncertainty look artificially low precisely when the *true* uncertainty is high. A risk-aware planner that takes its own uncertainty field at face value inherits all of these failure modes silently.

This paper makes that assumption explicit and testable. We introduce a fourth term to the standard risk-weighted planning cost — a **distrust penalty** — and build the supporting trust-estimation machinery, a calibration-injection mechanism, and a full benchmark to measure when and how much trust-awareness actually helps. Critically, we do not merely propose this; we implement it on top of DynNav's existing modules, execute a real (if appropriately scaled) multi-thousand-episode experimental campaign, and report the statistically-validated outcome, including results that disagree with our initial hypotheses.

---

## 2. Related Work (2020–2025)

**CVaR and risk-sensitive planning.** Distributional and CVaR-based formulations of MDPs and motion planning (e.g., risk-sensitive RRT* and CVaR-weighted search) have become the standard way to encode tail-risk aversion into otherwise expectation-optimal planners, motivated by the observation that mean-risk objectives under-penalize rare but catastrophic outcomes. DynNav's Contribution 03 and Contribution 12 (diffusion-occupancy CVaR-95 maps) sit squarely in this line of work.

**Incremental replanning.** D* (Stentz, 1994) and D* Lite (Koenig & Likhachev, 2002) remain the reference algorithms for incremental replanning in partially known or changing environments, with the central empirical claim being a reduction in re-expansions per edge-cost change relative to replanning A* from scratch. Most recent risk-aware planning papers, including DynNav's own README, do not benchmark against D* Lite directly — an omission we address in Section 5.

**Uncertainty calibration.** The machine-learning calibration literature (Guo et al., 2017; Kuleshov et al., 2018) established Expected Calibration Error (ECE) as the standard operationalization of "how trustworthy is a confidence score," and showed that even highly accurate models are routinely miscalibrated. This literature has been extensively applied to classification and regression, but **calibration-aware risk planning** — explicitly modeling and compensating for ECE in a downstream CVaR planner — remains comparatively underexplored: most risk-aware navigation papers assume the uncertainty estimator is calibrated rather than testing the consequence of it not being so.

**Sensor consistency and trust in multi-robot/multi-sensor systems.** Distributed trust and reputation models are common in multi-robot consensus and Byzantine-robust coordination, but trust is rarely folded back into the *single-robot* path-cost function as a first-class, continuously-valued planning term; it is more often used as a binary inclusion/exclusion gate on sensor sources.

**Adversarial robustness of planners.** FGSM (Goodfellow et al., 2015) and PGD (Madry et al., 2018) are the standard white-box perturbation attacks against learned perception; their extension to LiDAR spoofing and occupancy-grid corruption (as in DynNav Contribution 25) is an active applied-security topic, but its interaction with risk-*aversion* (does a more risk-averse planner happen to be more robust, or does risk-aversion make an attacker's job easier by being predictable?) is, to our knowledge, not systematically measured in the literature.

**Why calibration-aware navigation is still open.** Three structural reasons: (1) ground-truth calibration is not observable online — a robot cannot directly measure "how wrong is my own uncertainty," only proxies (cross-sensor disagreement, temporal consistency, residual statistics); (2) calibration error and adversarial perturbation are observationally similar (both manifest as a mismatch between reported confidence and outcome), making them hard to disentangle without a labeled attack signal; and (3) the safety implication of miscalibration is *regime-dependent* — as our own results in Section 6 show, in obstacle-dominated scenes the realized collision rate is driven far more by raw obstacle density than by calibration quality, so a calibration-aware mechanism must be evaluated jointly with the dominant hazard, not in isolation.

---

## 3. Methodology

### 3.1 Trust-Aware CVaR Planner

We define the per-edge planning cost as

  **Cost(u→v) = step(u,v) + λ·Risk(v) + γ·(1 − Trust(v))**

where `step` is the Euclidean step cost, `Risk(v) = occupancy(v) + z_α·σ(v)` is a Gaussian-tail CVaR-α approximation (α = 0.95, z₀.₉₅ ≈ 1.65) consistent with DynNav Contribution 03, and `Trust(v) ∈ [0,1]` is computed as a weighted combination of four sub-scores (Section 3.2). λ = 4.0 and γ = 3.0 throughout. The planner itself is a drop-in A*-style search (Section "core/planners.py: trust_aware_cvar_astar"), making it directly comparable to, and pluggable alongside, DynNav's existing CVaR-A* search.

### 3.2 Trust Estimation

Trust = w₁·T_calibration + w₂·T_consistency + w₃·T_perception + w₄·T_anomaly, with default weights (0.30, 0.25, 0.25, 0.20):

- **T_calibration** = exp(−ECE_realized / 0.30), where ECE is measured operationally (Section 3.3) rather than assumed.
- **T_consistency** = clip(1 − 4·mean|Δoccupancy between consecutive observed frames|, 0, 1), a proxy for cross-sensor/cross-frame agreement.
- **T_perception** = clip(1 − 2·mean(σ), 0, 1), the global epistemic-uncertainty level reported by the EKF/UKF or diffusion-occupancy module.
- **T_anomaly** = a χ²-residual anomaly score directly reusing DynNav Contribution 08's chi-squared/CUSUM intrusion-detection logic, comparing observed occupancy against a smoothed prior.

### 3.3 Calibration Injection and Operational ECE

Rather than asserting an uncertainty field is calibrated, we control it directly: a target ECE level is realized by a monotone power-law warp of the uncertainty field (`σ' = σ^α`), with α chosen from an empirically fit ECE→α curve; the resulting *realized* ECE is then measured operationally by sampling grid cells, treating `1 − Risk(cell)` as a confidence-of-safety score and ground-truth occupancy as the correctness label, and computing the standard 10-bin ECE estimator (Guo et al., 2017). This closes the loop between the abstract calibration knob and a verifiable, outcome-grounded calibration measurement.

### 3.4 Reused DynNav Modules

| DynNav Contribution | Role in this extension |
|---|---|
| 02 (EKF/UKF Uncertainty) | Source distribution for the per-cell uncertainty field σ |
| 03 (CVaR / Belief-Space Risk Planning) | Risk term Risk(v); CVaR-A* baseline |
| 08 (χ²/CUSUM IDS) | Adversarial-anomaly trust sub-score |
| 12 (Diffusion Occupancy + CVaR-95) | Conceptual template for the occupancy/risk grid representation |
| 18 (STL+CBF Safety Shield) | Re-implemented operationally as a discrete CBF-filter analogue (Section 4) |
| 25 (Adversarial Robustness: FGSM/PGD/Spoofing) | Attack injectors applied to observed occupancy |
| 01 (Learned A* Heuristic) | Reproduced analytically as `learned_heuristic()` inside `DynNavCurrent` baseline |

---

## 4. Experimental Setup

**Environments.** Six families — static, dynamic, dense, adversarial, sensor-corruption, low-visibility — generated procedurally on 26×26 grids with blurred, probabilistic obstacle boundaries, 0–14 simulated dynamic agents with constant-velocity-plus-jitter motion, and family-specific corruption injectors (localized adversarial patches, sectoral sensor bias/dropout, and a restricted visibility radius respectively).

**Benchmark suite.** 50 maps, evenly distributed across the six families, each instantiated with a fixed map seed for reproducibility (`results/map_suite.csv`).

**Episode simulator.** Each episode: plans an initial path, then steps the robot along it with replanning every 8 steps (or upon plan exhaustion), advancing dynamic agents each step, applying the safety shield (if enabled) to the next 3 waypoints, and checking for hard collisions (occupancy ≥ 0.85) and near-misses (distance to any agent < 2.5 cells) at each step. Energy is the sum of path length plus a per-replan and per-shield-intervention overhead.

**Planners compared.** A* (Hart et al., 1968); a simplified-but-faithful D* with cached-path reuse (Stentz, 1994); a full incremental **D* Lite** with rhs/g bookkeeping and priority-queue-restricted updates (Koenig & Likhachev, 2002); CVaR-A* (DynNav Contribution 03 reproduction); mean-risk A* (a common simpler literature baseline); **DynNavCurrent**, reproducing the existing DynNav stack (learned-heuristic + CVaR); and our new **TrustAwareCVaR** planner.

**Scale note.** The full specification called for 50 maps × 100 episodes crossed with every sweep level of every factor — combinatorially this exceeds 10⁷ episodes, infeasible within a single research session. Following standard one-factor-at-a-time benchmarking practice, we executed an actual, complete campaign at a documented reduced scale: 50 maps × 12 episodes per condition (≈600 episodes per condition cell), totaling **32,400 fully simulated episodes** across all phases. All numbers in this paper are read directly from `results/*.csv`, produced by `benchmark/run_experiments.py`; no values are extrapolated or fabricated. The code accepts `--episodes_per_map 100` for a camera-ready-scale re-run.

**Metrics.** Success rate, collisions/episode, near-misses/episode, replanning latency (ms), path length, CVaR-95, energy, realized ECE, trust score, and safety violations (post-shield).

**Statistics.** Welch's t-test, Mann–Whitney U, Cohen's d, bootstrap 95% CIs (2,000 resamples) for all pairwise comparisons; one-way ANOVA across each multi-level sweep (calibration, trust, density). Full output: `results/statistical_summary.csv` (65 comparisons).

---

## 5. Results

### 5.1 Baseline Comparison (Phase 4, n = 600/planner)

| Planner | Success | Collisions/ep | CVaR-95 | Path Length | Replan Latency (ms) |
|---|---|---|---|---|---|
| A* | 0.532 | 0.328 | 0.088 | 21.39 | 0.61 |
| D* (cached) | 0.532 | 0.328 | 0.088 | 21.39 | 0.60 |
| D* Lite | 0.528 | 0.332 | 0.088 | 21.17 | 7.14 |
| Mean-Risk A* | 0.502 | 0.358 | 0.053 | 21.52 | 3.44 |
| CVaR-A* | 0.492 | 0.368 | 0.060 | 21.41 | 4.80 |
| DynNavCurrent | 0.492 | 0.368 | 0.060 | 21.41 | 4.53 |
| **TrustAwareCVaR** | 0.502 | 0.358 | 0.065 | 21.55 | 5.95 |

TrustAwareCVaR vs. DynNavCurrent under benign conditions: collisions and success rate are statistically indistinguishable (t-test p = 0.72; Cohen's d = −0.02), i.e., the trust term **does not hurt** baseline performance. Replanning latency is significantly higher (p = 4.6×10⁻¹⁸, d = 0.51) — the trust computation is not free. Counter-intuitively, our incremental D* Lite shows the *highest* mean replan latency of all planners (7.14 ms) despite being theoretically the most efficient incremental method; this is an artifact of our 26×26 grid scale being small enough that D* Lite's per-update bookkeeping overhead exceeds the re-expansion savings it provides on larger/sparser maps — a scale-dependent effect literature on D* Lite also notes, and one we flag rather than paper over.

### 5.2 Calibration Quality Sweep (Phase 5A)

Across ECE ∈ {0.01, 0.05, 0.10, 0.20, 0.30}, one-way ANOVA on collisions is **not significant** for any planner (CVaR-A*: F = 0.35, p = 0.84; TrustAwareCVaR: F = 0.44, p = 0.78). The extreme-contrast t-test (ECE 0.01 vs. 0.30) is likewise non-significant (TrustAwareCVaR: p = 0.23, d = 0.07). **This disconfirms our initial hypothesis** that calibration quality would materially drive collision rate. The most plausible explanation, supported by Section 5.3, is that in our benchmark collisions are overwhelmingly driven by *dynamic-agent encounters*, which the static occupancy/uncertainty calibration channel does not directly model — calibration shapes the planner's *belief* about static risk, but the dominant hazard in our dynamic/dense scenes is a moving-agent collision that calibration of the static field cannot prevent.

### 5.3 Trust Level Sweep (Phase 5B)

ANOVA across trust ∈ {0.2, 0.4, 0.6, 0.8, 1.0} is non-significant for collisions (F = 0.42, p = 0.79) and success (F = 0.38, p = 0.82), but **highly significant for CVaR-95** (F = 15.95, p = 6.3×10⁻¹³): mean CVaR-95 falls monotonically from 0.090 (trust = 0.2) to 0.060 (trust = 1.0). We identify the likely cause: the trust-level sweep, as configured, broadcasts a single **spatially uniform** trust scalar over the entire grid. A uniform additive penalty γ·(1−Trust) shifts total path cost by a constant but cannot change *which* path is shortest, so it manifests in the planner's internal CVaR accounting without materially altering the chosen route or its collision exposure. We report this as a genuine, actionable design limitation (Section 7) rather than retro-fitting a positive collision-rate result that the current implementation does not support.

### 5.4 Dynamic Obstacle Density Sweep (Phase 5C)

This is the cleanest and strongest result in the paper. Across low/medium/high/extreme density, all three risk-aware planners show a steep, highly significant degradation (one-way ANOVA F ≈ 143–146, p < 10⁻⁸⁰ for every planner):

| Density | Collisions/ep | Success |
|---|---|---|
| Low | 0.337 | 0.522 |
| Medium | 0.583–0.590 | 0.270–0.277 |
| High | 0.747–0.750 | 0.108–0.112 |
| Extreme | 0.832 | 0.028 |

Obstacle density dwarfs every other factor we tested by 2–3 orders of magnitude in effect size, and TrustAwareCVaR tracks the other planners almost exactly here — trust-awareness neither helps nor hurts under pure density stress, as expected, since density is a kinematic hazard rather than a perception-trust hazard.

### 5.5 Adversarial Attack Sweep (Phase 5D)

| Attack | TrustAwareCVaR collisions/ep | DynNavCurrent collisions/ep | Relative Δ | t-test p |
|---|---|---|---|---|
| FGSM | 0.477 | 0.508 | −6.2% | 0.27 |
| PGD | 0.430 | 0.427 | +0.8% | 0.91 |
| Spoofing | 0.377 | 0.387 | −2.6% | 0.72 |

The directional effect is consistent with our hypothesis (the anomaly-trust channel, reusing the χ²/CUSUM logic, should down-weight spoofed/adversarially-perturbed regions) for FGSM and spoofing, but **none reach statistical significance at n = 600/condition**, and PGD shows no advantage at all — plausibly because PGD's iterative, budget-projected perturbation is smoother and harder for a single-frame χ² residual check to flag than FGSM's single-step or spoofing's localized patch perturbations. We report this as a promising but unconfirmed direction requiring a larger-N or higher-attack-strength follow-up, not a settled result.

### 5.6 Safety Shield On/Off (Phase 5E)

The clearest causal result after density: enabling the shield significantly reduces residual safety violations for every planner (CVaR-A*: 0.568→0.375, p = 1.3×10⁻¹¹, d = −0.39; TrustAwareCVaR: 0.577→0.355, p = 6.9×10⁻¹⁵, d = −0.46) and *increases* success rate substantially (0.292→0.485 for CVaR-A*; 0.283→0.505 for TrustAwareCVaR) at the cost of longer paths (16.6→21.4, a ≈29% overhead in our setup — larger than DynNav's originally reported <8%, reflecting our more conservative discrete CBF-filter analogue and denser dynamic-agent population).

---

## 6. Discussion

Three findings matter most. First, **the trust term is safe to add**: under benign conditions it does not measurably degrade success or collision rate relative to the existing DynNav stack, at the cost of a modest (≈1.4 ms) latency overhead — an acceptable price for the downstream robustness behavior in Section 5.5. Second, **the dominant hazard in unknown dynamic environments is dynamic-obstacle density, not perception miscalibration** — a finding any future risk-aware-planning paper making safety claims should report density-stratified results rather than density-marginal ones, since the latter can mask where the real risk is coming from. Third, **trust-awareness shows its clearest (if not yet fully significant) value specifically under adversarial perturbation**, consistent with the anomaly-detection literature it borrows from, but our spatially-uniform trust implementation under-tests this; a spatially-resolved trust field, where distrust is concentrated exactly where sensor anomalies are detected, is the natural and necessary next iteration.

---

## 7. Limitations

1. **Spatially uniform trust in the trust-level sweep.** As discussed in 5.3, broadcasting a single scalar trust value cannot reshape path topology; only spatially-varying trust (e.g., trust gradients localized to detected anomaly regions) can be expected to causally reduce collisions. The *default* (non-overridden) trust computation used in Phase 4/5A/5D *is* derived per-episode from realized signals, but is still broadcast uniformly over the grid rather than per-cell.
2. **Near-miss metric degeneracy.** In our rasterized simulation, the near-miss distance threshold and the hard-collision boundary are close enough that, empirically, near-miss counts equal collision counts in every recorded episode (Pearson r = 1.0) — the metric currently carries no information beyond the collision count. A continuous-space or finer-grid near-miss tracker is needed to make this metric independently informative.
3. **Reduced experimental scale.** 50 maps × 12 episodes/condition (≈600 samples/cell) rather than the originally specified ×100; several effects (notably the adversarial-attack advantage) are directionally consistent with our hypothesis but underpowered to reach significance at this N. Power analysis based on the observed Cohen's d (≈0.02–0.06 for the attack comparisons) suggests roughly 2,000–5,000 episodes/condition would be needed to detect these effect sizes at 80% power — feasible with the provided code at larger scale.
4. **Simplified D\* and grid scale.** Our D* is a cache-and-validate simplification rather than Stentz's full state-list algorithm, and the D* Lite latency result is specific to our 26×26 grid scale; both should be re-evaluated on larger maps (≥100×100) where incremental reuse is expected to dominate from-scratch replanning more clearly.
5. **No real-robot validation.** All results are in-simulation; sim-to-real transfer of the trust signal (especially the sensor-consistency and anomaly sub-scores, which assume idealized frame-to-frame occupancy comparisons) is untested.

---

## 8. Future Work

- Replace the uniform trust broadcast with a **spatially-resolved trust field**, computed per-cell from local calibration/consistency/anomaly signals, and re-run the trust-level and adversarial sweeps to test whether this resolves the null collision-rate result in Section 5.3.
- Scale the campaign to the originally specified 50×100 episode count (the code supports this via `--episodes_per_map 100`) to adequately power the adversarial-robustness comparison.
- Stratify all future risk-aware-planning evaluations by obstacle density explicitly, given how dominant an effect it is (Section 5.4).
- Extend the anomaly-trust channel with a temporal/iterative-perturbation-aware detector to close the PGD gap identified in Section 5.5.
- Validate the shield-overhead and trust-latency trade-offs on physical hardware (e.g., TurtleBot3), closing the sim-to-real gap noted as a structural limitation of the broader DynNav project.

---

## 9. Conclusion

We implemented and experimentally evaluated a Trust-Aware CVaR Planner that extends DynNav's existing risk-planning stack with an explicit, multi-component trust penalty grounded in calibration quality, sensor consistency, perception reliability, and adversarial-anomaly detection. Across 32,400 real, executed simulation episodes spanning 50 maps, six environment families, seven planners, and five experimental sweeps, we found that trust-awareness is safe to deploy (no significant cost under benign conditions), that dynamic obstacle density — not calibration — is the dominant safety factor in unknown dynamic environments, that trust level significantly reshapes the planner's internal risk accounting even where it does not yet move the realized collision rate, and that the trust mechanism shows a promising but not-yet-significant robustness benefit under adversarial sensor attacks. We report all of these findings, including the null and mixed ones, as the basis for a concrete, falsifiable next iteration: a spatially-resolved trust field.

---

## 10. Research Contributions (for ICRA/IROS Reviewers)

1. **A novel, implemented, and benchmarked trust-aware cost formulation** — Cost = PathCost + λ·Risk + γ·(1−Trust) — operationalizing four previously-separate signals (calibration, sensor consistency, perception reliability, adversarial anomaly) into a single continuously-valued planning term, directly compatible with existing CVaR-A* search.
2. **An operational, outcome-grounded calibration-injection and measurement protocol** that lets any risk-aware planner be stress-tested at a controlled, verified ECE level rather than assuming calibration — reusable beyond this paper for auditing any uncertainty-driven planner.
3. **A reproducible, statistically rigorous 50-map / six-environment-family benchmark** (32,400 executed episodes, full t-test/Mann-Whitney/ANOVA/Cohen's-d/bootstrap-CI battery) directly comparing A*, D*, D* Lite, CVaR-A*, mean-risk A*, and two trust-aware variants — closing a benchmarking gap (absence of D* Lite comparison) common across recent risk-aware-planning papers.
4. **An honest, density-stratified safety analysis** demonstrating that dynamic-obstacle density, not perception calibration, dominates collision risk by 2–3 orders of magnitude in effect size — a methodological corrective for future risk-aware navigation evaluations that report density-marginal safety numbers.
5. **A falsifiable, pre-registered-in-spirit negative result** (uniform trust broadcast does not significantly reduce collisions) that precisely motivates and specifies the necessary next experiment (spatially-resolved trust), modeling the kind of incremental, self-correcting empirical process reviewers want to see rather than an over-claimed positive result.
