# Shell and jq

For scripts and quick automation. `wrappers/shell/mostro.sh` defines a few functions:

```bash
{{#include ../../wrappers/shell/mostro.sh}}
```

## Recipes

```bash
# ids of pending USD sell orders, cheapest premium first
mostro-cli --output json order list --side sell --currency USD |
  jq -r '.data.orders | sort_by(.premium_percent | tonumber) | .[].id'

# fixed orders between 50 and 200 fiat units
mostro-cli --output json order list |
  jq '.data.orders[] | select(.fiat_amount_min == null and (.fiat_amount | tonumber) >= 50 and (.fiat_amount | tonumber) <= 200)'

# the status of one order
mostro-cli --output json order info --order "$ID" | jq -r '.data.orders[0].status // "not returned"'

# invoices the node is waiting for me to pay
mostro-cli --output json message list --since 120 |
  jq -r '.data.messages[] | select(.next_step == "pay_hold_invoice" or .next_step == "pay_bond_invoice")
         | "\(.order_id) \(.next_step) \(.payload.invoice)"'

# every requested action, newest last
mostro-cli --output json message list --since 1440 |
  jq -r '.data.messages[] | select(.next_step) | [.created_at, .order_id, .next_step] | @tsv'

# branch on the outcome of a write
out=$(mostro-cli --output json order cancel --order "$ID" --yes </dev/null)
case $(jq -r .status <<<"$out") in
  ok)        jq -r '.data.result' <<<"$out" ;;
  uncertain) echo "check with: mostro-cli --output json order info --order $ID" ;;
  error)     jq -r '"\(.error.code) \(.error.reason // "")"' <<<"$out" ;;
esac

# which commands does this binary support in JSON?
mostro-cli --output json schema | jq -r '.data.commands[] | select(.output_modes | index("json")) | .name'
```

`jq`'s `tonumber` is fine for **filtering** small values like premiums and fiat amounts,
but it uses doubles: never use it to compute with `sats_amount`.
