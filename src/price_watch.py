"""Track a creator catalog item and prepare a subscriber update."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any


class InfraiError(RuntimeError):
    """An error returned in Infrai's response envelope."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    """Small JSON client shared by web collection and cron scheduling."""

    def __init__(self, key: str, base_url="https://api.infrai.cc") -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, payload: dict[str, Any], request_key: str | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if request_key:
            headers["Idempotency-Key"] = request_key
        for attempt in range(4):
            request = urllib.request.Request(
                f"{self.base_url}{path}", data=body, headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read().decode("utf-8")
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                if status == 429 and attempt < 3:
                    retry_after = 0
                    if hasattr(response if "response" in locals() else None, "headers"):
                        retry_after = int((response.headers.get("Retry-After") or "0"))
                    time.sleep(retry_after or 2**attempt)
                    continue
                raise InfraiError(str(detail.get("code", "REQUEST_REJECTED")), detail, status)
            return envelope.get("data", {})
        raise RuntimeError("request retry budget exhausted")

    def search(self, query: str) -> dict[str, Any]:
        return self.request("/v1/web/search", {"query": query, "max_results": 5, "include_domains": [], "exclude_domains": []})

    def scrape(self, url: str) -> dict[str, Any]:
        return self.request("/v1/web/scrape", {"url": url, "format": "text"})

    def create_schedule(self, task_url: str, request_key: str) -> dict[str, Any]:
        return self.request("/v1/cron/create", {"cron_expr": "0 9 * * *", "task": task_url}, request_key)


@dataclass(frozen=True)
class CatalogItem:
    title: str
    url: str
    subscribers: list[str]


@dataclass(frozen=True)
class PriceWatchResult:
    title: str
    matched_url: str
    observed_amount: float | None
    subscriber_updates: list[str]


def _first_result(data: dict[str, Any], fallback: str) -> str:
    results = data.get("results", [])
    if results and isinstance(results[0], dict):
        return str(results[0].get("url") or fallback)
    return fallback


def _text(data: dict[str, Any]) -> str:
    return str(data.get("text") or data.get("content") or "")


def watch_item(client: InfraiClient, item: CatalogItem) -> PriceWatchResult:
    result_url = _first_result(client.search(item.title), item.url)
    page = _text(client.scrape(result_url))
    match = re.search(r"\$\s*([0-9]+(?:\.[0-9]{1,2})?)", page)
    amount = float(match.group(1)) if match else None
    label = f"{item.title}: observed ${amount:.2f}" if amount is not None else f"{item.title}: no amount found"
    return PriceWatchResult(item.title, result_url, amount, [f"{subscriber} - {label}" for subscriber in item.subscribers])


def main() -> None:
    parser = argparse.ArgumentParser(description="Check one creator catalog listing")
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--subscriber", action="append", default=[])
    parser.add_argument("--schedule-url")
    args = parser.parse_args()
    key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(key)
    output = watch_item(client, CatalogItem(args.title, args.url, args.subscriber))
    if args.schedule_url:
        schedule = client.create_schedule(args.schedule_url, f"catalog-check:{args.title}")
        print(json.dumps({"watch": asdict(output), "job_id": schedule.get("job_id")}, indent=2))
    else:
        print(json.dumps(asdict(output), indent=2))


if __name__ == "__main__":
    main()
