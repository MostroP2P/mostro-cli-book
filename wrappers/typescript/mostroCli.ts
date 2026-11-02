// Minimal TypeScript wrapper for the mostro-cli JSON interface (contract "1").
// Node 18+, no dependencies. Decimal strings stay strings; convert with BigInt.
//
//   import { MostroCli } from "./mostroCli.ts";
//   const cli = new MostroCli({ env: { MOSTRO_PUBKEY: "...", RELAYS: "wss://..." } });
//   const out = await cli.run(["order", "list", "--side", "sell"]);
//   if (out.status === "ok") console.log(out.data.orders.length);

import { execFile } from "node:child_process";

export type Status = "ok" | "error" | "uncertain";
export type Publication = "not_attempted" | "unknown" | "published" | "not_applicable";
export type DaemonAcceptance = "unknown" | "accepted" | "rejected" | "not_applicable";
export type Persistence = "not_attempted" | "applied" | "failed" | "not_applicable";

export type ErrorCode =
  | "invalid_arguments" | "output_not_supported"
  | "configuration_missing" | "configuration_invalid"
  | "relay_connection_failed" | "relay_read_failed" | "read_timeout" | "read_limit_exceeded"
  | "internal_error" | "identity_missing" | "identity_unreadable"
  | "protocol_unsupported" | "pow_required" | "request_rejected" | "reply_timeout"
  | "node_refused" | "reply_malformed" | "order_declined" | "order_not_saved"
  | "store_unwritable" | "order_unknown" | "store_unreadable";

export type WarningCode =
  | "invalid_event_timestamp" | "cleanup_incomplete" | "orders_not_returned"
  | "invalid_order_timestamp" | "local_status_stale" | "trade_keys_limited"
  | "trade_index_not_recorded";

/** Base-10 signed 64-bit integer as a string. Use BigInt(value) for arithmetic. */
export type Decimal = string;
export type Uuid = string;
export type Hex64 = string;
export type Rfc3339 = string;

export interface ErrorInfo { code: ErrorCode; message: string; reason?: string }
export interface Warning { code: WarningCode; message: string }

export interface Snapshot {
  since: Rfc3339; until: null; observed_at: Rfc3339;
  per_relay_limit: 50; max_unique_events: 10000;
  configured_relays: number; completed_relays: number; received_events: number;
  completion_policy: "all_relays_eose"; complete_history: false;
}

export interface Meta {
  publication: Publication; daemon_acceptance: DaemonAcceptance;
  persistence: Persistence; snapshot: Snapshot | null;
}

export interface Envelope<D = unknown> {
  schema_version: "1";
  command: string | null;
  status: Status;
  data: D | null;
  error: ErrorInfo | null;
  warnings: Warning[];
  meta: Meta;
}

export type Side = "buy" | "sell";
export type OrderStatus =
  | "active" | "canceled" | "canceled-by-admin" | "settled-by-admin" | "completed-by-admin"
  | "dispute" | "expired" | "fiat-sent" | "settled-hold-invoice" | "pending" | "success"
  | "waiting-buyer-invoice" | "waiting-payment" | "waiting-taker-bond" | "waiting-maker-bond"
  | "cooperatively-canceled" | "in-progress";

export interface PublicOrder {
  id: Uuid; side: Side; status: OrderStatus; sats_amount: Decimal; fiat_currency: string;
  fiat_amount: Decimal; fiat_amount_min: Decimal | null; fiat_amount_max: Decimal | null;
  payment_method: string; premium_percent: Decimal; created_at: Rfc3339 | null; created_at_unix: Decimal;
}

export interface OrderRecord {
  id: Uuid; side: Side | null; status: OrderStatus | null; sats_amount: Decimal; fiat_currency: string;
  fiat_amount: Decimal; fiat_amount_min: Decimal | null; fiat_amount_max: Decimal | null;
  payment_method: string; premium_percent: Decimal;
  buyer_trade_pubkey: Hex64 | null; seller_trade_pubkey: Hex64 | null;
  created_at: Rfc3339 | null; created_at_unix: Decimal | null;
  expires_at: Rfc3339 | null; expires_at_unix: Decimal | null;
}

export interface ListData {
  node_pubkey: Hex64;
  filters: { side: Side | null; currency: string | null; status: OrderStatus };
  orders: PublicOrder[];
}
export interface OrderInfoData { node_pubkey: Hex64; orders: OrderRecord[]; not_returned: Uuid[] }
export interface OrderNewData {
  node_pubkey: Hex64; order: OrderRecord; next_step: "wait_for_taker" | "pay_bond_invoice";
  payment_request: string | null; trade_index: Decimal; trade_pubkey: Hex64;
}
export interface OrderTakeData {
  node_pubkey: Hex64; order_id: Uuid; side: Side;
  next_step: "add_invoice" | "wait_for_seller_payment" | "pay_hold_invoice" | "pay_bond_invoice";
  order: OrderRecord | null; payment_request: string | null; trade_index: Decimal; trade_pubkey: Hex64;
}
export interface OrderInvoiceData {
  node_pubkey: Hex64; order_id: Uuid;
  result: "waiting_seller_payment" | "payment_accepted" | "invoice_updated";
  order: OrderRecord | null; trade_pubkey: Hex64;
}
export interface BondInvoiceData {
  node_pubkey: Hex64; order_id: Uuid; result: "invoice_accepted";
  counterparty_share_sats: Decimal | null; trade_pubkey: Hex64;
}
export interface StepData {
  node_pubkey: Hex64; order_id: Uuid;
  result: "fiat_sent" | "released" | "canceled" | "cancel_requested" | "cancel_accepted";
  next_step: "wait_for_release" | "wait_for_peer_cancel" | "sync_child_order" | null;
  trade_pubkey: Hex64; next_trade_index: Decimal | null;
}
export interface SyncData {
  node_pubkey: Hex64; since_minutes: Decimal;
  adopted: { order: OrderRecord; trade_index: Decimal; trade_pubkey: Hex64 }[];
  messages_read: Decimal; messages_ignored: Decimal; truncated: boolean;
  keys_read: Decimal; keys_not_read: Decimal;
}
export type MessagePayload =
  | { kind: "none" }
  | { kind: "order"; order: OrderRecord }
  | { kind: "payment_request"; order: OrderRecord | null; invoice: string; amount: Decimal | null }
  | { kind: "bond_payout_request"; order: OrderRecord; slashed_at: Rfc3339 | null; slashed_at_unix: Decimal }
  | { kind: "cant_do"; reason: string | null }
  | { kind: "peer"; counterparty_pubkey: string }
  | { kind: "text"; text: string }
  | { kind: "amount"; amount: Decimal }
  | { kind: "other"; variant: string };
export interface MessageRecord {
  event_id: Hex64; created_at: Rfc3339 | null; created_at_unix: Decimal;
  order_id: Uuid | null; request_id: Decimal | null; action: string;
  next_step: "pay_bond_invoice" | "add_invoice" | "pay_hold_invoice" | "add_bond_invoice" | null;
  trade_index: Decimal | null; trade_pubkey: Hex64; payload: MessagePayload;
}
export interface MessageListData {
  node_pubkey: Hex64; since_minutes: Decimal; messages: MessageRecord[];
  truncated: boolean; keys_read: Decimal; keys_not_read: Decimal;
}

/** Thrown when there is no usable envelope. `mayHaveActed` => treat like "uncertain". */
export class TransportError extends Error {
  mayHaveActed: boolean;
  stderr: string;
  constructor(message: string, mayHaveActed: boolean, stderr = "") {
    super(message);
    this.mayHaveActed = mayHaveActed;
    this.stderr = stderr;
  }
}

export interface Options { binary?: string; env?: Record<string, string>; timeoutMs?: number }

export class MostroCli {
  private binary: string;
  private env: NodeJS.ProcessEnv;
  private timeoutMs: number;

  constructor(options: Options = {}) {
    this.binary = options.binary ?? "mostro-cli";
    this.env = { ...process.env, ...(options.env ?? {}) };
    this.timeoutMs = options.timeoutMs ?? 45_000;
  }

  /** Runs `mostro-cli --output json ...args`. `write` marks commands that publish a change. */
  run<D = unknown>(args: string[], write = false): Promise<Envelope<D> & { exitCode: number }> {
    const argv = ["--output", "json", ...args];
    return new Promise((resolve, reject) => {
      const child = execFile(this.binary, argv, { env: this.env, timeout: this.timeoutMs, maxBuffer: 16 << 20 },
        (error, stdout, stderr) => {
          const exitCode = typeof child.exitCode === "number" ? child.exitCode : -1;
          if (error && (error as NodeJS.ErrnoException).code === "ENOENT") {
            return reject(new TransportError(`cannot start ${this.binary}`, false));
          }
          if (error && error.killed) return reject(new TransportError("timed out", write, stderr));
          const text = stdout.trim();
          if (!text) return reject(new TransportError("empty stdout", write && exitCode === 1, stderr));
          let envelope: Envelope<D>;
          try {
            envelope = JSON.parse(text);
          } catch {
            return reject(new TransportError("stdout is not one JSON document", write, stderr));
          }
          if (envelope.schema_version !== "1") {
            return reject(new Error(`unsupported schema_version ${String(envelope.schema_version)}`));
          }
          resolve({ ...envelope, exitCode });
        });
      child.stdin?.end(); // the CLI never reads stdin in JSON mode
    });
  }

  orderList(f: { side?: Side; currency?: string; status?: OrderStatus } = {}) {
    return this.run<ListData>(["order", "list", ...opt("--side", f.side), ...opt("--currency", f.currency),
      ...opt("--status", f.status)]);
  }
  orderInfo(...ids: Uuid[]) {
    return this.run<OrderInfoData>(["order", "info", ...ids.flatMap((id) => opt("--order", id))]);
  }
  messageList(f: { since?: number; order?: Uuid } = {}) {
    return this.run<MessageListData>(["message", "list", ...opt("--since", f.since), ...opt("--order", f.order)]);
  }
  orderSync(since?: number) {
    return this.run<SyncData>(["order", "sync", ...opt("--since", since)]);
  }
  /** Every write needs the user's consent; it is passed as --yes. */
  write<D>(args: string[], confirmed: boolean) {
    if (!confirmed) throw new Error("write commands need the user's confirmation (--yes)");
    return this.run<D>([...args, "--yes"], true);
  }
  fiatSent(order: Uuid, confirmed: boolean) { return this.write<StepData>(["order", "fiat-sent", ...opt("--order", order)], confirmed); }
  release(order: Uuid, confirmed: boolean) { return this.write<StepData>(["order", "release", ...opt("--order", order)], confirmed); }
  cancel(order: Uuid, confirmed: boolean) { return this.write<StepData>(["order", "cancel", ...opt("--order", order)], confirmed); }
}

// Attached form, so a value starting with "-" is never parsed as an option.
function opt(flag: string, value: string | number | undefined): string[] {
  return value === undefined ? [] : [`${flag}=${value}`];
}
