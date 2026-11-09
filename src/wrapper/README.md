# Writing a wrapper

A wrapper turns "run a process, read stdout" into function calls. The contract makes this
simple if the wrapper follows a few rules. Complete, tested wrappers are in `wrappers/`:
[Python](python.md), [TypeScript](typescript.md), [Rust](rust.md), [Shell](shell.md).
They keep stdin closed, so they pass invoices on the command line; to use `--invoice -`,
pipe stdin as in step 2 below.

## The algorithm

```text
1. argv = [binary, "--output", "json", ...command path, ...options]   # array, no shell
   + "--yes" for the commands that take it, only with the user's consent
2. spawn with a timeout (≈45 s, plus whatever --reply-timeout adds over 15 s),
   environment with MOSTRO_PUBKEY/RELAYS
   with --invoice - or --invoice=-: pipe stdin, write the invoice line, then close stdin
   otherwise: stdin closed
3. if spawn failed                     → TransportError(may_have_acted = false)
   if timeout                          → TransportError(may_have_acted = is_write)
   (order chat --message counts as a write here: relays only, never the node; allow it 90 s)
4. stdout.strip() empty                → TransportError(may_have_acted = is_write and exit == 1)
   not one JSON object                 → TransportError(may_have_acted = is_write)
5. envelope.schema_version != "1"      → IncompatibleError
6. return envelope (+ exit code)       → caller branches on status, then error.code
```

## Rules

1. **Build argv as a list.** Never join a command string for a shell; values such as
   payment methods and invoices are user data.
2. **One `--output json`, placed first.** Never let user data land where an option is
   expected. For a value that could start with `-`, use the attached form
   `--payment-method=<value>`: the CLI never reads an output selection inside a value.
3. **Close stdin.** The CLI reads it only for `--invoice -` or `--invoice=-` (then write
   the invoice line and close it); otherwise a closed stdin makes sure a future version can never block on a
   prompt. Prefer `--invoice -` to a literal invoice: a command line is visible to other
   local users in the process list.
4. **Parse stdout, ignore stderr** (log it, do not parse it).
5. **Branch on `status`, then `error.code`.** Never on `message`. Keep a default branch for
   codes you do not know (within v1 new commands can add codes).
6. **Keep decimal strings as strings** or parse them as big integers.
7. **Never retry `uncertain` or a write transport failure automatically.** See
   [Recovering](../flows/uncertain.md).
8. **Serialise writes** per data directory.
9. **Discover once**: call `schema` at start-up; check every command you need is present
   with `"json"` in `output_modes`.
10. **Validate optionally**: the per-command output schemas are strict; validating in tests
    (or in debug builds) catches drift between your wrapper and a new binary.

## Surfacing results to a UI

| Envelope | Show |
| --- | --- |
| `ok` | The data; warnings as notes |
| `error` + `node_refused` | "The node refused: `<reason>`" |
| `error` (other) | A sentence per code (your own text; the CLI's `message` is acceptable as a fallback) |
| `uncertain` | "We could not confirm whether this happened. Checking…" then run the check |

## Testing a wrapper without a node

Many outcomes can be produced offline:

| Outcome | How |
| --- | --- |
| `invalid_arguments` (exit 2) | `order list --side x` |
| `command: null` | an unknown command |
| `output_not_supported` | any [human-only command](../commands/legacy.md) |
| `configuration_missing` | unset `MOSTRO_PUBKEY`/`RELAYS` |
| `configuration_invalid` | `--mostro-pubkey not-a-key` |
| `identity_missing` | `MCLI_DIR` pointing to an empty directory, valid config |
| `relay_connection_failed` | `--relays ws://127.0.0.1:1` (with an identity, for identity commands) |
| `schema` success | `schema` |

For the rest, feed your parser the files in `examples/` (all 147 are real-shaped envelopes;
`examples/index.json` gives the exit code to pair with each).
