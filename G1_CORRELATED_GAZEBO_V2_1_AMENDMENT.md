# G1 Correlated Gazebo V2.1 Commissioning Amendment

**Freeze date:** 2026-09-25  
**Status:** frozen after the V2.0 validity failure and before any V2.1 execution outcome.

## Why this amendment is allowed

The V2.0 smoke produced no efficacy observation: neither hazard trigger was observed in any of the 9 trials and no dynamic closure was applied. The retained V2.0 artifact is therefore treated only as an execution-validity diagnostic.

V2.1 changes only the measurement/clearance plumbing needed to make the preregistered mechanism observable in Nav2/Gazebo. The scientific hazard law and comparison remain unchanged.

## Scientific quantities that remain frozen

- marginal closure probabilities: `p1=p2=0.5`;
- dependence conditions: `independent`, `common_cause`, `anti_correlated`;
- robust joint interval: `q=P(C1=1,C2=1) in [0,0.5]`;
- recoverability weight: `12.0`;
- planner conditions: `DynNavShortest`, `DynNavHistory`, `DynNavRobustHistory`;
- action-triggered activation semantics;
- parallel-return truth-table target `(1,1,1,0)` and `kappa=-1`;
- paired latent draws by dependence/repetition;
- primary outcomes and claim boundary.

## Amendment A — corridor clearance

V2.0 used 1.55 m physical corridors. Live Nav2 obstacle/inflation updates could eliminate traversable clearance before any injected closure. V2.1 widens the symmetric top and bottom corridors to **2.05 m** while preserving the same two-parallel-return topology.

Frozen V2.1 world geometry:

- world width: `7.0 m`;
- world height: `6.4 m`;
- outer wall thickness: `0.15 m`;
- central island x-range: `1.5..5.5 m`;
- central island y-range: `2.2..4.2 m`;
- bottom corridor physical width: `2.05 m`;
- top corridor physical width: `2.05 m`;
- blocker footprint: `0.40 x 2.05 x 1.00 m`.

Start/safe-region center becomes `(0.8, 5.225)` m and goal becomes `(6.2, 5.225)` m. Blocker centers become `(1.8,5.225)` and `(1.8,1.175)`.

## Amendment B — continuous action-trigger gates

The causal event remains an executed forward crossing at the same frozen x-locations. It is no longer tied to one exact y-row sampled at one controller instant.

- trigger 0 crosses x boundary `3.625 -> 3.675 m`;
- trigger 1 crosses x boundary `4.625 -> 4.675 m`;
- both are centered on top-corridor y=`5.225 m`;
- trigger gate half-width: `0.75 m`.

The planner encodes every directed grid edge intersecting the same gate as an equivalent action trigger. The runtime detects geometric crossing of the same continuous gate from consecutive executed poses and publishes the corresponding predeclared grid edge.

Normal multi-cell displacement between controller feedback samples is valid. Only a large pose discontinuity (`>0.75 m` between successive samples) is treated as a localization-jump validity failure.

## Amendment C — asynchronous executed-event authority

Executed-transition messages are authoritative action observations. A concurrent Nav2 replan may synchronize the planner's current position before the queued event message arrives; therefore source mismatch with the planner-synchronized position is logged but no longer causes the executed event to be rejected.

The per-trial `__RESET__` semantics remain mandatory.

## Pre-outcome route-ordering check

At 5 cm resolution the direct route remains approximately 108 transitions. The second trigger remains about 31 cells before the goal. The widened symmetric detour is approximately 270 transitions.

Thus, using the already frozen recoverability weight 12:

- independence-history direct objective is approximately `108 + 31*3 = 201 < 270`;
- arbitrary-dependence robust direct objective is approximately `108 + 31*6 = 294 > 270`.

The intended planner ordering therefore remains unchanged without weight retuning.

## V2.1 smoke gate

The first V2.1 run remains a commissioning smoke with one paired repetition per dependence condition (9 trials). It is interpreted only for:

- all 9 trials protocol-valid;
- topology contract still exactly `(1,1,1,0)`;
- trigger gates observable when the selected route crosses them;
- blocker injection/reset integrity;
- no localization-jump invalidity;
- complete paired artifact generation.

No V2.1 smoke efficacy comparison will be promoted as a result.

## Confirmatory target

If and only if the V2.1 smoke passes the validity gate, the already frozen confirmatory target is 10 paired repetitions per dependence condition (90 valid trials).

Any further change to geometry, trigger-gate width, hazard probabilities, dependence law, recoverability weight, or planner objective after inspection of V2.1 outcomes requires another protocol version.
