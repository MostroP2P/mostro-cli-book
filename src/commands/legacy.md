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

In human mode every one of them except the gRPC operator commands (`admsetmaintenance`,
`admmaintenancestatus`, `admcancelpending`), which never read it, also reads the
[config file](../getting_started.md#the-config-file) (after 0.17.0, not yet released; with
0.17.0, set `MOSTRO_PUBKEY` and `RELAYS` in the environment or with `-m` and `-r`):

- `MOSTRO_PUBKEY`, `RELAYS`, `POW` and `TRANSPORT` each come from the root option, else the
  environment variable when it is set, even to an empty value, else `$MCLI_DIR/config`: the
  same precedence as the JSON-capable commands. The file's values never enter the
  environment.
- The file is read right after the root options are applied, before `ADMIN_NSEC` is read and
  before `mcli.db` is created. A refused file (the same refusals as for the JSON-capable
  commands) stops the command there, even when the options give every value, with exit 1
  and one line on stderr naming the file and the problem, and the line when a line is at
  fault, never the file's content (control characters in the path are escaped):

  ```text
  Invalid config file /home/alice/.mcli/config: line 2 sets a key other than MOSTRO_PUBKEY, RELAYS, POW or TRANSPORT
  ```

- When `MOSTRO_PUBKEY` or `RELAYS` is missing, the error they print offers, next to the
  option and the environment variable, [`config set`](config_set.md)
  (`mostro-cli config set mostro-pubkey <npub>`, or `config set relays <relay[,relay...]>`),
  which writes it to `$MCLI_DIR/config` (else `~/.mcli/config`), suggests checking the
  file with [`config show`](config_show.md) (`mostro-cli config show`), and says that a
  variable that is set, even empty, wins over the file (unset it to use the file).
- A blank value counts as missing, whatever the file holds: an empty `-m`, or a
  `MOSTRO_PUBKEY` that is set but empty or only whitespace, prints `MOSTRO_PUBKEY not set`
  with that guidance instead of a key parse error, as an empty `-r` or `RELAYS` prints
  `RELAYS not set`. Either way the command stops with exit 1 before `mcli.db` is created
  and before any relay is contacted.
- `ADMIN_NSEC`, which the admin commands need, stays in the environment: the file refuses it.

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
  exits 2 with `error: The command arguments are invalid.`; a value the argument parser
  rejects (a bad UUID, a `--since` that is not a number, a second `--message`) exits 2 with
  the parser's own message. Both happen before any relay is contacted, and the message text
  never appears on stderr. The message is sent **without a prompt**, as `dmtouser` does;
  `--yes` is accepted and changes nothing in human mode.
- **Counterparty.** The order row's `counterparty_pubkey`, when it parses and is not your own
  trade key, is used as it is, unchecked, with no relay contacted; the removed `getdm` may
  have stored it, and nothing refreshes it. Otherwise the node's messages to the order's
  trade key are read once, and only the newest `buyer-took-order` or
  `hold-invoice-payment-accepted` naming both trade keys, or `fiat-sent-ok` with its peer,
  names it; the key is then saved in the row (a failed save is not reported). Neither is
  `counterparty_unknown` (exit 1):
  `error: The counterparty of this order was not found in the node's messages; it is known once the escrow is locked.`
  A trade whose lock-time messages are gone (beyond the newest 50 per relay, or expired after
  the node's `dm_days`) gets it too. Then `getdmuser -p` and `dmtouser -p`, which also need
  the order's row, are the fallback when you know the key.
- **Read, then send.** One bounded read of both sides in the window, oldest first, at most
  200, opened only with your trade key and the counterparty's as writers. The message is
  sent only after the read succeeded, so a failed read sends nothing.
- **Output.** "💬 Order Chat", the order and the counterparty, then "📭 No chat messages" or
  one block per message: the UTC time, "🫵 You" or "👤 Counterparty", and the text indented,
  with control characters, format characters (except the zero-width non-joiner and joiner)
  and line and paragraph separators escaped. A line follows when older messages may be
  missing (the read reached its limit of 200), and "📤 Your message (id ...)" when one was
  sent.
- **Errors** after the argument checks are one `error: <fixed message>` line on stderr and
  nothing on stdout, even when only the send failed after a good read. A send that no relay
  confirmed while one failed without a clear answer may have been delivered (exit 1): stderr
  gets `error: No relay confirmed accepting the request.` and "The message may have reached
  a relay. Run `order chat --order <id>` and look for your message before sending it
  again.", and stdout still shows the conversation and the message. It is never resent.
- **Not used:** `--pow`, `--transport` and `--reply-timeout` (a `--reply-timeout` out of
  range is still an argument error). The message goes to relays, never to the node: it mines
  no proof of work and waits for no reply. The worst case is 52 s for a read and 78 s with
  `--message`.
- `--verbose` adds one line on stderr, `verbose: order.chat <ok|code>`.
- `--output json` returns `output_not_supported` (exit 2) before anything runs, with the
  stages shown above; a call the argument parser rejects (a bad UUID, no `--order`) is
  `invalid_arguments` instead, also exit 2.
