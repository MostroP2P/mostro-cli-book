# Schema files

All in `schemas/`. Regenerate with `scripts/refresh_schemas.sh` from any binary.

| File | Origin | Content |
| --- | --- | --- |
| `discovery.json` | `mostro-cli --output json schema` | The full discovery envelope (all commands) |
| `<command>.input.json` | `.data.commands[].input_schema` | Options of one command |
| `<command>.output.json` | `.data.commands[].output_schema` | The envelope of one command, all statuses |
| `envelope-v1.json` | Written for this book | Any command's envelope; for first-pass checks and legacy rejections |

Commands with schemas: `bond.add-invoice`, `dispute.open`, `identity.init`,
`identity.show`, `message.list`, `order.add-invoice`, `order.cancel`, `order.chat`, `order.fiat-sent`,
`order.info`, `order.list`, `order.mine`, `order.new`, `order.rate`, `order.release`,
`order.sync`, `order.take-buy`, `order.take-sell`, `order.watch`, `schema`.

## Anatomy of an output schema

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "...",
  "type": "object",
  "required": [ all seven envelope keys ],
  "properties": { generic envelope },
  "oneOf": [
    { "title": "success", ... status ok, data: <DataType>, allowed stages },
    { "title": "failure of the resolved command", ... status error, error.code enum, allowed stages },
    { "title": "uncertain outcome of the resolved command", ... (write commands only) },
    { "title": "failure before the command was resolved", ... command null, invalid_arguments }
  ],
  "$defs": { DataType, OrderRecord, ErrorCode, WarningCode, ExecutionMeta, ... }
}
```

Facts encoded there and nowhere else in such detail:

- the error codes each status may carry, per command;
- the exact stage combinations per status;
- patterns of every string (UUID, hex, decimal, RFC 3339, reason);
- `$defs/WarningCode`: the warnings a command may emit.

## Validating in code

```python
import json
from jsonschema import Draft202012Validator

schema = json.load(open("schemas/order.take-sell.output.json"))
Draft202012Validator(schema).validate(envelope)
```

```ts
import Ajv2020 from "ajv/dist/2020";
const validate = new Ajv2020({ strict: false }).compile(schema);
if (!validate(envelope)) console.error(validate.errors);
```

`strict: false` is needed with Ajv because input schemas use the extension keywords
`x-case-insensitive` and `x-stdin`.

The files in `schemas/` list only the `next_step` values and payload kinds of the binary they
were generated from; both enums are open within version 1 ([Envelope](../envelope.md)). To
validate a newer binary's `message.list` or `order.watch` output, use that binary's
`mostro-cli --output json schema`, or allow unknown values of those two enums.

## Drift

The CLI repository checks its own copies (`docs/schemas/*-v1.json`) against the generator
in CI. This book's copies are refreshed by hand; after an upgrade, rerun
`scripts/refresh_schemas.sh` and `scripts/validate_examples.py`.
