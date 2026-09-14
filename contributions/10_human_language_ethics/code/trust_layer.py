from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TrustState:
    """
    Trust value T in [0, 1].

    Εδώ το T το ερμηνεύουμε ως:
      - "πόσο θεωρούμε ότι ο άνθρωπος εμπιστεύεται την αυτονομία"
      - και αντιστρόφως: όταν T χαμηλό, το ρομπότ πρέπει να γίνει ΠΙΟ προσεκτικό.
    """
    value: float = 0.8  # αρχικό trust (σχετικά υψηλό)


class TrustManager:
    """
    Simple trust dynamics model.

    - trust ↓ όταν:
        * έχουμε πολλά failures / regret
        * ενεργοποιείται safe_mode
    - trust ↑ όταν:
        * το σύστημα φέρεται συντηρητικά όταν υπάρχει σοβαρή γλωσσική προειδοποίηση
        * δεν υπάρχουν πρόσφατα προβλήματα
    """

    def __init__(self, alpha_down: float = 0.15, alpha_up: float = 0.05):
        self.alpha_down = alpha_down
        self.alpha_up = alpha_up

    def update(
        self,
        trust: TrustState,
        self_healing_decision: Dict,
        language_decision: Optional[Dict],
    ) -> TrustState:
        t = trust.value

        # 1. Πτώση εμπιστοσύνης λόγω τεχνικών προβλημάτων
        reasons: List[str] = self_healing_decision.get("reasons", [])
        safe_mode: bool = bool(self_healing_decision.get("safe_mode", False))

        if reasons:
            # έχουμε ήδη κάποια σοβαρή ένδειξη (drift, failure κτλ.)
            t -= self.alpha_down

        if safe_mode:
            # safe_mode ⇒ ο άνθρωπος αντιλαμβάνεται ότι το σύστημα "δυσκολεύεται"
            t -= self.alpha_down

        # 2. Άνοδος εμπιστοσύνης όταν:
        #   - δεν υπάρχουν λόγοι self-healing
        #   - αλλά υπήρξε κάποια γλωσσική προειδοποίηση που λήφθηκε υπόψη
        if not reasons and language_decision is not None:
            factors = language_decision.get("factors", [])
            risk_scale = float(language_decision.get("risk_scale", 1.0))

            if factors and risk_scale > 1.0:
                # το ρομπότ "άκουσε" τη γλώσσα και έγινε πιο προσεκτικό
                t += self.alpha_up

        # 3. Clamp σε [0, 1]
        t = max(0.0, min(1.0, t))
        trust.value = t
        return trust

    def compute_trust_weighted_risk(self, base_risk_scale: float, trust: TrustState) -> float:
        """
        Όσο ΜΙΚΡΟΤΕΡΗ η εμπιστοσύνη, τόσο μεγαλύτερη συντηρητικότητα.

        effective_risk = base_risk * (1 + β * (1 - T))

        όπου β = 0.7 π.χ.
        """
        beta = 0.7
        return base_risk_scale * (1.0 + beta * (1.0 - trust.value))
