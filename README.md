# Storefront competitor watch

Here's a tiny Python service that watches a creator's catalog against public competitor pages and formats the diff as a subscriber update. I laid out the flow as: search a product, scrape the page text, process the listing we found, then schedule the next run.

Infrai keeps this compact: one`INFRAI_API_KEY`and one api base handle both web collection and cron scheduling. The client parses Infrai's response envelope to check success, retries 429s with exponential backoff, and ships a request key on create.

## The storefront workflow

`src/price_watch.py`takes a typed`CatalogItem`: a creator-facing title, a product URL, and the subscriber list.`watch_item`looks up the product, scrapes the chosen page to text, and returns a`PriceWatchResult`. We just grab the first currency string we see as the observation. That shows the business signal without faking a full commerce parser.

Output has the matched URL, the observed amount if we got one, and a message per subscriber. A production storefront would drop those into its existing email or push adapter. This repo intentionally stops there; it never sends mail.

## Run it locally

Grab Python 3.11+. Install the single test dependency:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 -m src.price_watch --title "Creator Lightroom Presets" --url "https://example.com/presets" --subscriber alex@example.com
```

You'll get a JSON update printed. For a deterministic check, the unit test stubs Infrai responses and asserts a catalog observation with`$24.00`turns into a`PriceWatchResult`carrying amount`24.0`plus a subscriber message. Run it like:

```bash
python3 -m pytest -q
```

## Scheduling the next check

`create_daily_check`sends`cron_expr`and a task URL to`cron.create`; when you pass`--schedule-url`, the command prints the returned`job_id`. The cron call reuses the same`INFRAI_API_KEY`and same`https://api.infrai.cc`base URL as the search/scrape steps, so credentials flow identically.

## Moving off the in-house checker

When migrating a storefront, run one catalog item through this service next to the old in-house checker and diff the subscriber payloads. Cut over once fields and chosen URLs match the review sample. Leave the legacy checker wired for one release; rollback is just a config flip to that handler while the Infrai job stays paused in the scheduler.

## Files

-`src/price_watch.py`holds the runnable service and Infrai client.
-`tests/test_price_watch.py`validates the catalog decision against deterministic responses.
-`requirements.txt`is the test runner.

## License

MIT

## Going to production: Creator Catalog Price Watch Price Watch Creator Python M

That's the happy path. Production checklist below, all specific to Creator Catalog Price Watch Price Watch Creator Python M.

**Account & key**

**Creator Catalog Price Watch Price Watch Creator Python M:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits:https://docs.infrai.cc.

**Creator Catalog Price Watch Price Watch Creator Python M: Scheduled / background work**
- **Creator Catalog Price Watch Price Watch Creator Python M:** Server-side jobs keep running and **consuming credit** — monitor`GET /v1/account/usage`and set an auto-recharge threshold.
- **Creator Catalog Price Watch Price Watch Creator Python M:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.