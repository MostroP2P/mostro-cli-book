# Python

`wrappers/python/mostro_cli.py` — standard library only, Python 3.8+. Tested against
mostro-cli 0.17.0 (offline outcomes).

```python
from mostro_cli import MostroCli, TransportError

cli = MostroCli(env={"MOSTRO_PUBKEY": "<node hex>", "RELAYS": "wss://relay.example.com"})

book = cli.order_list(side="sell", currency="EUR")
if book.ok:
    for o in book.data["orders"]:
        amount = (f"{o['fiat_amount_min']}-{o['fiat_amount_max']}"
                  if o["fiat_amount_min"] is not None else o["fiat_amount"])
        print(o["id"], amount, o["fiat_currency"], o["payment_method"])
else:
    print("cannot read the book:", book.code)

# a write: `confirmed` must come from the user
order_id = "00000000-0000-0000-0000-000000000001"
try:
    out = cli.take_sell(order_id, confirmed=True)
except TransportError as exc:
    if exc.may_have_acted:
        print("unknown result; check with order info before retrying")
    raise
if out.ok and out.next_step == "add_invoice":
    sats = int(out.data["order"]["sats_amount"])   # create an invoice for this amount
elif out.uncertain:
    check = cli.order_info(order_id)                # never take again before checking
elif out.code == "node_refused":
    print("refused:", out.reason)
```

## Source

```python
{{#include ../../wrappers/python/mostro_cli.py}}
```

For message records, read the step with `message_next_step(record)`: it returns `None` for a
`next_step` value the wrapper does not know (the enum is open within contract 1). Read a
payload's fields only for a `kind` you know.

## Following a trade

`wrappers/python/example_trade_loop.py` polls `order info` and `message list` for one order
and prints what to do for each `next_step`. It never runs a write. With a binary that has
[`order watch`](../commands/order_watch.md), wait with it instead of polling.

```python
{{#include ../../wrappers/python/example_trade_loop.py}}
```
