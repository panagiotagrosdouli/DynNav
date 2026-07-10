import numpy as np
from ukf_fusion import UKF


def run_sim(seed=0, T=120, attack_start=60, bias=None):
    np.random.seed(seed)
    ukf = UKF()
    if bias is None:
        bias = np.array([1.0, 1.0, 0.5])

    # ground-truth state (x, y, yaw)
    x_true = np.array([0.0, 0.0, 0.0], dtype=float)

    detected_at = None
    triggered_steps = 0

    dt = 1.0
    u = np.array([0.05, 0.02, 0.01], dtype=float)  # vx, vy, yaw_rate

    for t in range(T):
        # truth motion
        x_true = x_true + np.array([0.05, 0.02, 0.01])

        # predict step (keeps filter aligned)
        ukf.predict(u, dt)

        # VO measurement
        z_vo = x_true + np.random.multivariate_normal(np.zeros(3), ukf.R_vo_nominal)

        # Inject attack bias after attack_start
        if t >= attack_start:
            z_vo = z_vo + bias

        # IMU measurement (yaw)
        yaw_meas = float(x_true[2] + np.random.normal(0.0, np.sqrt(ukf.R_imu_nominal[0, 0])))

        # updates
        ukf.update_vo(z_vo)
        ukf.update_imu(yaw_meas)

        # debug print
        if (t % 10 == 0) or (attack_start - 5 <= t <= attack_start + 10):
            info = ukf.last_vo_ids
            print(
                f"t={t:03d} attack={'YES' if t >= attack_start else 'no '} "
                f"d2={info['d2']:.3f} thr={info['thr']:.3f} "
                f"flagged={info['flagged']} streak={info['streak']} trig={info['triggered']} "
                f"security_alert={ukf.security_alert}"
            )

        if ukf.last_vo_ids and ukf.last_vo_ids["triggered"]:
            triggered_steps += 1

        if ukf.security_alert and detected_at is None:
            detected_at = t

    return detected_at, triggered_steps


if __name__ == "__main__":
    detected_at, triggered_steps = run_sim()
    print("Detected at step:", detected_at)
    print("VO triggered steps:", triggered_steps)
