# Command index

Every JSON-capable command, with what it touches. "Identity" means the local `mcli.db`
must already exist; only `identity init` creates it.

| CLI path | `command` | Kind | Network | Identity | Local write | `--yes` | Statuses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [`schema`](schema.md) | `schema` | offline | none | no | no | no | ok, error |
| [`config set`](config_set.md) | `config.set` | local write | none | no | `config` | no | ok, error |
| [`identity init`](identity_init.md) | `identity.init` | local write | none | creates it | `mcli.db` | no | ok, error |
| [`identity show`](identity_show.md) | `identity.show` | local read | none | yes (read) | no | no | ok, error |
| [`order mine`](order_mine.md) | `order.mine` | local read | none | yes (read) | no | no | ok, error |
| [`order list`](order_list.md) | `order.list` | public read | reads relays | no | no | no | ok, error |
| [`order info`](order_info.md) | `order.info` | request | 1 signed request | yes (read) | no | no | ok, error |
| [`message list`](message_list.md) | `message.list` | private read | reads relays | yes (read) | no | no | ok, error |
| [`order sync`](order_sync.md) | `order.sync` | private read + local write | reads relays | yes | order rows | no | ok, error, uncertain |
| [`order new`](order_new.md) | `order.new` | write | 1 signed request | yes | index + row | **yes** | ok, error, uncertain |
| [`order take-sell`](order_take_sell.md) | `order.take-sell` | write | 1 signed request | yes | index + row | **yes** | ok, error, uncertain |
| [`order take-buy`](order_take_buy.md) | `order.take-buy` | write | 1 signed request | yes | index + row | **yes** | ok, error, uncertain |
| [`order add-invoice`](order_add_invoice.md) | `order.add-invoice` | write | 1 signed request | yes | status | **yes** | ok, error, uncertain |
| [`bond add-invoice`](bond_add_invoice.md) | `bond.add-invoice` | write | 1 signed request | yes | none | **yes** | ok, error, uncertain |
| [`order fiat-sent`](order_fiat_sent.md) | `order.fiat-sent` | write | 1 signed request | yes | status (+ index) | **yes** | ok, error, uncertain |
| [`order release`](order_release.md) | `order.release` | write | 1 signed request | yes | status (+ index) | **yes** | ok, error, uncertain |
| [`order cancel`](order_cancel.md) | `order.cancel` | write | 1 signed request | yes | status | **yes** | ok, error, uncertain |
| [`dispute open`](dispute_open.md) | `dispute.open` | write | 1 signed request | yes | status | **yes** | ok, error, uncertain |
| [`order rate`](order_rate.md) | `order.rate` | write | 1 signed request | yes | none | **yes** | ok, error, uncertain |

All of them need `MOSTRO_PUBKEY` and `RELAYS` (root option, environment or
[config file](../getting_started.md#the-config-file)) except `schema`, `config set`,
`identity init`, `identity show` and `order mine`, which only use the local data directory
(`MCLI_DIR`, else `~/.mcli`) or nothing at all.

## Which key signs what

| Command | Signed with |
| --- | --- |
| `order info` | Identity key (index 0) |
| `order new`, `order take-*` | A **new** trade key at the next trade index (reserved locally first) |
| `order add-invoice`, `bond add-invoice`, `order fiat-sent`, `order release`, `order cancel`, `dispute open`, `order rate` | The trade key stored with the order's local row (hence `order_unknown` when the row is missing) |

## Command page layout

Each page has the same sections: a summary table, **Invocation**, **Input**, **Behavior**,
**Success data**, **Outcomes**, **Errors**, **Warnings**, **Examples** and **Next**.
The input and output schemas quoted are in `schemas/<command>.input.json` and
`schemas/<command>.output.json`.

## Input schemas

The discovery document gives an `input_schema` per command, generated from the argument
parser: one property per long option (`fiat-amount`, `yes`...), except the positional
arguments described below. Values are typed as strings because they are command-line
tokens, except the flag `yes`, a boolean, and the repeatable `order info --order`, an array
of strings. A wrapper can use it to build forms or LLM tool definitions, then turn the
object into `argv`: `{"order": "…", "yes": true}` → `--order … --yes`; an array gives the
option once per value.

A property marked `"x-positional": N` is a positional argument, not an option. Today these
are `key` (0) and `value` (1) of [`config set`](config_set.md) (after 0.17.0, not yet
released). Pass them after the command path in the order of `N` (0-based), with the
global options before the command path, and put `--` before them when a value could start
with `-`: `{"key": "pow", "value": "3"}` → `config set -- pow 3`. A wrapper that ignores the
keyword passes them as options (`--key pow`) and gets `invalid_arguments` (exit 2), with
nothing written.
