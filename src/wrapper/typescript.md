# TypeScript

`wrappers/typescript/mostroCli.ts` — Node 18+, no dependencies. It contains complete
TypeScript types for every data object of contract 1, usable on their own (for example to
type the output of a different runner). Tested (`node --experimental-strip-types`) with
Node 22 against a pre-release build and with Node 24 against mostro-cli 0.17.0.

```ts
import { MostroCli, TransportError } from "./mostroCli.ts";

const cli = new MostroCli({ env: { MOSTRO_PUBKEY: "<node hex>", RELAYS: "wss://relay.example.com" } });

const book = await cli.orderList({ side: "sell", currency: "EUR" });
if (book.status === "ok" && book.data) {
  for (const o of book.data.orders) {
    const sats = BigInt(o.sats_amount);          // decimal strings → BigInt, never Number
    console.log(o.id, sats === 0n ? "market" : sats.toString(), o.payment_method);
  }
}

const inbox = await cli.messageList({ since: 60 });
for (const m of inbox.data?.messages ?? []) {
  if (m.payload.kind === "payment_request") {
    console.log(`${m.next_step}: pay ${m.payload.invoice}`);   // narrowed by kind
  }
}

const orderId = "00000000-0000-0000-0000-000000000001";
try {
  const step = await cli.release(orderId, /* confirmed by the user */ true);
  if (step.status === "uncertain") {
    const info = await cli.orderInfo(orderId);   // check before doing anything else
  }
} catch (e) {
  if (e instanceof TransportError && e.mayHaveActed) { /* treat as uncertain */ }
}
```

## Source

```ts
{{#include ../../wrappers/typescript/mostroCli.ts}}
```
