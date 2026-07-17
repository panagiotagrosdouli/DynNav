from dynnav.security.attack_graph import CampaignCorrelator, SecurityAlert


def alert(
    source_id: str,
    alert_type: str,
    timestamp: float,
    *,
    confidence: float = 0.8,
    severity: float = 0.7,
    evidence: tuple[str, ...] = (),
) -> SecurityAlert:
    return SecurityAlert(
        source_id=source_id,
        alert_type=alert_type,
        timestamp=timestamp,
        confidence=confidence,
        severity=severity,
        evidence=evidence,
    )


def test_correlates_temporally_adjacent_multi_stage_alerts() -> None:
    correlator = CampaignCorrelator(max_gap=5.0)
    campaigns = correlator.correlate(
        [
            alert("gnss", "spoofing", 10.0, evidence=("position_jump",)),
            alert("imu", "bias", 11.0, evidence=("position_jump",)),
            alert("localizer", "state_divergence", 12.0),
        ]
    )

    assert len(campaigns) == 1
    assert campaigns[0].sources == ("gnss", "imu", "localizer")
    assert campaigns[0].attack_types == ("bias", "spoofing", "state_divergence")
    assert len(campaigns[0].links) == 2
    assert "multi_stage_pattern" in campaigns[0].links[0].reasons
    assert 0.0 <= campaigns[0].score <= 1.0


def test_separates_alerts_outside_temporal_window() -> None:
    correlator = CampaignCorrelator(max_gap=2.0)
    campaigns = correlator.correlate(
        [alert("gnss", "spoofing", 1.0), alert("gnss", "spoofing", 8.0)]
    )

    assert len(campaigns) == 2
    assert all(len(campaign.alerts) == 1 for campaign in campaigns)


def test_order_is_deterministic_for_unsorted_input() -> None:
    correlator = CampaignCorrelator(max_gap=5.0)
    campaigns = correlator.correlate(
        [alert("camera", "tamper", 3.0), alert("camera", "tamper", 1.0)]
    )

    assert [item.timestamp for item in campaigns[0].alerts] == [1.0, 3.0]
    assert "same_source" in campaigns[0].links[0].reasons
    assert "same_attack_type" in campaigns[0].links[0].reasons


def test_rejects_invalid_configuration() -> None:
    try:
        CampaignCorrelator(max_gap=0.0)
    except ValueError as exc:
        assert "max_gap" in str(exc)
    else:
        raise AssertionError("expected ValueError")
