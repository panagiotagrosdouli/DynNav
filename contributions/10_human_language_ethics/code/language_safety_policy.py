"""
Language-Driven Safety Policy
-----------------------------
Maps natural language messages (English + Greek) into
risk and uncertainty scaling factors for navigation.

Implementation:
  - rule-based keyword extraction (EN + EL)
  - multiplicative scaling of risk / uncertainty
  - conservative bounding
  - human-readable explanations
"""

from dataclasses import dataclass
import math
from typing import Dict, List


@dataclass
class LanguageSafetyConfig:
    base_risk: float = 1.0
    base_uncertainty: float = 1.0
    max_risk_scale: float = 3.0
    max_uncertainty_scale: float = 2.5

    def __post_init__(self) -> None:
        values = (self.base_risk, self.base_uncertainty,
                  self.max_risk_scale, self.max_uncertainty_scale)
        if not all(math.isfinite(value) and value > 0 for value in values):
            raise ValueError("language safety scales must be finite and positive")
        if self.max_risk_scale < self.base_risk or self.max_uncertainty_scale < self.base_uncertainty:
            raise ValueError("maximum scales must not be below their base scales")


@dataclass
class LanguageSafetyDecision:
    risk_scale: float
    uncertainty_scale: float
    factors: List[str]
    explanation: str

    def to_dict(self) -> Dict:
        return {
            "risk_scale": self.risk_scale,
            "uncertainty_scale": self.uncertainty_scale,
            "factors": self.factors,
            "explanation": self.explanation,
        }


class LanguageSafetyPolicy:
    """
    Bilingual (EN + Greek) rule-based language safety policy.
    """

    def __init__(self, config: LanguageSafetyConfig | None = None):
        self.config = config or LanguageSafetyConfig()
        self._build_keyword_map()

    def _build_keyword_map(self) -> None:
        """
        Build internal keyword rules.

        Each rule:
            (keywords, risk_multiplier, uncertainty_multiplier, description)
        """
        self._rules: List[tuple[list[str], float, float, str]] = [
            # Explicitly unsafe language must not be mistaken for neutral text.
            (["not safe", "unsafe", "dangerous", "not secure", "μη ασφαλές", "μη ασφαλες"],
             2.0, 1.5, "explicitly unsafe condition"),
            # Crowding / many people
            (
                [
                    "crowd",
                    "crowded",
                    "many people",
                    "a lot of people",
                    "πολύς κόσμος",
                    "πολυς κοσμος",
                    "κόσμος",
                    "κοσμος",
                ],
                1.6,
                1.1,
                "crowding / many people",
            ),
            # Slippery floor
            (
                [
                    "slippery",
                    "wet floor",
                    "γλιστερός",
                    "γλιστερος",
                    "γλιστράει",
                    "γλιστραει",
                    "βρεγμένο πάτωμα",
                    "βρεγμενο πατωμα",
                ],
                1.8,
                1.5,
                "slippery / wet floor",
            ),
            # Stairs / elevation
            (
                [
                    "stairs",
                    "steps",
                    "elevation",
                    "σκαλιά",
                    "σκαλια",
                    "σκάλες",
                    "σκαλες",
                ],
                1.5,
                1.1,
                "stairs / elevation changes",
            ),
            # Children present
            (
                [
                    "children",
                    "kids",
                    "παιδιά",
                    "παιδια",
                ],
                1.5,
                1.1,
                "children present",
            ),
            # Elderly present
            (
                [
                    "elderly",
                    "old people",
                    "ηλικιωμένοι",
                    "ηλικιωμενοι",
                ],
                1.7,
                1.1,
                "elderly people present",
            ),
            # Unseen / hidden hazard
            (
                [
                    "hidden",
                    "unseen",
                    "around the corner",
                    "you can't see",
                    "you cant see",
                    "δεν φαίνεται",
                    "δεν φαινεται",
                    "γωνία",
                    "γωνια",
                ],
                1.4,
                1.4,
                "unseen / hidden hazard",
            ),
        ]

        # Explicit neutral markers
        self._neutral_markers: List[str] = [
            "nothing special",
            "normal",
            "ισορροπημένος διάδρομος",
            "ισορροπημενος διαδρομος",
        ]

    def evaluate(self, message: str) -> LanguageSafetyDecision:
        """
        Analyze a natural language message and compute multiplicative
        scaling factors for risk and uncertainty.

        Parameters
        ----------
        message : str
            User message in English or Greek.

        Returns
        -------
        LanguageSafetyDecision
        """
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        text = message.lower().strip()

        # Neutral checks
        if text in self._neutral_markers:
            return LanguageSafetyDecision(
                risk_scale=self.config.base_risk,
                uncertainty_scale=self.config.base_uncertainty,
                factors=[],
                explanation="No language-driven adjustment (neutral message).",
            )

        risk = self.config.base_risk
        uncert = self.config.base_uncertainty
        activated_factors: List[str] = []

        for keywords, r_mult, u_mult, desc in self._rules:
            if any(k.lower() in text for k in keywords):
                activated_factors.append(desc)
                risk *= r_mult
                uncert *= u_mult

        # Conservative caps
        risk = min(risk, self.config.max_risk_scale)
        uncert = min(uncert, self.config.max_uncertainty_scale)

        if not activated_factors:
            explanation = (
                "No safety-related keywords detected; leaving risk and uncertainty unchanged."
            )
        else:
            bullet_list = "\n  - " + "\n  - ".join(activated_factors)
            explanation = "Language-driven factors:" + bullet_list

        return LanguageSafetyDecision(
            risk_scale=risk,
            uncertainty_scale=uncert,
            factors=activated_factors,
            explanation=explanation,
        )
