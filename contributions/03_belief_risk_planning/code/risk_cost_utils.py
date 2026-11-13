"""
risk_cost_utils.py

Utility συναρτήσεις για cost σε risk-aware navigation με ανθρώπινες προτιμήσεις.

Κύρια συνάρτηση:

    human_aware_edge_cost(
        base_length,
        edge_risk,
        lambda_effective,
        human_pref,
        is_dark=False,
        is_low_feature=False,
        low_feature_penalty=5.0,
        dark_area_penalty=5.0,
    )

Αυτή υλοποιεί:

    cost = base_length + lambda_effective * edge_risk
           + penalties(αν ο άνθρωπος θέλει να αποφεύγει σκοτεινές / low-feature περιοχές)
"""

from pathlib import Path
import sys

# C03's historical ethical-cost helper uses source owned by C10.
# Resolve it by repository-relative path so the helper works from any cwd.
_C10_CODE = Path(__file__).resolve().parents[3] / "contributions" / "10_human_language_ethics" / "code"
if str(_C10_CODE) not in sys.path:
    sys.path.insert(0, str(_C10_CODE))

from user_preferences import HumanPreference
from ethical_risk_policy import EthicalRiskPolicy, EthicalRiskConfig

def human_aware_edge_cost(
    base_length: float,
    edge_risk: float,
    lambda_effective: float,
    human_pref: HumanPreference,
    is_dark: bool = False,
    is_low_feature: bool = False,
    low_feature_penalty: float = 5.0,
    dark_area_penalty: float = 5.0,
) -> float:
    """
    Υπολογίζει το κόστος ενός edge / segment με βάση:

        base_length           : γεωμετρικό μήκος / χρόνο / energy
        edge_risk             : κάποιο risk metric (π.χ. κοντά σε εμπόδια, μεγάλη αβεβαιότητα)
        lambda_effective      : risk weight μετά τον συνδυασμό robot + human
        human_pref            : αντικείμενο HumanPreference
        is_dark               : αν η ακμή περνάει από σκοτεινή περιοχή
        is_low_feature        : αν η ακμή περνάει από low-feature περιοχή
        low_feature_penalty   : penalty για low-feature περιοχές (αν το ζητά ο άνθρωπος)
        dark_area_penalty     : penalty για σκοτεινές περιοχές (αν το ζητά ο άνθρωπος)

    Επιστρέφει:
        cost = base_length + lambda_effective * edge_risk + penalties
    """
    cost = base_length + lambda_effective * edge_risk

    if human_pref.avoid_dark_areas and is_dark:
        cost += dark_area_penalty

    if human_pref.avoid_low_feature_areas and is_low_feature:
        cost += low_feature_penalty

    return cost
def human_and_ethical_edge_cost(
    base_length: float,
    physical_risk: float,
    lambda_weight: float,
    ethical_policy: EthicalRiskPolicy,
    near_human: bool = False,
    in_private_zone: bool = False,
    in_vulnerable_area: bool = False,
) -> dict:
    """
    Compute a combined cost that includes:
      - base geometric length
      - physical risk scaled by lambda_weight
      - ethical risk as defined by ethical_policy

    Returns a dict so it is easy to log all components.
    """
    # Physical risk cost term (lambda * R_phys)
    physical_risk_cost = lambda_weight * physical_risk

    total_cost, ethical_risk = ethical_policy.edge_total_cost(
        base_length=base_length,
        physical_risk_cost=physical_risk_cost,
        near_human=near_human,
        in_private_zone=in_private_zone,
        in_vulnerable_area=in_vulnerable_area,
    )
    return {
        "total_cost": total_cost,
        "base_length": base_length,
        "physical_risk": physical_risk,
        "physical_risk_cost": physical_risk_cost,
        "ethical_risk": ethical_risk,
        "lambda_weight": lambda_weight,
    }


def path_risk_sum(path, risk_grid):
    """
    Sum of risk along a path.
    Assumes risk_grid is indexed as risk_grid[y, x].
    Path is an iterable of (x, y) tuples.
    """
    r = 0.0
    for (x, y) in path:
        r += float(risk_grid[int(y), int(x)])
    return r


def path_length_l2(path):
    """Euclidean length of polyline path."""
    if path is None or len(path) < 2:
        return 0.0
    import math
    L = 0.0
    for i in range(1, len(path)):
        x0, y0 = path[i-1]
        x1, y1 = path[i]
        L += math.hypot(x1 - x0, y1 - y0)
    return float(L)


