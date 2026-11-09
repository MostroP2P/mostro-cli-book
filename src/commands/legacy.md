# Human-only commands

These commands still exist with their old spellings and human output only. With
`--output json` each returns `output_not_supported` (exit 2) **before doing anything**: no
configuration is loaded, no database is touched, nothing is sent. Their canonical names are already reserved and will
be used when they gain JSON output.

`order chat` is new, not an old spelling, but it has human output only for now, so it is
listed here too; see [`order chat`](#order-chat) below.

| CLI command | Reserved `command` | What it does |
| --- | --- | --- |
| `listdisputes` | `dispute.list` | List open disputes |
| `disputechat` | `dispute.chat` | Read the dispute conversation with the solver |
| `getdmuser` | `chat.history` | Read both sides of the peer chat of an order |
| `dmtouser` | `chat.send` | Send a peer chat message |
| `order chat` | `order.chat` | Read the peer chat of an order and send one message, without the counterparty's key |
| `senddm` | `message.send` | Send a direct message to a user |
| `restore` | `account.restore` | Ask the node for your active orders and disputes |
| `getuserinfo` | `account.info` | Your reputation as the node holds it |
| `getlasttradeindex` | `account.trade-index` | Ask the node for your last trade index and store it |
| `getlasttradeprivkey` | `account.trade-key` | Print the last trade **private** key |
| `conversationkey` | `account.conversation-key` | Print a conversation key |
| `getadmindm` | `admin.message-list` | Latest direct messages (admin) |
| `admcancel` | `admin.cancel` | Cancel an order (admin) |
| `admsettle` | `admin.settle` | Settle a hold invoice (admin) |
| `admaddsolver` | `admin.add-solver` | Add a dispute solver (admin) |
| `admtakedispute` | `admin.take-dispute` | Take a dispute (admin/solver) |
| `admsenddm` | `admin.message-send` | Admin direct message |
| `sendadmindmattach` | `admin.message-attach` | Admin message with encrypted attachment |
| `admsetmaintenance` | `maintenance.set` | Toggle the daemon's maintenance mode (operator, gRPC) |
| `admmaintenancestatus` | `maintenance.status` | Maintenance status (operator, gRPC) |
| `admcancelpending` | `maintenance.cancel-pending` | Cancel a pending order as operator (gRPC) |

```sh
mostro-cli --output json getlasttradeprivkey
```

```json
{{#include ../../examples/general/output_not_supported_secret.json}}
```

_`general/output_not_supported_secret` · exit 2 · fixture_

Note the stages `not_attempted / unknown / not_attempted`: the command was resolved but
not executed.

A wrapper that needs one of these today has to run it in human mode and treat its output
as text for a person, not as data. Do not scrape it; its wording is not a contract.

## `order chat`

After 0.17.0, not yet released. It reads the peer chat (kind 14) of an order you hold and,
with `--message`, sends one message to its counterparty. You never pass the counterparty's
key. It replaces `getdmuser` and `dmtouser`, which stay as the fallback described below.

```sh
mostro-cli order chat --order <order-id>
mostro-cli order chat --order <order-id> --message "hi, sending now"
```

- **Needs** `MOSTRO_PUBKEY`, `RELAYS`, an existing identity (it never creates one) and the
  order's row in the local store. An order with no row is `order_unknown`, before any relay
  is contacted.
- **Options.** `--since` is 1 to 10080 minutes (default 10080, the seven-day chat window).
  `--message` takes one value, trimmed, 1 to 4096 bytes; a text that starts with `-` is
  written `--message=<text>`. A `--since` out of range or a message that is empty or too long
  exits 2 with `error: The command arguments are invalid.`; a second `--message` or a bad
  UUID exits 2 with the argument parser's own message. Both happen before any relay is
  contacted, and the message text never appears on stderr. The message is sent **without a
  prompt**, as `dmtouser` does; `--yes` is accepted and changes nothing in human mode.
- **Counterparty.** The order row's `counterparty_pubkey`, when it parses and is not your own
  trade key, is used as it is, with no relay contacted. The legacy `getdm` may have stored it
  and never refreshes it. Otherwise the node's messages to the order's trade key are read
  once, and only the newest `buyer-took-order` or `hold-invoice-payment-accepted` naming both
  trade keys, or `fiat-sent-ok` with its peer, names it; the key is then saved in the row (a
  failed save is not reported). Neither gives exit 1 and
  `error: The counterparty of this order was not found in the node's messages; it is known once the escrow is locked.`
  A trade whose lock-time messages are gone (beyond the newest 50 per relay, or expired after
  the node's `dm_days`) gets it too. Then `getdmuser -p` and `dmtouser -p`, which also need
  the order's row, are the fallback when you know the key.
- **Read, then send.** One bounded read of both sides in the window, oldest first, at most
  200, opened only with your trade key and the counterparty's as writers. The message is
  sent only after the read succeeded, so a failed read sends nothing.
- **Output.** "💬 Order Chat", the order and the counterparty, then "📭 No chat messages" or
  one block per message: the UTC time, "🫵 You" or "👤 Counterparty", and the text indented,
  with control, format and line separator characters escaped. A line follows when older
  messages may be missing (the read reached its limit of 200), and
  "📤 Your message (id ...)" when one was sent.
- **Errors** after the argument checks are one `error: <fixed message>` line on stderr and
  nothing on stdout. A send that no relay confirmed while one failed without a clear answer
  may have been delivered (exit 1): stderr gets
  `error: No relay confirmed accepting the request.` and "The message may have reached a
  relay. Run `order chat --order <id>` and look for your message before sending it again.",
  and stdout still shows the conversation and the message. It is never resent.
- **Not used:** `--pow`, `--transport` and `--reply-timeout`. The message goes to relays,
  never to the node: it mines no proof of work and waits for no reply. The worst case is
  52 s for a read and 78 s with `--message`.
- `--verbose` adds one line on stderr, `verbose: order.chat <ok|code>`.
- `--output json` returns `output_not_supported` (exit 2) before anything runs, with the
  stages shown above.
