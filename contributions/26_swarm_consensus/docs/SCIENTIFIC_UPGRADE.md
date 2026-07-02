# C26 Scientific Upgrade Notes — Swarm Consensus Evaluation

## What was already strong

Contribution 26 already implemented a useful distributed-robotics idea:

> A robot swarm should agree on a navigation plan even when some robots are faulty, silent, or malicious.

The existing module includes:

- navigation proposals from multiple robots,
- faulty robot simulation,
- random / constant-bad / silent fault modes,
- robust outlier detection using median absolute deviation,
- weighted-median BFT consensus,
- fallback behaviour when too few robots respond.

This is important because multi-robot systems cannot blindly trust every shared plan or cost estimate.

## Main weakness before this upgrade

The original module demonstrated BFT consensus, but did not evaluate its distributed-system properties.

A reviewer could ask:

> Does consensus remain accurate when the swarm scales?

or:

> How robust is it to Byzantine robots, silent robots, and packet loss?

or:

> What is the communication overhead of reaching agreement?

## New contribution added

C26 now includes:

```text
swarm_consensus_evaluator.py
experiments/eval_swarm_consensus.py
```

The new benchmark evaluates:

- consensus accuracy,
- mission success,
- Byzantine detection recall proxy,
- communication messages,
- communication scaling,
- trust-weighted agreement,
- scalability score,
- packet-loss robustness.

## New benchmark

Run:

```bash
python contributions/26_swarm_consensus/experiments/eval_swarm_consensus.py
```

Output:

```text
contributions/26_swarm_consensus/results/c26_swarm_consensus.csv
```

The benchmark evaluates:

- honest swarms at 5, 10, 20, and 50 robots,
- swarms near the BFT fault bound,
- random Byzantine robots,
- silent robots,
- packet-loss scenarios.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 26 evaluates swarm consensus under scalability, Byzantine faults, silent robots, and packet loss using consensus accuracy, mission success, detection recall, communication overhead, trust-weighted agreement, and scalability metrics.

## Relationship to other contributions

C26 connects directly to:

- C09 multi-robot coordination under uncertainty,
- C16 federated learning, where robust aggregation is needed,
- C08 intrusion detection and trust scoring,
- C25 adversarial attack simulation,
- C20 failure explanation when consensus fails.

## Limitations

- The consensus model is a lightweight centralized simulation of proposal collection.
- Communication cost is approximated by message counts.
- Packet loss is modeled through silent robot behaviour.
- The BFT bound is used as a design reference; this is not a formally verified distributed protocol.
- Real deployment requires asynchronous networking, message authentication, clock handling, and ROS 2/DDS communication experiments.

## Next research step

The strongest extension is trust-adaptive swarm consensus:

```text
robot proposals + IDS trust scores + packet-loss evidence -> weighted robust consensus -> team plan
```

This would connect C26 with C08, C16, and C25 in a resilient multi-robot autonomy stack.
