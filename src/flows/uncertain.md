# Recovering from uncertain outcomes

`status: "uncertain"` means: **a request was, or may have been, published, and the CLI
cannot prove what the node did** — or the node accepted it and the local write failed. The
CLI never retries on its own. Neither should you, until you have checked.

Why it matters: retrying a write that already happened can create a second order, take a
second order, or (for `release`) act twice on money.

## Step 1: read the stages

| `meta` | Meaning |
| --- | --- |
| `publication: published`, `daemon_acceptance: accepted`, `persistence: failed` (`order_not_saved`) | The node **did** act. Only the local row is missing. `data` is present. |
| `publication: published`, `daemon_acceptance: unknown` | The request reached a relay; the node may or may not have acted. |
| `publication: unknown` | A relay may have the request; it may never have reached the node. |

## Step 2: check, per command

| Command | How to check | It happened if |
| --- | --- | --- |
| `order new` | `message list --since 30`; look for messages about a new order of yours. If `data` is present (`order_not_saved`), you have the id: `order info --order <data.order.id>` | An order with your terms exists for your key |
| `order take-sell` / `take-buy` | `order info --order <id>` | Status moved past `pending` and your trade key appears as buyer/seller |
| `order add-invoice` | `order info --order <id>` | Status is no longer `waiting-buyer-invoice` |
| `bond add-invoice` | Wait for the payout; `message list` | The payout arrives / no new request |
| `order fiat-sent` | `order info --order <id>` | Status `fiat-sent` (or later) |
| `order release` | `order info --order <id>` | Status `settled-hold-invoice` or `success` |
| `order cancel` | `order info --order <id>` | Status `canceled` / `cooperatively-canceled`, or a cooperative-cancel message in `message list` |
| `dispute open` | `order info --order <id>` | Status `dispute`. **Do not resend blindly**: the node answers a second dispute on the same order with silence |
| `order rate` | No command shows it | Assume it may have happened; do not resend (the node does not answer a side that already rated) |
| `order sync` | Run `order sync` again | It is idempotent; always safe |

Give the node a little time (tens of seconds) before concluding it did not act: a
`reply_timeout` can simply be a slow answer.

## Step 3: act

| Finding | Action |
| --- | --- |
| It happened, and the local row exists | Continue the flow from the new status |
| It happened, row missing (`order_not_saved`) | Fix the store (disk, permissions). For a take or new order, commands needing the row return `order_unknown`; copy `data` somewhere safe. Range children can be recovered with `order sync` |
| It did not happen | Retry the same command. For `order new`/`take-*` the CLI will use a **fresh trade index** (the old one was spent), which is what the node expects |
| Cannot tell | Wait and check again; ask the user. Never loop retries automatically |

## Trade index after uncertain

For `order new` and the takes, `meta.persistence` on an uncertain outcome is about the
reserved trade index. The CLI records the index as spent **before** it publishes, so it is
`applied`: the next attempt uses a fresh key, which is what the node expects. An index
that cannot be recorded stops the command with `store_unwritable` before anything is sent,
so there is nothing uncertain to recover.

## A small state machine

```text
                 ┌──────── ok ───────► continue
run(command) ────┼──────── error ────► fix by code, retry allowed
                 └──────── uncertain ─► CHECK (order info / message list)
                                          ├─ happened ─────► continue
                                          ├─ not happened ─► retry once
                                          └─ unknown ──────► ask the user
```
