"""Report rendering + the account scoping that keeps MY and SG sales apart.

daily_report.py is a script, not a package module, so it is loaded by path.
"""
import datetime as dt
import importlib.util
import pathlib

from adbot import cpa

_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "daily_report.py"
_spec = importlib.util.spec_from_file_location("daily_report", _PATH)
daily_report = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(daily_report)

TODAY = dt.date(2026, 8, 6)
YESTERDAY = dt.date(2026, 8, 5)
NOW = dt.datetime(2026, 8, 6, 22, 9)

# One shared Paid Student List: MY rows plus an SG row (utm_campaign prefixed "[sg]").
SALES = [
    cpa.Sale(YESTERDAY, "stockbloom | travel | 1-1-3", "as", "video 2：你敢吗？", 2399.0),
    cpa.Sale(YESTERDAY, "stockbloom | travel | 1-1-3", "as", "video 2：你敢吗？", 2399.0),
    cpa.Sale(YESTERDAY, "[sg] stockbloom | broad | 1-1-3 a", "as", "freestyle: korea", 2399.0),
    cpa.Sale(TODAY, "stockbloom | luxury goods | 1-1-3", "as", "video 12", 1999.0),
    cpa.Sale(dt.date(2026, 7, 1), "stockbloom | travel | 1-1-3", "as", "old", 2399.0),
]
MY_SPEND = {"stockbloom | travel | 1-1-3": ("STOCKBLOOM | TRAVEL | 1-1-3", 3000.0),
            "stockbloom | luxury goods | 1-1-3": ("STOCKBLOOM | LUXURY GOODS | 1-1-3", 1000.0)}
SG_SPEND = {"[sg] stockbloom | broad | 1-1-3 a": ("[SG] STOCKBLOOM | BROAD | 1-1-3 A", 5000.0)}


def test_new_sales_map_scopes_to_this_account():
    """The SG sale must not show up in the MY report, and vice versa — but is still counted."""
    (yday, y_rows, y_other), (today, t_rows, t_other) = daily_report.new_sales_map(
        SALES, MY_SPEND, TODAY)
    assert (yday, today) == (YESTERDAY, TODAY)
    assert y_rows == [("STOCKBLOOM | TRAVEL | 1-1-3", "video 2：你敢吗？", 2, 4798.0)]
    assert (y_other, t_other) == (1, 0)          # the SG sale, flagged not dropped
    assert t_rows == [("STOCKBLOOM | LUXURY GOODS | 1-1-3", "video 12", 1, 1999.0)]

    (_, sg_yday, sg_other), (_, sg_today, _) = daily_report.new_sales_map(
        SALES, SG_SPEND, TODAY)
    assert sg_yday == [("[SG] STOCKBLOOM | BROAD | 1-1-3 A", "freestyle: korea", 1, 2399.0)]
    assert sg_other == 2                          # the two MY sales
    assert sg_today == []


def test_new_sales_section_states_the_answer():
    new_sales = daily_report.new_sales_map(SALES, MY_SPEND, TODAY)
    md = daily_report.render_report(NOW, dt.date(2026, 8, 6), [], [], 50.0,
                                    account_label="MY", new_sales=new_sales)
    assert "# 📊 Daily Ads Report · MY" in md
    assert "MY account" in md
    assert "**Yesterday (Wed 05 Aug)** — **2 sales** · RM4,798: _(+1 on the other account)_" in md
    assert "video 2：你敢吗？ — 2× · RM4,798" in md
    assert "**Today so far (Thu 06 Aug)** — **1 sale** · RM1,999:" in md


def test_new_sales_section_says_no_sale_explicitly():
    """A quiet day must read as 'no new sale', never as a missing section."""
    new_sales = daily_report.new_sales_map([], MY_SPEND, TODAY)
    md = daily_report.render_report(NOW, dt.date(2026, 8, 6), [], [], 50.0,
                                    account_label="SG", new_sales=new_sales)
    assert "**Yesterday (Wed 05 Aug)** — no new sale." in md
    assert "**Today so far (Thu 06 Aug)** — no new sale." in md


def test_report_without_cpa_addon_omits_new_sales_section():
    md = daily_report.render_report(NOW, dt.date(2026, 8, 6), [], [], 50.0)
    assert "New sales" not in md
    assert "whole account (MTC + STOCKBLOOM)" in md  # unlabelled config keeps the old header
    assert "(no campaign spent this ad-week yet)" in md


def test_cpa_money_map_excludes_the_other_account():
    """MY blended CPA must not be diluted by SG sales the MY account never paid for."""
    rows, blended = daily_report.cpa_money_map(SALES, MY_SPEND, TODAY)
    assert rows == [("STOCKBLOOM | TRAVEL | 1-1-3", 3000.0, 3, 1000.0),
                    ("STOCKBLOOM | LUXURY GOODS | 1-1-3", 1000.0, 1, 1000.0)]
    assert blended == 1000.0                      # 4000 spend / 4 MY sales — SG's row excluded

    sg_rows, sg_blended = daily_report.cpa_money_map(SALES, SG_SPEND, TODAY)
    assert sg_rows == [("[SG] STOCKBLOOM | BROAD | 1-1-3 A", 5000.0, 1, 5000.0)]
    assert sg_blended == 5000.0
