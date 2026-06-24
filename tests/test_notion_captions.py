from adbot.notion_captions import content_id_from_title, fetch_captions


def test_content_id_from_title_parses_video_rows():
    assert content_id_from_title("Video 1：最痛苦的是什么") == "video_1"
    assert content_id_from_title("Video 11：你不敢下单") == "video_11"
    assert content_id_from_title("video2 - 采访角度") == "video_2"
    # Non-video rows (collection pages, hooks, scripts) are not buildable video ids.
    assert content_id_from_title("JUNE 2026 Facebook 广告文案合集") is None
    assert content_id_from_title("Hook 1：越懒越赚钱") is None
    assert content_id_from_title("") is None


def _page(title, hook, caption=None):
    props = {
        "Title": {"type": "title", "title": [{"plain_text": title}]},
        "Hook": {"type": "rich_text", "rich_text": [{"plain_text": hook}]},
        "Type": {"type": "select", "select": {"name": "Video"}},
    }
    if caption is not None:
        props["Caption"] = {"type": "rich_text", "rich_text": [{"plain_text": caption}]}
    return {"id": f"page_{title}", "properties": props}


class FakeNotion:
    """Stands in for NotionClient: canned rows + per-page body blocks."""

    def __init__(self, pages, bodies):
        self._pages = pages
        self._bodies = bodies  # page_id -> list of paragraph strings

    def query_database(self, database_id):
        return self._pages

    def get_block_children(self, block_id):
        return [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": line}]}}
                for line in self._bodies.get(block_id, [])]


def test_fetch_captions_maps_video_rows_and_skips_others():
    pages = [
        # Caption property present -> used verbatim (blank lines preserved).
        _page("Video 1：最痛苦的是什么", "🔴 看到 signal 不敢进？问题不是胆量",
              caption="做过交易的你，有没有试过——\n\n👇 点击下方链接，立即免费报名"),
        # No Caption property -> caption is empty, so the build will fill it from the snapshot.
        _page("Video 8：你的钱放 FD，是在等死", "🔴 存款放 FD 每年缩水"),
        _page("JUNE 2026 广告文案合集", ""),  # collection page -> skipped
    ]
    caps = fetch_captions(FakeNotion(pages, {}), "db_id")

    assert set(caps) == {"video_1", "video_8"}  # the collection page was skipped
    assert caps["video_1"]["name"] == "Video 1：最痛苦的是什么"
    assert caps["video_1"]["headline"] == "🔴 看到 signal 不敢进？问题不是胆量"
    # Caption property is faithful — the blank line between paragraphs survives.
    assert caps["video_1"]["caption"] == "做过交易的你，有没有试过——\n\n👇 点击下方链接，立即免费报名"
    # video_8 has Title + Hook but no Caption -> empty (snapshot fills it in the build merge).
    assert caps["video_8"]["caption"] == ""
    assert caps["video_8"]["name"] == "Video 8：你的钱放 FD，是在等死"


def test_pull_notion_captions_is_inert_without_config():
    """The build's Notion step must no-op (not raise / not hit network) when unconfigured."""
    from adbot.commands.build import _pull_notion_captions
    from adbot.logging import get_logger
    from adbot.settings import NotionCfg, Secrets, Settings

    class U:
        def __init__(self, cid):
            self.content_id = cid

    units = [U("video_1")]
    log = get_logger()

    disabled = Settings()  # notion disabled by default
    assert _pull_notion_captions(disabled, units, log) == {}

    no_token = Settings(notion=NotionCfg(enabled=True, database_id="db"), secrets=Secrets())
    assert _pull_notion_captions(no_token, units, log) == {}
