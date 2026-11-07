# Range orders

A **range order** advertises a fiat interval instead of a fixed amount:

```sh
mostro-cli --output json order new --side sell --currency USD \
  --fiat-amount 10 --fiat-amount-max 100 --payment-method "Zelle" --yes
```

It is always at market price (`--sats` must be 0). In outcomes it shows as
`fiat_amount_min: "10"`, `fiat_amount_max: "100"` (and usually `fiat_amount: "0"`).

## Taking a range order

The taker chooses an amount inside the range:

```sh
mostro-cli --output json order take-sell --order <id> --amount 50 --yes
mostro-cli --output json order take-buy  --order <id> --amount 50 --yes
```

The node checks it (a value outside the range is refused, typically `invalid_amount`).
For the taker, the trade is then an ordinary trade.

## Continuing the range as the maker

After a partial trade, the node creates a **child order** with the same terms for the rest
of the range (here 10..50 USD), under a **new trade key of the maker**. For that, the
maker's request must carry the next key. `mostro-cli` does this automatically, only when
you are the maker of a range order with room left (`max − traded ≥ min`) and only in the
maker's own step:

| You made a... | The step that carries the next key | When the child is announced |
| --- | --- | --- |
| `sell` range order | `order release` | Right after the release |
| `buy` range order | `order fiat-sent` | When the seller releases |

The outcome reports the reserved index in `data.next_trade_index`, and for a sell order's
release `data.next_step` is `sync_child_order`.

The child order is announced with a `new-order` message to the new key. Commands acting on
an order need a local row, so give it one:

```sh
mostro-cli --output json order sync
```

`data.adopted[0].order.id` is the child's id; it is now usable with `order cancel`,
`order release`, etc. `order sync` is idempotent: run it after every range step, or
periodically.

## Sequence (sell range order)

```text
maker: order new (10..100)               → order A, key #3
taker: order take-sell --amount 40       → trade on A
maker: pays hold invoice; taker: fiat-sent
maker: order release --order A           → released, next_trade_index "4", next_step sync_child_order
node : new-order (child B, 10..60) to key #4
maker: order sync                        → adopted: [B, trade_index "4"]
maker: order cancel --order B            (works: B has a row now)
```

## Pitfalls

- The index of the next key (#4 above) is recorded in the store before the step is
  published. If it cannot be recorded, the step fails with `store_unwritable` and nothing is
  sent; fix the store and run the step again.
- Orders saved by older CLI versions mark taken orders as "mine" too; for those, a taker's
  step may send a next key that the node ignores, costing one trade index. Harmless.
- `cancel` never continues a range.
