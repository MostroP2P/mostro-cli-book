# Order statuses

The `status` of an order, as defined by the Mostro protocol (wire names, with hyphens).
`order list --status` accepts all of them (any letter case; default `pending`).

| Status | Meaning | Typical next |
| --- | --- | --- |
| `pending` | Published on the book, waiting for a taker | Taken → `waiting-buyer-invoice` / `waiting-payment`; or canceled / expired |
| `waiting-maker-bond` | Bonded node: waiting for the maker's bond | `pending` once paid |
| `waiting-taker-bond` | Bonded node: taken, waiting for the taker's bond | Continues the take once paid |
| `waiting-buyer-invoice` | Taken; the node waits for the buyer's invoice | `order add-invoice` |
| `waiting-payment` | The node waits for the seller to pay the hold invoice | Seller pays |
| `active` | Sats locked and buyer invoice known; the buyer must pay the fiat | `order fiat-sent` |
| `fiat-sent` | The buyer reported the fiat payment | Seller checks and runs `order release` |
| `settled-hold-invoice` | The seller released; the hold invoice is settled; the node pays the buyer | `success` |
| `success` | The buyer was paid; trade complete | Rate (human-only) |
| `canceled` | Canceled | — |
| `cooperatively-canceled` | Canceled by both parties | — |
| `expired` | A pending order reached its expiration | — |
| `dispute` | A dispute is open; a solver handles it | Human-only dispute commands |
| `canceled-by-admin` | A solver/admin canceled it (the seller is refunded) | — |
| `settled-by-admin` | A solver/admin settled it (the buyer is paid) | — |
| `completed-by-admin` | A solver/admin closed it as completed | — |
| `in-progress` | Defined by the protocol; the CLI passes it through | — |

Terminal statuses for a polling loop: `success`, `canceled`, `cooperatively-canceled`,
`expired`, `canceled-by-admin`, `settled-by-admin`, `completed-by-admin`.

See the [protocol book](https://mostro.network/protocol/) for the daemon's precise state
machine.
