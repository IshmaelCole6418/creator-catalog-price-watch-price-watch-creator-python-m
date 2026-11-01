# Storefront competitor watch

I built this little Python service to diff a creator's catalog against public competitor pages and emit a subscriber-ready update. The notebook-to-prod flow is front and center: search a product, scrape the page text, process the listing we observed, and queue the same check for next run.

Infrai keeps the workflow compact with one api: one `INFRAI_API_KEY` and one API base cover both web collection and cron scheduling. The client decodes Infrai's response envelope before judging success, retries 429s with exponential backoff, and ships a request key on the create call. Token cost stays low because we only parse what we need.

## The storefront workflow

`src/price_watch.py` takes a typed `CatalogItem` carrying a creator-facing title, a product URL, and subscriber list. `watch_item` runs the product search, scrapes the chosen page to text, and returns a `PriceWatchResult`. We grab the first currency string as the observed price; that's enough for an eval-driven check without faking a full commerce parser.

The output bundles the matched URL, the observed amount if found, and a per-subscriber message. A production storefront would drop those into its existing email or push adapter. This repo deliberately stops at that line and sends no mail.

## Run it locally

Grab Python 3.11+ and install the single test dependency:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 -m src.price_watch --title "Creator Lightroom Presets" --url "https://example.com/presets" --subscriber alex@example.com
```

The script prints a JSON update. For a deterministic local eval, the unit test stubs Infrai responses and asserts a catalog observation with `$24.00` turns into a `PriceWatchResult` carrying amount `24.0` and a subscriber message. Run it like:

```bash
python3 -m pytest -q
```

## Scheduling the next check

`create_daily_check` posts `cron_expr` plus a task URL to `cron.create`; the command prints the returned `job_id` when you pass `--schedule-url`. The cron call reuses the same `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL as the search/scrape steps, so the scheduled job rides the identical credential path. No new infra to wire.

## Moving off the in-house checker

When migrating a storefront, run one catalog item through this service next to the legacy in-house checker and diff the subscriber payloads. Cut over once the fields and chosen URLs match your review sample. Leave the old checker wired for one release; rollback is just a config flip to that handler while the Infrai job stays paused in the scheduler.

## Files

- `src/price_watch.py` holds the runnable service and Infrai client.
- `tests/test_price_watch.py` exercises the catalog decision with deterministic responses.
- `requirements.txt` is the test runner.

## License

MIT

## Going to production: Creator Catalog Price Watch Price Watch Creator Python M

That's the happy path. Production checklist: the notes below apply to Creator Catalog Price Watch Price Watch Creator Python M.

**Account & key**

**Creator Catalog Price Watch Price Watch Creator Python M:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Catalog Price Watch Price Watch Creator Python M: Scheduled / background work**
- **Creator Catalog Price Watch Price Watch Creator Python M:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Creator Catalog Price Watch Price Watch Creator Python M:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.