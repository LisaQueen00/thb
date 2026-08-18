from thb_input.extract.acceptance import ACCEPTANCE_CASES


def test_acceptance_dataset_covers_planned_cases() -> None:
    assert len(ACCEPTANCE_CASES) == 13
    assert len({case.name for case in ACCEPTANCE_CASES}) == 13
    assert {"10_healthy_communication", "13_anti_overanalysis"} <= {
        case.name for case in ACCEPTANCE_CASES
    }


def test_acceptance_expectations_do_not_contradict() -> None:
    assert all(
        not (case.expected_non_empty & case.expected_empty)
        for case in ACCEPTANCE_CASES
    )
