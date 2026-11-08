# Human-only commands

These commands still exist with their old spellings and human output only. With
`--output json` each returns `output_not_supported` (exit 2) **before doing anything**: no
configuration is loaded, no database is touched, nothing is sent. Their canonical names are already reserved and will
be used when they gain JSON output.

| CLI command | Reserved `command` | What it does |
| --- | --- | --- |
| `listdisputes` | `dispute.list` | List open disputes |
| `disputechat` | `dispute.chat` | Read the dispute conversation with the solver |
| `getdmuser` | `chat.history` | Read both sides of the peer chat of an order |
| `dmtouser` | `chat.send` | Send a peer chat message |
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

In human mode the ones that talk to the node also read the
[config file](../getting_started.md#the-config-file) (after 0.17.0, not yet released; with
0.17.0, set `MOSTRO_PUBKEY` and `RELAYS` in the environment or with `-m` and `-r`):

- `MOSTRO_PUBKEY`, `RELAYS`, `POW` and `TRANSPORT` each come from the root option, else the
  environment variable when it is set, even to an empty value, else `$MCLI_DIR/config`: the
  same precedence as the JSON-capable commands. The file's values never enter the
  environment.
- The file is read right after the root options are applied, before `ADMIN_NSEC` is read and
  before `mcli.db` is created. A refused file (the same refusals as for the JSON-capable
  commands) stops the command there with exit 1 and one line on stderr naming the file and
  the problem, and the line when a line is at fault, never the file's content:

  ```text
  Invalid config file /home/alice/.mcli/config: line 2 sets a key other than MOSTRO_PUBKEY, RELAYS, POW or TRANSPORT
  ```

- When `MOSTRO_PUBKEY` or `RELAYS` is missing, the error they print offers a line in
  `$MCLI_DIR/config` (else `~/.mcli/config`) as a third way to give it, next to the option
  and the environment variable.
- `ADMIN_NSEC`, which the admin commands need, stays in the environment: the file refuses it.
- The gRPC operator commands (`admsetmaintenance`, `admmaintenancestatus`,
  `admcancelpending`) never read the file.

A wrapper that needs one of these today has to run it in human mode and treat its output
as text for a person, not as data. Do not scrape it; its wording is not a contract.
