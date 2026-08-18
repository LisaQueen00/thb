from thb_input.strategize.acceptance import ACCEPTANCE_CASES


def test_acceptance_dataset_covers_ten_planned_cases() -> None:
    assert len(ACCEPTANCE_CASES) == 10
    assert len({case.name for case in ACCEPTANCE_CASES}) == 10


def test_acceptance_strategy_expectations_do_not_conflict() -> None:
    assert all(case.required_types for case in ACCEPTANCE_CASES)
    assert all(
        not (case.required_types & case.forbidden_types) for case in ACCEPTANCE_CASES
    )


def test_acceptance_covers_goal_and_required_input_variants() -> None:
    assert any(case.explicit_goal for case in ACCEPTANCE_CASES)
    assert any(case.explicit_goal is None for case in ACCEPTANCE_CASES)
    assert any(case.requires_user_input for case in ACCEPTANCE_CASES)
