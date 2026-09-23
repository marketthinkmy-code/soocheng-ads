"""The permanent ban gate (owner 2026-09-23, after the second account ban)."""
from adbot.compliance import banned_reason, filter_banned, is_banned, norm_key

BANNED = ["trading 早就不是这样了", "做么你 trading 不用看盘", "freestyle 1",
          "office 突访", "炒过那么多", "你敢吗", "分钟赚"]


def test_one_master_matches_all_its_ad_name_variants():
    # the same footage ships under 拼接：/ HOOK：/ 重拍：/ 🌟 variants and mixed case
    for name in ("拼接：Video 5：Trading 早就不是这样了！",
                 "video 5：trading 早就不是这样了！",
                 "🌟 video 5：Trading 早就不是这样了！"):
        assert is_banned(name, BANNED), name
    for name in ("HOOK：Video 8：做么你 Trading 不用看盘的？",
                 "video 8：做么你 trading 不用看盘的？"):
        assert is_banned(name, BANNED), name


def test_whitespace_and_star_are_ignored():
    # Meta names vary between「1 分钟赚 300」and「1分钟赚300」for one video
    assert is_banned("video 1: 1 分钟赚 300", BANNED)
    assert is_banned("video1:1分钟赚300", BANNED)
    assert is_banned("🌟 freestyle 1", BANNED)
    assert norm_key("🌟 freestyle 1") == "freestyle1"


def test_clean_winners_are_not_caught():
    for name in ("HOOK：Video 12：不选 forex 不选黄金", "freestyle: korea",
                 "重拍：Video 6：我跟你讲！", "拼接：Video 1：用我的方法",
                 "video 2: 我只有一个目的", "HOOK：Video 5：盖电脑，喂！"):
        assert not is_banned(name, BANNED), name


def test_empty_inputs_are_safe():
    assert not is_banned("", BANNED)
    assert not is_banned("anything", [])
    assert banned_reason("anything", None) is None


def test_banned_reason_and_filter_report_the_matched_entry():
    assert banned_reason("🌟 video 2：你敢吗？", BANNED) == "你敢吗"
    hits = filter_banned(["freestyle: korea", "🌟 freestyle 1", "video 11：office 突访"], BANNED)
    assert hits == [("🌟 freestyle 1", "freestyle 1"), ("video 11：office 突访", "office 突访")]
