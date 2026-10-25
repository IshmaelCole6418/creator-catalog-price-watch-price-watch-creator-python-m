from src.price_watch import CatalogItem, InfraiClient, watch_item


class FakeClient(InfraiClient):
    def __init__(self) -> None:
        super().__init__("test-key")

    def search(self, query: str) -> dict:
        assert query == "Creator Lightroom Presets"
        return {"results": [{"url": "https://seller.example/presets"}]}

    def scrape(self, url: str) -> dict:
        assert url == "https://seller.example/presets"
        return {"text": "Creator Lightroom Presets - $24.00"}


def test_catalog_observation_becomes_subscriber_update() -> None:
    item = CatalogItem("Creator Lightroom Presets", "https://example.com/presets", ["alex@example.com"])
    result = watch_item(FakeClient(), item)
    assert result.observed_amount == 24.0
    assert result.matched_url == "https://seller.example/presets"
    assert result.subscriber_updates == ["alex@example.com - Creator Lightroom Presets: observed $24.00"]
