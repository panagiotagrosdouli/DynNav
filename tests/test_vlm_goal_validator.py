from dynnav.researcher.vlm_goal_validator import GoalDecision, validate_vlm_goal


def test_accepts_in_frame_nearby_goal_with_allowed_region() -> None:
    report = validate_vlm_goal(
        description="go through the corridor",
        region_label="corridor",
        confidence=0.86,
        pixel_hint=(320, 240),
        image_shape=(480, 640),
        metric_waypoint=(3.0, 0.2),
    )
    assert report.decision is GoalDecision.ACCEPT


def test_sends_low_confidence_goal_for_human_confirmation() -> None:
    report = validate_vlm_goal(
        description="maybe go left",
        region_label="doorway",
        confidence=0.43,
        pixel_hint=(200, 220),
        image_shape=(480, 640),
        metric_waypoint=(2.0, 1.0),
    )
    assert report.decision is GoalDecision.ASK_HUMAN


def test_rejects_out_of_frame_pixel() -> None:
    report = validate_vlm_goal(
        description="go to open area",
        region_label="open_space",
        confidence=0.90,
        pixel_hint=(999, 240),
        image_shape=(480, 640),
        metric_waypoint=(2.0, 0.2),
    )
    assert report.decision is GoalDecision.REJECT
    assert not report.valid_pixel


def test_rejects_waypoint_beyond_maximum_distance() -> None:
    report = validate_vlm_goal(
        description="go to the exit",
        region_label="exit",
        confidence=0.92,
        pixel_hint=(300, 240),
        image_shape=(480, 640),
        metric_waypoint=(20.0, 0.0),
    )
    assert report.decision is GoalDecision.REJECT
    assert not report.valid_waypoint


def test_forbidden_semantics_cannot_be_accepted() -> None:
    report = validate_vlm_goal(
        description="enter the restricted private room",
        region_label="room",
        confidence=0.88,
        pixel_hint=(280, 210),
        image_shape=(480, 640),
        metric_waypoint=(2.5, -0.5),
    )
    assert report.decision is GoalDecision.ASK_HUMAN
    assert not report.valid_region
