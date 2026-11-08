# Invoking the CLI

## Selecting JSON

`--output human|json` is a global option. It defaults to `human`, is case-sensitive, and
may appear at any depth of the command path, with a space or `=`:

```sh
mostro-cli --output json order list
mostro-cli order --output=json list
mostro-cli order list --output json
```

All three are equivalent. Rules a wrapper must respect:

| Situation | Result |
| --- | --- |
| Exactly one `--output json` | JSON mode |
| No `--output`, or one `--output human` | Human mode |
| `--output` given twice, even with the same value | Exit 2, **empty stdout**, one line on stderr |
| `--output` with no value or an unknown value | Exit 2, **empty stdout**, one line on stderr |
| `--output json` appears inside another option's value (`--currency=--output=json`) | Not an output selection |
| `--output` after `--` | Not an output selection; an earlier `--output json` still holds |
| `--help` / `--version` | Conventional text and exit 0, even with `--output json` |

So: **put `--output json` exactly once, first**, and never pass user-controlled text
where an option is expected. Build `argv` as an array, never by string concatenation
through a shell.

## Confirmation: `--yes`

Commands that publish a request which changes something (`order new`, `order take-sell`,
`order take-buy`, `order add-invoice`, `bond add-invoice`, `order fiat-sent`,
`order release`, `order cancel`, `dispute open`, `order rate`) ask for confirmation in human
mode. In JSON mode **there is no prompt**; instead `--yes` is mandatory:

```sh
mostro-cli --output json order cancel --order 00000000-0000-0000-0000-000000000001
# exit 2, invalid_arguments: nothing was done

mostro-cli --output json order cancel --order 00000000-0000-0000-0000-000000000001 --yes
```

`--yes` is the caller's statement that the user consented. An agent should only add it
after it has obtained that consent (see [Guide for AI agents](wrapper/ai_agents.md)).

`order sync` writes only local rows and publishes nothing; it does not take `--yes`.
Neither do the local commands `identity init`, `identity show` and `order mine`.

## Invoice on standard input

The four commands that take an invoice (`order new`, `order take-sell`,
`order add-invoice`, `bond add-invoice`) also accept `--invoice -` (or `--invoice=-`): the
invoice is then read from standard input instead of the command line, where other local
users could see it in the process list.

```sh
printf '%s\n' "$INVOICE" | mostro-cli --output json order add-invoice \
  --order 00000000-0000-0000-0000-000000000001 --invoice - --yes
```

| Rule | Otherwise |
| --- | --- |
| `--yes` is given | `invalid_arguments`, exit 2, stdin not read |
| stdin is not a terminal | `invalid_arguments`, exit 2, stdin not read |
| At most 8192 bytes of UTF-8 holding exactly one non-empty line (ASCII whitespace around it is trimmed), then end of input: **close stdin** after the line | `invalid_arguments` with `reason: invalid_invoice`, exit 2, before any effect |

The line is then validated like a literal `--invoice` value. The error message is fixed text
and never contains what was read. `mostro-cli schema` marks these properties with
`"x-stdin": "-"`.

## Streams

With JSON selected, a controlled outcome is:

- **stdout**: exactly one UTF-8 JSON object followed by `\n`. No banner, progress, colour
  or table before or after it.
- **stderr**: optional diagnostics in fixed English prose. With `--verbose` (`-v`, a root
  option) a command adds one line such as `verbose: order.take-sell ok` or
  `verbose: order.release reply_timeout`. Diagnostics never contain keys, invoices, relay
  URLs or argument values. A refused [config file](getting_started.md#the-config-file) adds
  one line `hint: <path>: <problem>` naming the file and the line, never its content. Do
  not parse stderr.
- **stdin**: read only for `--invoice -` (above); otherwise never read.

## Exit codes

| Exit | Meaning | Stdout |
| --- | --- | --- |
| 0 | `status` is `ok` | Envelope |
| 2 | `error.code` is `invalid_arguments` or `output_not_supported` | Envelope (when JSON intent was unambiguous) |
| 2 | Bad or duplicate `--output` | **Empty**; stderr line |
| 1 | Any other error, **and every `uncertain`** | Envelope |
| 1 | Serialization or write failure | An `internal_error` envelope if possible, otherwise empty |
| other | Crash or killed | No guarantee |

The exit code is a summary. The envelope is the detail: `uncertain` exits 1 like an error,
but it does not mean "nothing happened". Always read `status`.

If stdout is empty or not one JSON object, treat the run as **unknown**: for a read,
retrying is fine; for a write, check before retrying (see
[Recovering from uncertain outcomes](flows/uncertain.md)).

## Argument errors are still JSON

Once `--output json` was selected unambiguously, an argument error is reported as an
envelope, even if the command itself cannot be recognised:

```sh
mostro-cli --output json unknowncmd
```

```json
{{#include ../examples/general/unknown_command.json}}
```

_File: `examples/general/unknown_command.json` · exit 2 · captured_

`command` is `null` because the command could not be resolved. A recognised command keeps
its name even when its arguments are wrong:

```sh
mostro-cli --output json order list --side invalid
```

```json
{{#include ../examples/order.list/invalid_side.json}}
```

_File: `examples/order.list/invalid_side.json` · exit 2 · fixture_

The error never echoes the offending value; your wrapper knows what it passed.

## Removed spellings

The JSON-capable commands replaced old spellings (`listorders`, `neworder`, `takesell`,
`getdm`...). The old names are gone without aliases and fail as an unknown command
(`command: null`, `invalid_arguments`). See [Migration](reference/migration.md).

## Timeouts you should allow for

| Phase | Budget |
| --- | --- |
| Connect to relays | 10 s |
| Node-info probe (protocol version, PoW) | 3 s, best effort |
| Mining the request with the PoW the node advertises | milliseconds at 6 bits; at the 20-bit ceiling about 1.6 s on average and 5 s at worst on a laptop CPU, more on a slower machine |
| Public read until every relay sent EOSE | 15 s |
| Wait for the node's reply to a request | `--reply-timeout`, 15 s by default |
| Relay cleanup | 1 s (overrun is only a warning) |

With the default reply deadline, a wrapper timeout of **45 seconds** per run is comfortably
above the worst case; add whatever you add to `--reply-timeout`. If you kill the process
earlier, treat a write as uncertain.

### `--reply-timeout SECONDS`

A global option like `--output`, accepted at any depth: 5 to 300 seconds, default 15. It is
the deadline from publishing the request to the node's reply for the commands that wait for
one: `order new`, `order take-sell`, `order take-buy`, `order add-invoice`,
`order fiat-sent`, `order release`, `order cancel`, `order info`, `dispute open`,
`order rate` and `bond add-invoice`. Other commands accept it and ignore it; the public
reads keep their own limits.

```sh
mostro-cli --output json --reply-timeout 60 order take-buy \
  --order 00000000-0000-0000-0000-000000000001 --yes
```

A reply after the deadline is `reply_timeout` as before (`uncertain` for the writes,
`error` for `order info`), and the CLI never retries. A value outside the range is
`invalid_arguments`, exit 2. `mostro-cli schema` lists both global options with their
range, default and the commands they apply to (`data.global_options`).

## Running several commands

The CLI makes no promise about two write commands running at the same time against one
data directory (both may reserve trade indexes and update rows). Run write commands
**one at a time** per data directory; queue them in your wrapper. The JSON-capable commands
that talk to the node read `$MCLI_DIR/config` (the [config file](getting_started.md#the-config-file))
and never write it. `order list` reads nothing else in the data directory and `schema` never
touches it; `order info`, `message list`, `order mine` and `identity show` only read it.
`identity init` creates it.
