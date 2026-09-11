from app.game.votes import count_votes, tally


def test_da_so_tuong_doi_thang():
    assert tally({"a": "x", "b": "x", "c": "y"}) == "x"


def test_hoa_thi_khong_ai_chet():
    assert tally({"a": "x", "b": "y"}) is None


def test_khong_ai_vote_thi_none():
    assert tally({}) is None


def test_dem_phieu_tra_so_luong():
    assert count_votes({"a": "x", "b": "x", "c": "y"}) == {"x": 2, "y": 1}
