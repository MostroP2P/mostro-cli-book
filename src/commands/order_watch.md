# order watch

| | |
| --- | --- |
| `command` | `order.watch` |
| Kind | Private live read: the node's messages about one order and its peer chat |
| Who | Either party of an order in the local store |
| Needs | `MOSTRO_PUBKEY`, `RELAYS`, identity (never created), the order's local row |
| Publishes | Nothing |
| Local write | May save the counterparty's key in the order's row, as [`order chat`](order_chat.md) does; not reported |
| Statuses | `ok`, `error` |
| Schemas | `schemas/order.watch.input.json`, `schemas/order.watch.output.json` |

Follows an order you hold until its trade ends: the node's messages to the order's trade key
and, once the counterparty is known, the order's peer chat. In JSON each call returns one
document as soon as there is something new, with a cursor, so a program loops watch, act,
watch instead of polling [`message list`](message_list.md) and [`order chat`](order_chat.md).
In human mode it streams until the trade ends.

After 0.17.0, not yet released.

## Invocation

```text
mostro-cli --output json order watch --order UUID [--since MINUTES | --after CURSOR] [--timeout SECONDS]
mostro-cli order watch --order UUID [--since MINUTES | --after CURSOR] [--timeout SECONDS]
```

## Input

| Option | Required | Rule |
| --- | --- | --- |
| `--order` | yes | UUID of an order in the local store |
| `--since` | no | How far back to replay first, in minutes, 1..10080. Default 30 |
| `--after` | no | `data.cursor` of an earlier JSON call, verbatim. Conflicts with `--since` |
| `--timeout` | no | Seconds, 1..86400, counted from the end of the first replay. **JSON default 30**; human mode has no deadline without it |

Any invalid value, a malformed cursor, or `--after` with `--since` is `invalid_arguments`
(exit 2) before configuration, store or relays are read, and is never echoed.

## Behavior

**Replay, then live.** The window (`--since`, or the cursor's time) is replayed first, then
new records arrive live. The opening replay is strict, as the reads are: every relay must
connect within 10 s and finish its replay within 15 s. After that a relay that drops
reconnects on its own (every 10 s) and replays the window; no relay failure ends a live
watch. Each record is returned once: node messages by `event_id`, chat messages by
`message_id`, across relays, resends and, with the cursor, calls. After 10,000 records in
one run the watch ends with `read_limit_exceeded`.

**Counterparty.** Found as [`order chat`](order_chat.md) finds it (the row, else the node's
lock-time messages, then cached in the row). When it is not known yet the watch starts
without the chat (`counterparty_pubkey` is null), and the first new node message that names
it brings the chat in, with its replay. There is no `counterparty_unknown` here.

**One document per JSON call.** It returns at the first new records after the replays, or an
empty success at the deadline. **An empty result means nothing was observed** (relays may
have been down), not that nothing happened. A killed or timed-out call prints nothing and is
safe to repeat with the same cursor.

**The cursor.** Opaque: pass it back with `--after` exactly as received. It covers accepted
records only, by their envelope time, kept 60 s behind the newest (the chat clock skew),
with the ids already seen at or after that time (at most 200). Documented limit: a record
that reaches the relays after records stamped more than 60 s later is never returned by a
later call, nor is one inside a range the cursor raised past when more than 200 records fell
within it; when more than 200 records fall within the last minute, a later call returns some
of them again. Deduplicate by `event_id` and `message_id`.

**End.** `ended` is true when a returned node message about the order carries
`purchase-completed`, `hold-invoice-payment-settled`, `rate`, `canceled`,
`cooperative-cancel-accepted` or `admin-canceled`. `admin-settled` ends it only for the
seller (the order's row says which side you are); the buyer's payout follows and can still
fail and ask for a new invoice. Stop watching at `ended: true`. After `purchase-completed`
(buyer) or `hold-invoice-payment-settled` (seller) the node sends `rate` right away, so the
update that holds the end waits for it (up to 10 s, never past `--timeout`) and carries it,
listed after the end even when both carry the same second, with `next_step` `rate`: run
[`order rate`](order_rate.md). Without it the trade still ends; rate anyway. `bond-slashed`
and `add-bond-invoice` may follow an end: read them with
[`message list --order`](message_list.md).
Some watches never end on their own: an untaken order that expires (the node sends the maker
nothing) and a trade that ended before the window. Check [`order info`](order_info.md).

**Not used:** `--pow`, `--transport` and `--reply-timeout`: nothing goes to the node. An
invalid `POW` or `TRANSPORT` in the environment is ignored, but a value the argument parser
rejects on the command line (`--pow abc`, `--transport bogus`, an out-of-range
`--reply-timeout`) is still `invalid_arguments`. Timing: 10 s to
connect, 15 s for the replay, 15 s more when the counterparty is learned (up to 26 s first
when it must be looked up), then live until a record, the end or `--timeout` (an update that ends a completed trade waits
up to 10 s more for its `rate`, never past `--timeout`), then 1 s of cleanup. A JSON call
takes at most `--timeout` + 67 s; allow `--timeout` + 70 s (100 s with the default).

**Human output.** "👀 Watching order <id>", the window start and the counterparty (or "not
known yet; the chat is followed once the escrow is locked"); "📭 Nothing yet; waiting for the
node or the counterparty..." when the replay is empty; then each update: a node message as
`message list` shows it, with its next step, under "📨 From Mostro:", and a chat message as
`order chat` shows it, escaped, under "💬 Chat:". A line follows when the counterparty is
learned and one when older messages may be missing. Each update is written whole and
flushed. The last line is "🏁 The trade ended: <action>" (the end, such as
`purchase-completed`, not the `rate` printed before it with its "👉 Next:" line), or at
`--timeout` "⏰ Stopped at the watch deadline; the trade has not ended."; both exit 0. Ctrl-C stops it, with no exit status
promised. A value the argument parser rejects gets the parser's own message; other errors
are one `error: <fixed message>` line on stderr (exit 1, 2 for arguments). A stdout that
cannot be written stops the watch with `error: the watch could not be written` (exit 1).
The warnings are not printed. `--verbose` adds `verbose: order.watch <ok|code>` on stderr.

## Success data: `WatchData`

| Field | Type | Meaning |
| --- | --- | --- |
| `order_id` | uuid | The order |
| `counterparty_pubkey` | hex64 or null | The counterparty's trade key; null while the chat is not followed |
| `messages` | array of [`MessageRecord`](message_list.md#messagerecord) | The node's new messages about the order, oldest first, with `next_step` |
| `chat` | array of [`ChatRecord`](order_chat.md#chatrecord) | The new chat messages, oldest first, each once by `message_id` |
| `ended` | boolean | One of the messages ended the trade (above) |
| `truncated` | boolean | A relay's replay reached its limit of 50, so older records may be missing |
| `cursor` | string | Pass it back verbatim with `--after` to get only newer records |

At the deadline both lists are empty, `ended` is false and the cursor is carried forward.
`meta.snapshot` is always null.

## Outcomes

| Case | status | code | Stages |
| --- | --- | --- | --- |
| New records, or empty at the deadline | `ok` | | not_applicable / not_applicable / not_applicable |
| Bad option or cursor | `error` | `invalid_arguments` (exit 2) | not_applicable / not_applicable / not_applicable |
| Configuration, identity, store, not in store, failed opening replay, too many records | `error` | its code | not_applicable / not_applicable / not_applicable |

It is a read: never `uncertain`, always safe to repeat.

## Errors

`invalid_arguments`, `configuration_missing`, `configuration_invalid`, `identity_missing`,
`identity_unreadable`, `store_unreadable`, `order_unknown`, `relay_connection_failed`,
`relay_read_failed`, `read_timeout`, `read_limit_exceeded`, `internal_error`. Never
`counterparty_unknown`, `request_rejected` or a node code: nothing is sent.

## Warnings

`invalid_event_timestamp`, `cleanup_incomplete`.

## Examples

{{#include ../../generated/order_watch.md}}

## Next

Act on the newest `next_step` (see the [decision table](../wrapper/decision_table.md)), then
watch again with `--after <cursor>`. At `ended: true`, rate with
[`order rate`](order_rate.md): the `rate` record of a completed trade asks it with
`next_step` `rate`.
