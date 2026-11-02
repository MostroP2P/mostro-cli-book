#!/usr/bin/env bash
# Shell helpers for the mostro-cli JSON interface. Needs bash and jq.
#
#   source wrappers/shell/mostro.sh
#   out=$(mostro_json order list --side sell) ; rc=$?
#   mostro_status "$out"            # ok | error | uncertain | transport
#   jq -r '.data.orders[].id' <<<"$out"

MOSTRO_CLI="${MOSTRO_CLI:-mostro-cli}"

# Runs one command in JSON mode and prints its envelope. Returns the CLI's exit
# code. stdin is closed; stderr is passed through.
mostro_json() {
  "$MOSTRO_CLI" --output json "$@" </dev/null
}

# Prints ok, error, uncertain, or transport when $1 is not one JSON envelope.
mostro_status() {
  jq -er 'select(.schema_version == "1") | .status' <<<"$1" 2>/dev/null || echo transport
}

# Prints the error code, or nothing.
mostro_code() {
  jq -r '.error.code // empty' <<<"$1" 2>/dev/null
}

# Example: list pending sell orders in a currency, one line each.
mostro_book() {
  local out
  out=$(mostro_json order list --side sell --currency "${1:-USD}") || true
  case "$(mostro_status "$out")" in
    ok) jq -r '.data.orders[] |
          [.id, .fiat_currency,
           (if .fiat_amount_min then "\(.fiat_amount_min)-\(.fiat_amount_max)" else .fiat_amount end),
           (if .sats_amount == "0" then "market" else .sats_amount end),
           "\(.premium_percent)%", .payment_method] | @tsv' <<<"$out" ;;
    transport) echo "no envelope" >&2; return 1 ;;
    *) echo "failed: $(mostro_code "$out")" >&2; return 1 ;;
  esac
}
