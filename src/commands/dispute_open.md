# dispute open

| | |
| --- | --- |
| `command` | `dispute.open` |
| Kind | Write |
| Who | The **buyer or the seller** of an `active` or `fiat-sent` order |
| Needs | `MOSTRO_PUBKEY`, `RELAYS`, identity, the order's local row, a writable store, `--yes` in JSON mode |
| Publishes | One `dispute` request signed with the order's trade key, no payload |
| Local write | Status → `dispute`; never spends a trade index |
| Statuses | `ok`, `error`, `uncertain` |
| Schemas | `schemas/dispute.open.input.json`, `schemas/dispute.open.output.json` |

Asks the node to open a dispute on a trade that went wrong: for example, the seller does not
release after the fiat was sent, or the buyer never sends the fiat. A solver then takes the
dispute; talking to the solver is human-only today (see [Human-only commands](legacy.md)).

## Invocation

```text
mostro-cli --output json dispute open --order UUID --yes
```

Replaces `dispute -o ...` (no alias).

## Input

| Option | Required | Rule |
| --- | --- | --- |
| `--order` | yes | UUID of an order in the local store |
| `--yes` | **yes in JSON** | An agent must have explicit user consent for this specific order |

## Behavior

Looks up the order's trade key in the local `orders` table (`order_unknown` if missing;
nothing sent), publishes `dispute` and waits for the reply to **that** request. The node
answers the initiator with `dispute-initiated-by-you` and the new dispute's id; the other
party is told with `dispute-initiated-by-peer`. The CLI then records the local status
`dispute`.

The node only accepts a dispute on an `active` or `fiat-sent` order, from its buyer or
seller; otherwise it refuses (`node_refused`, reasons such as `not_allowed_by_status` or
`invalid_pubkey`). A **second** dispute on the same order gets no answer at all, so it ends
as `uncertain` with `reply_timeout`. The CLI never retries.

## Success data: `DisputeOpenData`

| Field | Type | Meaning |
| --- | --- | --- |
| `node_pubkey` | hex64 | The node |
| `order_id` | uuid | The order |
| `dispute_id` | uuid | The dispute the node created |
| `trade_pubkey` | hex64 | The order's trade key |

## Outcomes

| Case | status | code | Stages |
| --- | --- | --- | --- |
| Dispute opened, row updated | `ok` | | published / accepted / applied |
| Dispute opened, row update failed | `ok` + `local_status_stale` | | published / accepted / failed |
| Not in store | `error` | `order_unknown` | not_attempted / unknown / not_attempted |
| Other local failure, no `--yes` in JSON | `error` | its code | not_attempted / unknown / not_attempted |
| Refused (wrong status, not a party...) | `error` | `node_refused` + `reason` | published / rejected / not_attempted |
| No reply (also a second dispute) | `uncertain` | `reply_timeout` | published / unknown / not_attempted |
| Unusable reply (including a `cant-do` naming another order or none) | `uncertain` | `reply_malformed` | published / unknown / not_attempted |
| Relay dropped the wait, proof of work | `uncertain` | `relay_read_failed`, `pow_required` | published / unknown / not_attempted |
| Ambiguous relays | `uncertain` | `request_rejected` | unknown / unknown / not_attempted |

After `uncertain`, **do not send it again blindly**: the node answers a repeated dispute
with silence, so a second try only times out again. Run `order info --order <id>`; status
`dispute` means it went through.

## Errors

`invalid_arguments`, `configuration_*`, `relay_connection_failed`, `relay_read_failed`,
`internal_error`, `identity_*`, `protocol_unsupported`, `pow_required`, `request_rejected`,
`node_refused`, `order_declined` (human prompt only), `store_unwritable`, `order_unknown`;
uncertain: `reply_timeout`, `reply_malformed`, `request_rejected`, `relay_read_failed`,
`pow_required`.

A store that cannot be read or written is `store_unwritable`, and nothing is sent.

## Warnings

`local_status_stale`, `invalid_event_timestamp`, `cleanup_incomplete`.

## Examples

{{#include ../../generated/dispute_open.md}}

## Next

Wait for the solver; watch [`message list`](message_list.md) and
[`order info`](order_info.md). The dispute conversation itself is human-only today
(`disputechat`).
