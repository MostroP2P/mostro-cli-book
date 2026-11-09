# order rate

| | |
| --- | --- |
| `command` | `order.rate` |
| Kind | Write (node only) |
| Who | Either party of a **finished** trade |
| Needs | `MOSTRO_PUBKEY`, `RELAYS`, identity, the order's local row, `--yes` in JSON mode |
| Publishes | One `rate-user` request with the rating, signed with the order's trade key |
| Local write | None; never spends a trade index |
| Statuses | `ok`, `error`, `uncertain` |
| Schemas | `schemas/order.rate.input.json`, `schemas/order.rate.output.json` |

Rates the counterparty of a finished trade from 1 to 5.

## Invocation

```text
mostro-cli --output json order rate --order UUID --rating 1-5 --yes
```

Replaces `rate -o ... -r ...` (no alias).

## Input

| Option | Required | Rule |
| --- | --- | --- |
| `--order` | yes | UUID of an order in the local store |
| `--rating` | yes | An integer from 1 to 5; anything else is `invalid_arguments` (exit 2) and nothing is sent |
| `--yes` | **yes in JSON** | |

## Behavior

Checks the rating, looks up the order's trade key in the local `orders` table
(`order_unknown` if missing; nothing sent), publishes `rate-user` and waits for the reply to
**that** request. The node acknowledges with `rate-received` carrying the rating; the CLI
checks that it is the rating it sent. Nothing is written locally (the store only has to be
readable).

The node asks for the rating with a `rate` message to both sides when the trade is over;
[`message list`](message_list.md) and [`order watch`](order_watch.md) report it with
`next_step` `rate` (after 0.17.0, not yet released; 0.17.0: `null`).

The node accepts a rating once the order is `success`, or `settled-hold-invoice` when the
seller rates; otherwise it refuses (`node_refused`, reason `invalid_order_status`). Some
cases get **no answer** at all: a side that already rated, a counterparty in full-privacy
mode, a sender who is neither party. They end as `uncertain` with `reply_timeout`. The
CLI never retries.

## Success data: `RateData`

| Field | Type | Meaning |
| --- | --- | --- |
| `node_pubkey` | hex64 | The node |
| `order_id` | uuid | The order |
| `rating` | integer | The rating the node acknowledged, 1 to 5 (a JSON number, not a string) |
| `trade_pubkey` | hex64 | The order's trade key |

## Outcomes

| Case | status | code | Stages |
| --- | --- | --- | --- |
| Rating received | `ok` | | published / accepted / not_attempted |
| Rating outside 1-5, no `--yes` in JSON | `error` | `invalid_arguments` | not_attempted / unknown / not_attempted |
| Not in store | `error` | `order_unknown` | not_attempted / unknown / not_attempted |
| Other local failure | `error` | its code | not_attempted / unknown / not_attempted |
| Refused (trade not finished...) | `error` | `node_refused` + `reason` | published / rejected / not_attempted |
| No reply (already rated, full-privacy counterparty) | `uncertain` | `reply_timeout` | published / unknown / not_attempted |
| Unusable reply (another rating, another order, a `cant-do` naming another order or none) | `uncertain` | `reply_malformed` | published / unknown / not_attempted |
| Relay dropped the wait, proof of work | `uncertain` | `relay_read_failed`, `pow_required` | published / unknown / not_attempted |
| Ambiguous relays | `uncertain` | `request_rejected` | unknown / unknown / not_attempted |

After `uncertain`, **do not send the rating again**: the node may have recorded it, and it
answers a second one with silence. No command shows whether a rating was recorded.

## Errors

As [dispute open](dispute_open.md#errors).

## Warnings

`invalid_event_timestamp`, `cleanup_incomplete`. Never `local_status_stale`: nothing is
written locally.

## Examples

{{#include ../../generated/order_rate.md}}

## Next

Nothing: the trade is over.
