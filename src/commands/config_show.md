# config show

> After 0.17.0, not yet released: mostro-cli 0.17.0 has no `config` command and reads no
> config file. With 0.17.0, pass the node settings as options or environment variables.

| | |
| --- | --- |
| `command` | `config.show` |
| Kind | Local read |
| Needs | Nothing. `MCLI_DIR` or the home directory locates the file. No `MOSTRO_PUBKEY`, `RELAYS`, identity, stdin or `--yes` |
| Publishes | Nothing; contacts no relay or node |
| Local write | None: no file or directory is created or changed |
| Statuses | `ok`, `error` |
| Schemas | `schemas/config.show.input.json`, `schemas/config.show.output.json` |

Reports the [config file](../getting_started.md#the-config-file)'s path
(`$MCLI_DIR/config`, else `~/.mcli/config`) and the four node settings stored in it. Use it
to check what [config set](config_set.md) or a hand-written file left there, or which line a
`configuration_invalid` points at.

## Invocation

```text
mostro-cli --output json config show
```

## Input

None. An argument or an option of its own (`--yes` included) is `invalid_arguments`
(exit 2). Root options such as `--mostro-pubkey` or `--relays` are accepted and ignored.
Neither they nor the environment variables are reported: the outcome says what the file
holds, not which value a command would use.

## Behavior

1. Locates the data directory (`MCLI_DIR`, else `.mcli` in the home directory) and reads
   `config` in it strictly, as [config set](config_set.md) does.
2. No file, or no data directory, is not a problem: the outcome is `ok`, `path` names
   where the file would be and every value is `null`. When no data directory can be
   determined, or its path is not UTF-8, `path` is `null` too.
3. A file the commands refuse (another key such as `ADMIN_NSEC`, a line that is not
   `KEY=VALUE`, a refused value, not a readable UTF-8 file), or one the process cannot
   reach (a data directory it may not look into, a `config` that is a directory), is
   `configuration_invalid` (exit 1), never a set of nulls. Stderr then has one line naming
   the file and the problem, and the line when a line is at fault, never the file's
   content; control characters in the path are escaped:

   ```text
   hint: /home/alice/.mcli/config: line 2 sets a key other than MOSTRO_PUBKEY, RELAYS, POW or TRANSPORT
   ```

4. Otherwise each value is reported as the commands read it: an `export ` prefix and one
   pair of quotes removed, trimmed, the last of repeated lines; an empty value is `null`.
   Comments and blank lines are not reported.

It never creates the data directory or any file in it, never opens `mcli.db`, never reads
stdin or `ADMIN_NSEC` and connects to nothing.

A value it shows is used only when neither the root option nor a set environment variable
gives that setting, even an empty one (see the precedence in
[Configure the node](../getting_started.md#configure-the-node)). When a command does not
use a value the file holds, look for a variable the environment still sets.

The values it returns are ones the commands accept: a key, relay URLs, a number or `nip44`.
This is not a secrecy promise: a private key written as 64 hex characters can pass the
public key check, and it would then be shown. Relay URLs appear as stored.

In human mode it prints the file's path, with control characters escaped, and each setting
or `not set`:

```text
Config file: /home/alice/.mcli/config
MOSTRO_PUBKEY: not set
RELAYS: wss://relay.example.com,wss://relay2.example.com
POW: 3
TRANSPORT: not set
```

A `null` path prints `Config file: unknown (no data directory, or its path is not UTF-8)`.
With `--verbose`, stderr adds `verbose: config.show ok` (or the error code). An error prints
`error: <message>` on stderr, after the `hint:` line when the file was refused.

## Success data: `ConfigData`

The same type as the data of [config set](config_set.md#success-data-configdata).

| Field | Type | Meaning |
| --- | --- | --- |
| `path` | string or null | The config file's path, whether or not it exists; `null` when no data directory can be determined or its path is not UTF-8 |
| `mostro_pubkey` | string or null | `MOSTRO_PUBKEY` as stored in the file; `null` when absent or empty |
| `relays` | string or null | `RELAYS` as stored, the list as written (trimmed, spacing kept); `null` when absent or empty |
| `pow` | string or null | `POW` as stored: a number as text (`"3"`), not a JSON number; `null` when absent or empty |
| `transport` | string or null | `TRANSPORT` as stored (`"nip44"`); `null` when absent or empty |

Values are not normalized: an `npub` stays an `npub`.

## Outcomes

| Case | status | code | Stages |
| --- | --- | --- | --- |
| File read, or no file | `ok` | | `not_applicable` ×3 |
| An argument or an option of its own was given | `error` | `invalid_arguments` (exit 2) | `not_applicable` ×3 |
| The file is refused or cannot be reached (with the `hint:` line) | `error` | `configuration_invalid` | `not_applicable` ×3 |

## Errors

`invalid_arguments`, `configuration_invalid`, `internal_error`. Nothing is published or
written in any case. After `configuration_invalid`, fix what the `hint:` line names (the
line at fault, or a file or data directory the process cannot read) by hand:
[config set](config_set.md) refuses the same file and never repairs it.

## Warnings

None. The schema's shared `WarningCode` list names `invalid_event_timestamp` and
`cleanup_incomplete`, but this command emits no warning.

## Examples

{{#include ../../generated/config_show.md}}

## Next

[config set](config_set.md) changes one value. Once `MOSTRO_PUBKEY` and `RELAYS` are there,
[order list](order_list.md) and the other networked commands run without `-m` or `-r`.
