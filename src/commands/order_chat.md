# order chat

| | |
| --- | --- |
| `command` | `order.chat` |
| Kind | Private read; with `--message`, also one chat message to the counterparty |
| Who | Either party of an order in the local store, once the escrow is locked |
| Needs | `MOSTRO_PUBKEY` and `RELAYS` (each from its root option, its environment variable or the [config file](../getting_started.md#the-config-file)), identity, the order's local row; `--yes` with `--message` in JSON mode |
| Publishes | Nothing; with `--message`, one chat message to the relays: the message is signed with the order's trade key, inside a kind-14 envelope signed with a conversation key both parties derive from their trade keys. Never a request to the node |
| Local write | May save the counterparty's key in the order's row; not reported in the stages |
| Statuses | `ok`, `error`; `uncertain` only with `--message` |
| Schemas | `schemas/order.chat.input.json`, `schemas/order.chat.output.json` |

Reads the peer chat of an order you hold: what you and your counterparty wrote to each
other, for example to agree on the payment details. With `--message` it then sends one
message. You never pass the counterparty's key.

After 0.17.0, not yet released.

## Invocation

```text
mostro-cli --output json order chat --order UUID [--since MINUTES]
mostro-cli --output json order chat --order UUID [--since MINUTES] --message TEXT --yes
```

Replaces `getdmuser` and `dmtouser` for an order in the local store. Both stay, human-only,
as the fallback for `counterparty_unknown` (below).

## Input

| Option | Required | Rule |
| --- | --- | --- |
| `--order` | yes | UUID of an order in the local store |
| `--since` | no | Window in minutes, 1..10080 (7 days). **Default 10080** |
| `--message` | no | One message, trimmed, 1 to 4096 bytes; write `--message=TEXT` for a text that starts with `-` |
| `--yes` | **yes in JSON, with `--message`** | Without `--message` it does nothing |

Any invalid value, a second `--message`, or `--message` without `--yes` in JSON is
`invalid_arguments` (exit 2) before configuration, store or relays are read. The text is
never echoed, on stdout or stderr. The message text is on the command line, where other
local users can see it in the process list.

## Behavior

**Counterparty.** The order row's `counterparty_pubkey`, when it parses and is not your own
trade key, is used as it is, unchecked, with no relay contacted; the removed `getdm` may have
stored it, and nothing refreshes it. Otherwise the node's messages to the order's trade key
are read once, and only the newest `buyer-took-order` or `hold-invoice-payment-accepted`
naming both trade keys, or `fiat-sent-ok` with its peer, names it; the key is then saved in
the row (a failed save is not reported). Neither is `counterparty_unknown`: the counterparty
is known once the escrow is locked. A trade whose lock-time messages are gone (beyond the
newest 50 per relay, or expired after the node's `dm_days`) gets it too. Then `getdmuser -p`
and `dmtouser -p` ([human-only](legacy.md)), which also need the order's row, are the
fallback when you know the key.

**Read, then send.** One bounded read of both sides in the window, oldest first, at most 200,
opened only with your trade key and the counterparty's as writers. With `--message`, the
message is sent only after the read succeeded, so a failed read sends nothing. When no relay
confirms the message and one failed without a clear answer, the outcome is `uncertain`; the
CLI never resends it.

**Not used:** `--pow`, `--transport` and `--reply-timeout` (an out-of-range
`--reply-timeout` is still `invalid_arguments`). The message goes to relays, never to the
node: it mines no proof of work and waits for no reply, so relays that require proof of
work for chat messages refuse it (`request_rejected` when every relay does). The worst
case is 52 s for a read and 78 s with `--message`; allow 90 s.

**Human output.** "💬 Order Chat", the order and the counterparty, then "📭 No chat messages"
or one block per message: the UTC time, "🫵 You" or "👤 Counterparty", and the text indented,
with control characters, format characters (except the zero-width non-joiner and joiner)
and line and paragraph separators escaped. A line follows when older messages may be
missing, and "📤 Your message (id ...)" when one was sent. Human mode sends **without a
prompt**, as `dmtouser` does. A value the argument parser rejects (a bad UUID, a `--since`
that is not a number, a second `--message`) gets the parser's own message; other errors are
one `error: <fixed message>` line on stderr and nothing on stdout. An uncertain send adds
"The message may have reached a relay. Run `order chat --order <id>` and look for your
message before sending it again." and still prints the conversation and the message.
`--verbose` adds `verbose: order.chat <ok|code>` on stderr.

## Success data: `ChatData`

Also the `data` of an `uncertain` send.

| Field | Type | Meaning |
| --- | --- | --- |
| `order_id` | uuid | The order |
| `counterparty_pubkey` | hex64 | The counterparty's trade key |
| `messages` | array of `ChatRecord` | The conversation in the window, oldest first by `created_at` then `message_id`, at most 200; never the message sent on this run |
| `truncated` | boolean | A relay or the cap of 200 may have left out older messages |
| `sent` | `ChatRecord` or null | The message sent on this run; non-null exactly when `meta.publication` is `published` or `unknown` |

`meta.snapshot` is always null.

### ChatRecord

| Field | Type | Meaning |
| --- | --- | --- |
| `message_id` | hex64 | Id of the signed chat message inside its encrypted wrapper: the same on every relay. Deduplicate by it |
| `from` | `"me"` \| `"counterparty"` | `me` when the order's trade key wrote it |
| `created_at` | rfc3339 or null | When it was written; null with `invalid_event_timestamp` |
| `created_at_unix` | decimal string | Exact seconds |
| `text` | string | What was written: untrusted, at most 4096 bytes |

## Outcomes

| Case | status | code | Stages |
| --- | --- | --- | --- |
| Read | `ok` | | not_applicable / not_applicable / not_applicable |
| Read, then the message published | `ok` | | published / not_applicable / not_applicable |
| Bad option, `--message` without `--yes` in JSON | `error` | `invalid_arguments` (exit 2) | not_applicable / not_applicable / not_applicable |
| Configuration, identity, store, not in store, no counterparty, failed read | `error` | its code | not_applicable / not_applicable / not_applicable |
| Send step: the wrap failed, no relay connected, every relay refused | `error` | `internal_error`, `relay_connection_failed`, `request_rejected` | not_attempted / not_applicable / not_applicable |
| No relay confirmed, one failed ambiguously | `uncertain` | `request_rejected` (data present) | unknown / not_applicable / not_applicable |

Publication stays `not_applicable` until the send step runs, with or without `--message`.
`published` and `unknown` concern the relays only: the node never receives a chat message.
After `uncertain`, **do not send it again blindly**: run `order chat --order <id>` without
`--message`. The message reached a relay if a record whose `message_id` equals
`data.sent.message_id` is in `data.messages`.

## Errors

`invalid_arguments`, `configuration_missing`, `configuration_invalid`, `identity_missing`,
`identity_unreadable`, `store_unreadable`, `order_unknown`, `counterparty_unknown`,
`relay_connection_failed`, `relay_read_failed`, `read_timeout`, `read_limit_exceeded`,
`request_rejected`, `internal_error`. Never `pow_required`, `reply_timeout` or
`node_refused`: the node is not involved.

## Warnings

`invalid_event_timestamp`, `cleanup_incomplete`.

## Examples

{{#include ../../generated/order_chat.md}}

## Next

Poll it while you agree on the payment, as you poll [`message list`](message_list.md), and
deduplicate by `message_id`. The trade goes on with [`order fiat-sent`](order_fiat_sent.md)
and [`order release`](order_release.md).
