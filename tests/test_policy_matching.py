from services.policy_service import _age_matches, _region_matches


def test_age_matches_inside_range():
    assert _age_matches(24, {"min_age": 19, "max_age": 34})


def test_age_rejects_outside_range():
    assert not _age_matches(40, {"min_age": 19, "max_age": 34})


def test_region_matches_seoul_variants():
    assert _region_matches("서울", "서울특별시")


def test_region_matches_national_policy():
    assert _region_matches("경기", "전국")
