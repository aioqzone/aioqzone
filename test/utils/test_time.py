from time import sleep


def test_approx_ts():
    from aioqzone.utils.time import approx_ts

    assert approx_ts("前天11:11") + 86400 == approx_ts("昨天 11:11")
    assert approx_ts("昨天\t11:11") + 86400 == approx_ts("11:11")
    assert approx_ts("2022年1月1日11:11") < approx_ts("2022年01月27日")
    assert approx_ts("前天11:11") == (sleep(1) or approx_ts("前天11:11"))
    assert approx_ts("2022年1月1日") == (sleep(1) or approx_ts("2022年1月1日"))
