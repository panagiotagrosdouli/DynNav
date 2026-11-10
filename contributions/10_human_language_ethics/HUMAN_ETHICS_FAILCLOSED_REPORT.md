# C10 — Fail-closed human and language navigation policy audit

## Executable engineering change

The historical C10 `human_ethics_policy.py` accepted invalid upstream human-state observations. A non-finite human distance (for example NaN) could cause every proximity comparison to be false and lead to a `NORMAL` decision and positive autonomous speed. The original low operator-trust or ambiguous-language state returned `ASK_OPERATOR`, but simultaneously marked `path_allowed=True` with positive caution speed, despite requiring operator confirmation.

The revised policy now validates finite, nonnegative human distance and bounded [0,1] trust/language/autonomy indicators. Unknown zone types and missing/invalid values fail closed to `BLOCK_PATH`, `max_speed=0`, `path_allowed=False` and `requires_operator_confirmation=True`. A genuine `ASK_OPERATOR` decision also disallows motion until separate confirmed authorization; requesting an operator does not constitute permission.

Targeted tests check NaN and infinity values, negative human-distance readings, unknown zone classifications, low trust and language confidence, normal corridor behavior and genuine no-go restrictions. The C10 workflow executes the actual existing nine-scenario policy benchmark and independently checks resulting action/speed/path permission fields.

## Scientific and safety limitations

These are **software policy-contract tests** on controlled generated scenarios, not a human-subjects experiment or physical human-robot interaction assessment. Safe speed limits are rule-based, not validated against real braking distance, perception uncertainty, dynamic people, cultural/ethical norms or legal requirements. No live ROS2 human detector was attached, and no physical Dingo was controlled by this contribution.

**Verified C10 human-robot physical trials: 0.**

Actual robot validation requires calibrated human detection, uncertainty and ground truth, independent collision avoidance/physical emergency stops, trained onsite safety personnel, ethical review where required and independently verified ROS2 trajectory evidence. The test result must never be described as proof of certified social or ethical safety.
