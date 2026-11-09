# message list

| | |
| --- | --- |
| `command` | `message.list` |
| Kind | Private read |
| Needs | `MOSTRO_PUBKEY`, `RELAYS`, an existing identity (read only) |
| Publishes | Nothing |
| Local write | None: a repeated call returns the same messages |
| Statuses | `ok`, `error` |
| Schemas | `schemas/message.list.input.json`, `schemas/message.list.output.json` |

Reads the messages the **node** sent to your trade keys: "a taker arrived, pay this hold
invoice", "send your invoice", "the buyer says fiat was sent", "your order was canceled"...
It is the **inbox** of a trade and the way a program learns what to do next.

## Invocation

```text
mostro-cli --output json message list [--since MINUTES] [--order UUID]
```

Replaces `getdm`.

## Input

| Option | Required | Rule |
| --- | --- | --- |
| `--since` | no | Window in minutes, 1..10080 (7 days). **Default 30** |
| `--order` | no | Read only the key stored with this order (`order_unknown` if not in the store) |

## Behavior

Reads the keys of trade indexes 1..last (at most the newest 200), or only the order's key
with `--order`. Returns only messages **authored by the configured node** and addressed to
those keys, decrypted and summarized, **oldest first**, at most 200. Peer chat and messages
from other authors are not included; the peer chat of an order is read with
[`order chat`](order_chat.md).

Poll it: there is no push. Typical intervals are 10 to 30 seconds during an active trade.
Deduplicate by `event_id`. To follow one order, with its chat, use
[`order watch`](order_watch.md): it returns as soon as there is something new.

**Human output.** One block per message. When a message asks you for something, its
"👉 Next:" line names the command with the record's order id filled in, for example
"send an invoice for the sats: `order add-invoice --order 00000000-0000-0000-0000-000000000001 --invoice <invoice>`"
(`<id>` only when the record names no order; after 0.17.0, not yet released: 0.17.0 prints
`<id>` in every case). A failed payout prints its own line ([payment_failed](#payment_failed)).
After 0.17.0, not yet released: `hold-invoice-payment-accepted` prints
"send the fiat, then: `order fiat-sent --order <order-id>`" and `rate` prints
"rate your counterparty: `order rate --order <order-id> --rating <1-5>`"; 0.17.0 prints no
"👉 Next:" line for either.

## Success data: `MessageListData`

| Field | Type | Meaning |
| --- | --- | --- |
| `node_pubkey` | hex64 | The node |
| `since_minutes` | decimal string | The window used |
| `messages` | array of `MessageRecord` | Oldest first |
| `truncated` | boolean | More than 200 records matched, or a relay hit its per-relay limit: narrow `--since` or use `--order` |
| `keys_read` | decimal string | Keys read |
| `keys_not_read` | decimal string | Keys beyond the newest 200 (see warning `trade_keys_limited`) |

### MessageRecord

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | hex64 | Nostr event id; unique per message, use it to deduplicate |
| `created_at` | rfc3339 or null | When the node sent it |
| `created_at_unix` | decimal string | Exact seconds |
| `order_id` | uuid or null | The order the message is about |
| `request_id` | decimal string or null | Correlation id of the request this answers, if any |
| `action` | string | Protocol action, kebab-case: `pay-invoice`, `add-invoice`, `fiat-sent-ok`, `canceled`... ([list](../reference/actions.md)) |
| `next_step` | enum or null | What the node asks you to do (below); null for informational messages |
| `trade_index` | decimal string or null | Index of the key it was addressed to; null when only known from an order row older than the newest 200 keys |
| `trade_pubkey` | hex64 | The key it was addressed to |
| `payload` | `MessagePayload` | Typed summary of the content (below) |

### next_step

| `next_step` | From action | Do |
| --- | --- | --- |
| `pay_bond_invoice` | `pay-bond-invoice` | Pay the invoice in the `payment_request` payload |
| `add_invoice` | `add-invoice`; `payment-failed` with `payment_attempts` `"0"` | [`order add-invoice`](order_add_invoice.md) |
| `pay_hold_invoice` | `pay-invoice` | Pay the hold invoice in the `payment_request` payload |
| `add_bond_invoice` | `add-bond-invoice` | [`bond add-invoice`](bond_add_invoice.md) |
| `fiat_sent` | `hold-invoice-payment-accepted` (to the buyer only, once the seller's hold invoice is paid) | Send the fiat, then [`order fiat-sent`](order_fiat_sent.md); only while `order info` says `active` |
| `rate` | `rate` (to both sides, right after `purchase-completed` for the buyer or `hold-invoice-payment-settled` for the seller) | [`order rate`](order_rate.md); once the order is `success` (a seller may rate from `settled-hold-invoice`) |

`fiat_sent` and `rate` come after 0.17.0 and are not yet released; 0.17.0 reports both messages
with `next_step: null`.

Every other action has `next_step: null`, and so has a `payment-failed` while the node still
retries.

A `next_step` is what the message asked **when the node sent it**; the record stays in later
listings within `--since`, after the trade has moved on. Before acting on one, check the
order's status with [`order info`](order_info.md), and act on each `event_id` once: an old
`fiat_sent` record still says `fiat_sent` after you ran `order fiat-sent`.

`next_step` is an open enum within version 1: a later executable may add values. Treat a value
you do not know as `null` (nothing you know how to do is asked). See
[Envelope](../envelope.md).

### MessagePayload

Discriminated by `kind`:

| `kind` | Fields | Carried by (typically) |
| --- | --- | --- |
| `none` | — | Status notifications (`canceled`, `waiting-seller-to-pay`...) |
| `order` | `order`: OrderRecord | `new-order`, `add-invoice`... |
| `payment_request` | `order`: OrderRecord or null; `invoice`: string; `amount`: decimal string or null | `pay-invoice`, `pay-bond-invoice` |
| `bond_payout_request` | `order`: OrderRecord; `slashed_at`: rfc3339 or null; `slashed_at_unix`: decimal string | `add-bond-invoice` |
| `cant_do` | `reason`: reason or null | `cant-do` |
| `peer` | `counterparty_pubkey`: string | `fiat-sent-ok` |
| `text` | `text`: string (≤ 4096 bytes, untrusted) | Text messages from the node |
| `amount` | `amount`: decimal string | Amount payloads |
| `payment_failed` | `payment_attempts`: decimal string; `payment_retries_interval`: decimal string | `payment-failed` (after 0.17.0, not yet released) |
| `other` | `variant`: string | Any other payload, by variant name only (e.g. `rating_user`). The name is informative, not a stable identifier |

The invoice in `payment_request` is meant for the caller (to pay it). Treat `text` and
`counterparty_pubkey` as untrusted data.

`kind` is an open enum within version 1: a later executable may add kinds, and may give a
payload it reported as `other` a kind of its own. Treat a payload of a `kind` you do not know as
opaque: read no field but `kind`.

#### payment_failed

The node could not pay the buyer's invoice. It sends `payment-failed` once per buyer invoice: on
the first failed payout to it, and again, with a new `event_id`, after a replacement invoice
from `order add-invoice` resets the count. It never updates the count in between.

| Field | Meaning |
| --- | --- |
| `payment_attempts` | How many more times the node will try to pay, as of this message (mostrod v0.20.2 sends its setting minus one, so `"2"` by default) |
| `payment_retries_interval` | Seconds between two attempts (approximate: the node skips retries while its Lightning node is unsynced) |

While attempts are left, `next_step` is `null`: the node retries on its own and sends
`add-invoice` (`next_step: add_invoice`) only if every attempt fails. At `payment_attempts`
`"0"` the node neither retries nor asks, and `next_step` is `add_invoice`: send a new invoice
with [`order add-invoice`](order_add_invoice.md). Human mode prints
"🔁 Payment failed: the node will retry the payment up to N more times, every M seconds", or
"🔁 Payment failed: the node will not retry the payment" followed by the add-invoice Next line.
mostro-cli 0.17.0 reports this payload as `{"kind": "other", "variant": "payment_failed"}`. The
retry behaviour is read from the mostrod v0.20.2 source, not observed on a node.

## Outcomes

| Case | status | code | Snapshot |
| --- | --- | --- | --- |
| Read (even empty) | `ok` | | present |
| Bad option (window out of range) | `error` | `invalid_arguments` (exit 2) | null |
| No identity, unreadable store, unknown `--order` | `error` | `identity_missing`, `identity_unreadable`, `store_unreadable`, `order_unknown` | null |
| Configuration, connection | `error` | `configuration_*`, `relay_connection_failed` | null |
| Read failed | `error` | `relay_read_failed`, `read_timeout`, `read_limit_exceeded` | present |

All stages are `not_applicable`.

## Errors

`invalid_arguments`, `configuration_missing`, `configuration_invalid`,
`relay_connection_failed`, `relay_read_failed`, `read_timeout`, `read_limit_exceeded`,
`internal_error`, `identity_missing`, `identity_unreadable`, `order_unknown`,
`store_unreadable`.

## Warnings

`trade_keys_limited`, `invalid_event_timestamp`, `cleanup_incomplete`.

## Examples

{{#include ../../generated/message_list.md}}

## Next

Drive a trade from the messages: [Trade flows](../flows/sell_maker.md).
