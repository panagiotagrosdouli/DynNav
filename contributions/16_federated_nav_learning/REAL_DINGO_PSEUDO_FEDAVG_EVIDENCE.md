# C16 — Actual Dingo recording and OFFLINE pseudo-client FedAvg training

**Verified successful CI:** [run #42795632447](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42795632447), with source SHA-256, 4 targeted numerical tests, actual recorded data decoding, training of federated and centralized linear predictors, and independent held-out result assertions.

## Real robotic data provenance

The historical LILocBench physical Clearpath Dingo ROS1 bag was downloaded, verified with SHA-256 `df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58`, and analyzed using the existing C13 action/odometry time alignment that uses commands available **before** the movement step.

- Actual odometry messages: **2,328**.
- Actual recorded commanded-velocity messages: **6,866**.
- Valid causally aligned movement/action steps: **2,305**.
- Source: https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/

These are physical-world recordings, but the original Dingo was **not controlled by C16**.

## What was genuinely trained

A small linear 3-output motion-step predictor was trained on `[commanded_v * dt, commanded_w * dt, dt]` to estimate next local `[dx, dy, d_yaw]`. Training-only normalization was used.

1. Split original samples chronologically, **65% train, 15% validation and 20% untouched test**.
2. Split ONLY the training block into **six disjoint, contiguous pseudo-client shards** from the single original Dingo recording.
3. Run 60 rounds of actual local supervised gradient steps and **existing C16 `FederatedServer.aggregate` FedAvg** with weighted and uniform aggregation.
4. Independently fit a centralized linear model with matched global training iterations and compare on the same untouched test with stationary and commanded-kinematic baselines.
5. Save the model weights, normalization statistics, source hash, exact split indices and output table.

This is useful algorithmic experimentation but **NOT true multi-robot federated deployment**. There is no network transmission, DDS robot discovery, distribution across independent robot trajectories, secure aggregation, or mathematically validated differential privacy.

## Actual chronological held-out results

| Method | Translational step RMSE (m) | Heading step RMSE (rad) |
|---|---:|---:|
| Centralized supervised linear | 0.00089356 | 0.00486102 |
| Weighted pseudo-FedAvg | 0.00089013 | 0.00485983 |
| Uniform pseudo-FedAvg | 0.00088997 | 0.00485984 |
| Command kinematics | 0.00120091 | 0.00500886 |
| Zero-motion | 0.02642418 | 0.01409991 |

The weighted/uniform federated and centralized results are **very similar**. The tiny observed differences in one continuous session are not evidence of statistically significant generalization, privacy preservation or superiority of a multi-robot federated algorithm. Neither a fleet-level fairness gap nor a multi-site heterogeneity claim can be grounded in one original physical robot sequence.

## Reproduction

```bash
python -m pytest -q contributions/16_federated_nav_learning/tests
python contributions/16_federated_nav_learning/experiments/eval_real_dingo_pseudoclient_fedavg.py \
  /path/to/authentic_dynamics_0.bag \
  --output-dir results/c16_real_dingo --rounds 60 --pseudo-clients 6
```

Workflow: `.github/workflows/c16-real-dingo-fedavg.yml`. Artifact `c16-recorded-dingo-pseudo-client-fedavg-training` contains `report.json` and `model_params.npz`; raw licensed bag data are not uploaded.

## Scientific gaps that remain open

- **0 verified physical C16 robot-controlled trials**.
- **0 real independently participating robot clients**; the six pseudo-clients are chronological subsequences from one Dingo.
- No `(epsilon,delta)`-DP proof, per-example gradient clipping, verified privacy accountant, or secure aggregation; historic `dp_epsilon` simulation settings in C16 should not be interpreted as a proven privacy guarantee.
- No physical robot trajectory actively chosen by a federated model, no real network reliability or privacy threat model and no independent robots/sites.
- Need a fleet with independently acquired training sessions, shared model specification, secure deployment, disjoint held-out sites, privacy protocol, energy/communication measurements, paired baselines and onsite hardware safety.

**Scientific verdict:** Actual physically recorded movement supports the numerical feasibility of offline FedAvg aggregation, with no demonstrated advantage over centralized fitting. It does **not** support the full C16 privacy-preserving multi-robot navigation hypothesis.
