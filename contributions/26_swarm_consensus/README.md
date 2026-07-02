# Contribution 26 — Swarm Consensus Navigation and Resilience Evaluation

[![Module](https://img.shields.io/badge/Module-26-purple)](.) [![Type](https://img.shields.io/badge/Type-Multi--Robot%20%2F%20Distributed-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

## Plain-language summary

A robot swarm should not execute a plan just because one robot recommends it.

Some robots may be:

```text
faulty,
silent,
compromised,
overconfident,
or affected by bad local sensing.
```

Contribution 26 implements Byzantine-fault-tolerant swarm consensus for navigation plan selection. Multiple robots submit local path proposals and cost estimates. The swarm then uses robust weighted-median consensus to select a shared navigation plan.

The upgraded version adds a resilience benchmark:

> The module does not only run consensus. It evaluates whether consensus remains accurate and useful under scaling, Byzantine faults, silent robots, and packet loss.

---

## Research Question

> **RQ26:** Can a robot swarm reach reliable navigation consensus when some robots are faulty, silent, or adversarial?

This contribution studies:

- multi-robot navigation proposals,
- Byzantine-fault-tolerant consensus,
- robust outlier detection,
- weighted-median agreement,
- silent robot / packet-loss behaviour,
- swarm scalability,
- trust-weighted agreement,
- communication overhead.

---

## Conceptual Pipeline

```text
N robots compute local plans
      ↓
robots broadcast path-cost proposals
      ↓
invalid / silent proposals are filtered
      ↓
MAD-based outlier detection
      ↓
weighted-median consensus
      ↓
team executes agreed plan
      ↓
consensus resilience evaluation
```

---

## Existing Components

The original C26 implementation includes:

- `NavProposal`,
- `ConsensusResult`,
- `SwarmRobot`,
- `BFTConsensus`,
- `SwarmCoordinator`,
- random Byzantine behaviour,
- constant-bad Byzantine behaviour,
- silent robot behaviour,
- robust median absolute deviation outlier detection,
- weighted-median consensus.

---

## Byzantine Fault Model

The module uses the common BFT design reference:

```text
f ≤ floor((N - 1) / 3)
```

where:

- `N` is the number of robots,
- `f` is the number of Byzantine or compromised robots.

The implementation is a lightweight simulation and not a formally verified distributed protocol, but it allows the repository to test the navigation consequences of faulty shared proposals.

---

## Fault Types

| Fault type | Behaviour |
|---|---|
| `random` | Sends random corrupted paths and high random costs |
| `constant_bad` | Always reports an extreme cost such as 9999 |
| `silent` | Does not respond, simulating packet loss or denial of service |

---

## New Upgrade Added

C26 now includes:

```text
swarm_consensus_evaluator.py
```

This evaluator measures:

- consensus accuracy,
- mission success,
- Byzantine detection recall proxy,
- communication messages,
- communication scaling,
- trust-weighted agreement,
- scalability score,
- agreed cost vs honest reference cost.

---

## Files

```text
26_swarm_consensus/
├── README.md
├── swarm_consensus.py
├── swarm_consensus_evaluator.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_swarm_consensus.py
└── results/
    └── c26_swarm_consensus.csv
```

---

## Quick Start

Run a single consensus round:

```python
from contributions.26_swarm_consensus.swarm_consensus import SwarmCoordinator
import numpy as np

coord = SwarmCoordinator(n_robots=6, n_byzantine=1)

grid = np.zeros((20, 20))
grid[8:12, 8:12] = 1.0

result = coord.plan(grid, start=(0, 0), goal=(18, 18))

print(f"Agreed cost:        {result.agreed_cost:.2f}")
print(f"Participants:       {result.n_participants}")
print(f"Byzantine detected: {result.n_byzantine_detected}")
print(f"Method:             {result.method}")
```

Run the new swarm-consensus benchmark:

```bash
python contributions/26_swarm_consensus/experiments/eval_swarm_consensus.py
```

This generates:

```text
contributions/26_swarm_consensus/results/c26_swarm_consensus.csv
```

---

## Benchmark Scenarios

The benchmark evaluates:

| Scenario family | Purpose |
|---|---|
| `scale_N_honest` | Tests consensus scaling with 5, 10, 20, and 50 honest robots |
| `scale_N_bft_bound` | Tests consensus near the BFT fault bound |
| `random_byzantine` | Tests random corrupted proposals |
| `silent_faults` | Tests denial-of-service / silent robots |
| `packet_loss_20pct` | Tests moderate packet loss |
| `packet_loss_35pct` | Tests severe packet loss |

---

## Evaluation Metrics

| Metric | Meaning |
|---|---|
| Consensus accuracy | Agreement cost closeness to honest reference cost |
| Mission success | Whether the agreed plan is finite and sufficiently close to the honest reference |
| Byzantine detection recall | Fraction of faulty robots detected as outliers |
| Communication messages | Approximate proposal/consensus message count |
| Communication scaling | Messages normalized by swarm size |
| Trust-weighted agreement | Combination of consensus accuracy and participation |
| Scalability score | Agreement quality penalized by communication overhead |
| Participants | Number of robots that responded |

---

## Scientific Contribution

The upgraded C26 contribution is not simply:

> Use voting to pick a swarm plan.

It is stronger:

> Evaluate robust swarm consensus under scale, Byzantine faults, silent robots, packet loss, and communication overhead.

This makes the module a measurable distributed-robotics contribution.

---

## Integration

- **Extends:** C09 multi-robot coordination under uncertainty
- **Supports:** C16 federated learning through robust aggregation ideas
- **Uses:** C08 IDS trust scores as future proposal weights
- **Stress-tested by:** C25 adversarial attack simulator
- **Explained by:** C20 failure explainer when consensus fails
- **Can trigger:** C05 safe mode when agreement quality or participation drops

Recommended runtime interface:

```text
swarm_consensus_input = {
    robot_id,
    proposed_path,
    proposed_cost,
    confidence,
    trust_score,
    communication_status
}
```

Recommended output:

```text
swarm_consensus_output = {
    agreed_path,
    agreed_cost,
    participants,
    detected_byzantine,
    consensus_accuracy,
    communication_messages,
    mission_success
}
```

---

## Limitations

- The implementation simulates centralized proposal collection rather than full asynchronous distributed consensus.
- Communication overhead is approximated by message counts.
- Packet loss is modeled as silent robots.
- The BFT bound is a design reference, not a formal verification result for this implementation.
- Real deployment requires ROS 2/DDS networking experiments, message authentication, clock handling, replay protection, and asynchronous failure handling.

---

## Next Research Step

The strongest extension is trust-adaptive swarm consensus:

```text
robot proposals
      ↓
IDS trust scores + packet-loss evidence
      ↓
trust-weighted robust consensus
      ↓
team plan or safe-mode fallback
```

This would connect C26 directly to C08, C16, and C25.

---

## Conclusion

Contribution 26 establishes the distributed swarm-consensus layer of DynNav.

The upgraded version makes the module stronger by evaluating consensus accuracy, Byzantine resilience, packet-loss robustness, communication overhead, and scalability.
