# schema

| | |
| --- | --- |
| `command` | `schema` |
| Kind | Offline discovery |
| Needs | Nothing: no configuration, identity, network or stdin |
| Statuses | `ok`, `error` |
| Schemas | `schemas/schema.input.json`, `schemas/schema.output.json` |

Describes the machine interface of **this** binary: every command, whether it supports
JSON, its input schema, its output schema and the configuration it reads.

## Invocation

```text
mostro-cli --output json schema
mostro-cli schema                  # human mode: the same DiscoveryData, pretty-printed, without envelope
```

## Input

None. Any option is `invalid_arguments`.

## Behavior

Pure and deterministic for a given binary. It never reads environment values or the config
file (so it never prints secrets or relay URLs), never opens the database and never
connects. Call it once at wrapper start-up and cache it keyed by `executable_version`.

## Success data: `DiscoveryData`

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | string | Contract version, `"1"` |
| `executable_version` | string | Package version of the binary, e.g. `"0.17.0"` |
| `schema_dialect` | string | `"https://json-schema.org/draft/2020-12/schema"` |
| `commands` | array of `CommandDescriptor` | Sorted by `name`; JSON-capable and human-only commands alike |
| `global_options` | array of `GlobalOption` | The options accepted at any command depth (`output`, `reply-timeout`), sorted by `name` |

### CommandDescriptor

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Canonical dotted name, as in the `command` field of outcomes |
| `cli_path` | array of string | Tokens to type today, e.g. `["order", "take-sell"]`, `["getdmuser"]` |
| `output_modes` | array of `"human"` \| `"json"` | `["human", "json"]` for the JSON-capable commands, `["human"]` for the [human-only](legacy.md) ones |
| `input_schema` | object or null | JSON Schema of the options (and of the positional arguments, marked `x-positional`); `null` for human-only commands |
| `output_schema` | object or null | JSON Schema of the whole envelope; `null` for human-only commands |
| `required_configuration` | array of string or null | Names of the required settings (`["MOSTRO_PUBKEY", "RELAYS"]`), each from its root option, its environment variable or the [config file](../getting_started.md#the-config-file) key of that name; `[]` for the local commands (`schema`, `config set`, `config show`, `identity init`, `identity show`, `order mine`); `null` when not modeled (the human-only commands) |

Example descriptor (trimmed):

```json
{
  "name": "order.cancel",
  "cli_path": ["order", "cancel"],
  "output_modes": ["human", "json"],
  "input_schema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "order": { "type": "string", "description": "Id of the order" },
      "yes": { "type": "boolean", "description": "Send the request without asking (required with --output json)" }
    },
    "required": ["order"]
  },
  "output_schema": { "title": "...", "oneOf": ["..."], "$defs": {"...": "..."} },
  "required_configuration": ["MOSTRO_PUBKEY", "RELAYS"]
}
```

Input schemas use three extension keywords: `"x-case-insensitive": true` on enums that
accept any letter case (`side`, `status` of `order list`), `"x-stdin": "-"` on the options
that read their value from standard input when given `-` (`invoice` of `order new`,
`order take-sell`, `order add-invoice` and `bond add-invoice`; see
[Invoice on standard input](../invocation.md#invoice-on-standard-input)), and
`"x-positional": N` on the properties passed as positional arguments, in the order of `N`
(0-based), after the command path (`key` and `value` of [config set](config_set.md); see
[Positional arguments](../invocation.md#positional-arguments)). `x-positional` is after
0.17.0, not yet released.

### GlobalOption

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Long option name without dashes: `output`, `reply-timeout` |
| `type` | string | Value type on the command line (`string`) |
| `description` | string | Help text, with the range and default |
| `enum` | array of string | Allowed values, when the option has a fixed set (`output`); absent otherwise |
| `default` | string | Default value as text (`"15"` for `reply-timeout`); absent when there is none |
| `applies_to` | array of string | Canonical names of the commands the option takes effect on, sorted |

## Outcomes

| Case | status | code | Stages |
| --- | --- | --- | --- |
| Described | `ok` | | `not_applicable` ×3 |
| An option was given | `error` | `invalid_arguments` (exit 2) | `not_applicable` ×3 |
| Could not serialize | `error` | `internal_error` | `not_applicable` ×3 |

## Using it in a wrapper

```sh
# names of JSON commands and the codes each can fail with
mostro-cli --output json schema | jq -r '
  .data.commands[] | select(.output_schema != null) |
  "\(.name): \([.output_schema.oneOf[] | .properties.error.properties.code.enum? // empty] | add | unique | join(", "))"'
```

Check at start-up that every command your wrapper uses is present with `"json"` in
`output_modes`; refuse to run against an older binary instead of failing mid-trade.

## Examples

{{#include ../../generated/schema.md}}

## Next

[Command index](README.md) · [order list](order_list.md)
