# Human-only commands

These commands still exist with their old spellings and human output only. With
`--output json` each returns `output_not_supported` (exit 2) **before doing anything**: no
configuration is loaded, no database is touched, nothing is sent. Their canonical names are already reserved and will
be used when they gain JSON output.

`order watch` is new, not an old spelling, but it has human output only for now, so it is
listed here too; see [`order watch`](#order-watch) below.

| CLI command | Reserved `command` | What it does |
| --- | --- | --- |
| `listdisputes` | `dispute.list` | List open disputes |
| `disputechat` | `dispute.chat` | Read the dispute conversation with the solver |
| `getdmuser` | `chat.history` | Read both sides of the peer chat of an order |
| `dmtouser` | `chat.send` | Send a peer chat message |
| `order watch` | `order.watch` | Follow an order's node messages and chat until the trade ends (human output for now) |
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

## `order watch`

After 0.17.0, not yet released. It follows an order you hold until its trade ends: the
node's messages to the order's trade key and, once the counterparty is known, the order's
peer chat. It is the one command that stays connected. It reads only and publishes nothing.

```sh
mostro-cli order watch --order <order-id>
mostro-cli order watch --order <order-id> --since 120 --timeout 3600
```

- **Needs** `MOSTRO_PUBKEY` and `RELAYS` (each from its root option, its environment variable
  or the [config file](../getting_started.md#the-config-file)), an existing identity (it never creates one) and the
  order's row in the local store. An order with no row is `order_unknown`, before any relay
  is contacted.
- **Options.** `--since` is how far back to replay first, 1 to 10080 minutes (default 30).
  `--timeout` is 1 to 86400 seconds, counted from the end of the first replay; without it
  the watch has no deadline. `--after <cursor>` (conflicts with `--since`) is accepted
  already, but the cursor it takes comes with the JSON output, which does not exist yet. An
  invalid value exits 2 before configuration, store or relay access, and is never shown.
- **Replay, then live.** The window is replayed first, then each new record is printed as it
  arrives. Each record is shown once: node messages by event id, chat messages by their
  `message_id`, across relays and resends. The opening replay is strict, as the reads are:
  every relay must connect within 10 s and finish the replay within 15 s. After that, a relay
  that drops reconnects on its own (every 10 s) and replays the window; no relay failure
  ends a live watch. After 10,000 records the watch ends with `read_limit_exceeded`.
- **Counterparty.** Found as [`order chat`](order_chat.md) finds it. When it is not known
  yet, the watch starts without the chat, and the first new node message that names it
  brings the chat in, with its replay; the watch does not save that key, the next lookup
  does.
- **End.** A node message for this order with `purchase-completed`,
  `hold-invoice-payment-settled`, `canceled`, `cooperative-cancel-accepted` or
  `admin-canceled` ends the watch. `admin-settled` ends it only for the seller (the order's
  row says which side you are); the buyer's payout follows and can still fail and ask for a
  new invoice. `rate`, `bond-slashed` and `add-bond-invoice` may arrive after the end: read
  them with [`message list --order`](message_list.md). Some watches never end on their own:
  an untaken order that expires (the node sends the maker nothing) and a trade that ended
  before the window. Use `--timeout`, and [`order info`](order_info.md) for the order's
  status.
- **Output.** "👀 Watching order <id>", the window start and the counterparty (or "not
  known yet; the chat is followed once the escrow is locked"); "📭 Nothing yet; waiting for
  the node or the counterparty..." when the replay is empty; then each update: a node
  message as `message list` shows it, with its next step, under "📨 From Mostro:", and a
  chat message as `order chat` shows it, escaped, under "💬 Chat:". A line follows when the
  counterparty is learned and one when older messages may be missing. Each update is
  written whole and flushed. The last line is "🏁 The trade ended: <action>", or at
  `--timeout` "⏰ Stopped at the watch deadline; no ending message was seen. Run
  `order info` to check the order."; both exit 0. Ctrl-C stops it, with no exit status
  promised.
- **Errors** after parsing go to stderr as one `error: <fixed message>` line, never with an
  argument's value (exit 1, 2 for a bad value); an argument the parser rejects gets its
  fixed description and a `--help` hint (exit 2). A stdout that cannot be written stops the
  watch with `error: the watch could not be written` (exit 1). On Unix, a reader that
  closes stdout while the watch is idle (`| head -n 5`, a closed pager) stops it the same
  way; elsewhere the watch notices at its next write. The read warnings are not printed in
  human mode.
- **Not used:** `--pow` and `--transport`, not even an invalid value, and `--reply-timeout`
  (an invalid `--reply-timeout` still exits 2): nothing goes to the node. Timing: 10 s to connect, 15 s for the replay, 15 s more when the
  counterparty is learned (up to 26 s first when it must be looked up), then live until the
  end or `--timeout`, then 1 s of cleanup.
- `--verbose` adds one line on stderr, `verbose: order.watch <ok|code>`.
- `--output json` returns `output_not_supported` (exit 2) before any configuration, store or
  relay access, with the stages shown above. An argument the parser refuses, such as an
  order id that is not a UUID, is `invalid_arguments` (exit 2) instead.
