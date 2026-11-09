# config set

> After 0.17.0, not yet released: mostro-cli 0.17.0 has no `config` command and reads no
> config file. With 0.17.0, pass the node settings as options or environment variables.

| | |
| --- | --- |
| `command` | `config.set` |
| Kind | Local write |
| Needs | `MCLI_DIR` or a home directory. No `MOSTRO_PUBKEY`, `RELAYS`, identity, stdin or `--yes` |
| Publishes | Nothing; contacts no relay or node |
| Local write | Creates the data directory or makes it owner-only; rewrites `config` and keeps its lock file `.config.lock` beside it; never touches `mcli.db` |
| Statuses | `ok`, `error` |
| Schemas | `schemas/config.set.input.json`, `schemas/config.set.output.json` |

Writes one node setting to the [config file](../getting_started.md#the-config-file)
(`$MCLI_DIR/config`, else `~/.mcli/config`) and keeps the other settings stored there. Run
it once per setting when deploying, instead of writing the file by hand; every later
command then finds the node key and the relays without `-m` or `-r`.

## Invocation

```text
mostro-cli --output json config set <mostro-pubkey|relays|pow|transport> <VALUE>
```

```sh
mostro-cli --output json config set mostro-pubkey <hex or npub public key of the node>
mostro-cli --output json config set relays wss://relay.example.com,wss://relay2.example.com
```

The key and the value are positional arguments after the command path, not options. Put
`--` before a value that starts with `-`: without it the value is read as an option and the
call fails with `invalid_arguments` (exit 2), or, when it looks like `--output`, with an
empty stdout. A program that passes user data can always put `--` right after the command
path (`config set -- relays <value>`): everything after it is positional.

Root options such as `--mostro-pubkey` or `--relays` are accepted and ignored, and the node
settings of the environment play no part: only the given value is written.

## Input

| Property | Position | Type | Meaning |
| --- | --- | --- | --- |
| `key` | 0 | enum `mostro-pubkey`, `relays`, `pow`, `transport` | The setting to write |
| `value` | 1 | string | Its value, trimmed and checked as the commands check it |

Both are required. In the input schema they carry `"x-positional": 0` and `"x-positional": 1`
(see [Positional arguments](../invocation.md#positional-arguments)).

| `key` | Line written | Accepted value |
| --- | --- | --- |
| `mostro-pubkey` | `MOSTRO_PUBKEY=...` | A public key: 64 hex characters or `npub` |
| `relays` | `RELAYS=...` | Comma-separated `ws://` or `wss://` relay URLs |
| `pow` | `POW=...` | A number from 0 to 255 |
| `transport` | `TRANSPORT=...` | `nip44` |

An empty value (after trimming), a value with a control character inside it (a newline
between two URLs, for instance) or a value its setting refuses (an `nsec`, an `https://`
URL, `256`, `gift-wrap`) is `invalid_arguments` (exit 2), and so are another key
(`admin-nsec`, `MOSTRO_PUBKEY` in capitals), a missing value, an extra argument and
`--yes`. Nothing is read or written then, and the value is never echoed, in either mode.
No command removes a setting: delete its line from the file by hand.

## Behavior

1. Checks the key and the value. A refusal stops here.
2. Reads the existing `config` strictly. A file the commands refuse (another key such as
   `ADMIN_NSEC`, a line that is not `KEY=VALUE`, a refused value, not a readable UTF-8
   file), or one the process cannot reach (a data directory it may not look into), is
   `configuration_invalid` (exit 1) with one stderr line naming the file and the problem,
   and the line when a line is at fault, never the file's content. The file and the data
   directory are left as they were. A missing file or data directory is not a problem.

   ```text
   hint: /home/alice/.mcli/config: line 2 sets a key other than MOSTRO_PUBKEY, RELAYS, POW or TRANSPORT
   ```

3. Creates the data directory, one level deep and owner-only (`0700` on Unix), or makes an
   existing one owner-only, as `identity init` does. When no data directory can be
   determined (no `MCLI_DIR` and no home directory) or it cannot be created (its parent does
   not exist, a file is in its place), the outcome is `configuration_unwritable` and nothing
   is written.
4. Takes an exclusive lock on `.config.lock` in the data directory (an empty owner-only
   file, kept afterwards), reads `config` again and replaces it atomically: an owner-only
   (`0600` on Unix) temporary file `.config.<pid>.tmp` is written, synced and renamed over
   `config`. A temporary file of the same name left by an earlier crashed run is removed
   first. Runs of `config set` at the same time wait for each other's lock, so none of
   their changes is lost (for one key, the last run wins).
5. The new file has one `NAME=value` line per stored setting, in the order
   `MOSTRO_PUBKEY`, `RELAYS`, `POW`, `TRANSPORT`. The other settings keep their values as
   stored (quotes and an `export ` prefix removed); comments, blank lines, a byte order
   mark and repeated lines are dropped. A `config` that is a symlink is replaced by a
   regular file; its target is not changed.
6. When the write or the rename fails, the temporary file is removed and the old `config`
   is intact (`configuration_unwritable`, `persistence: failed`). After either
   `configuration_unwritable`, the data directory may already have been created or made
   owner-only, with an empty `.config.lock` in it.

It never opens or creates `mcli.db`, never reads `ADMIN_NSEC` and connects to nothing.

A value written here is used only when neither the root option nor a set environment
variable gives that setting (see the precedence in
[Configure the node](../getting_started.md#configure-the-node)).

On Windows the default data directory is `.mcli` in the profile folder (normally
`%USERPROFILE%\.mcli`), and no Unix file modes are set.

The values it writes and returns are ones the commands accept: a key, relay URLs, a number
or `nip44`. An `nsec` is refused, but this is not a secrecy promise: a private key written
as 64 hex characters can pass the public key check, and it would then be stored and shown.
Never pass a secret. Relay URLs appear in `data` as given.

In human mode a success prints the file's path and each setting stored after the write,
with control characters in the path escaped:

```text
Config file: /home/alice/.mcli/config
MOSTRO_PUBKEY: not set
RELAYS: wss://relay.example.com,wss://relay2.example.com
POW: 3
TRANSPORT: not set
```

With `--verbose`, stderr adds `verbose: config.set ok` (or the error code). An error prints
`error: <message>` on stderr, after the `hint:` line when the file was refused; an unknown
key or a missing value prints the argument parser's own message, which does not repeat the
value.

## Success data: `ConfigData`

| Field | Type | Meaning |
| --- | --- | --- |
| `path` | string or null | The config file's path; `null` only when the data directory's path is not UTF-8 |
| `mostro_pubkey` | string or null | `MOSTRO_PUBKEY` as stored in the file after the write; `null` when absent |
| `relays` | string or null | `RELAYS` as stored, the list as given (trimmed, spacing kept); `null` when absent |
| `pow` | string or null | `POW` as stored: a number as text (`"3"`), not a JSON number; `null` when absent |
| `transport` | string or null | `TRANSPORT` as stored (`"nip44"`); `null` when absent |

Values are not normalized: an `npub` stays an `npub`.

## Outcomes

| Case | status | code | Stages (publication / daemon / persistence) |
| --- | --- | --- | --- |
| Setting written | `ok` | | not_applicable / not_applicable / applied |
| Unknown key, missing or extra argument, refused or empty value | `error` | `invalid_arguments` (exit 2) | not_applicable ×3 |
| The existing file is refused or cannot be reached (with the `hint:` line); nothing changed | `error` | `configuration_invalid` | not_applicable / not_applicable / not_attempted |
| No data directory can be determined, or the directory, the lock or the temporary file cannot be created | `error` | `configuration_unwritable` | not_applicable / not_applicable / not_attempted |
| The write or the rename failed; the old file is intact | `error` | `configuration_unwritable` | not_applicable / not_applicable / failed |

## Errors

`invalid_arguments`, `configuration_invalid`, `configuration_unwritable`, `internal_error`.
Nothing is published in any case. Only this command emits `configuration_unwritable`
([catalogue](../errors.md)): make `MCLI_DIR` (else `~/.mcli`) a directory you own on a disk
with free space, then run it again. After `configuration_invalid`, fix or delete the line
the `hint:` names; `config set` never repairs a refused file.

## Warnings

None. The schema's shared `WarningCode` list names `invalid_event_timestamp` and
`cleanup_incomplete`, but this command emits no warning.

## Examples

{{#include ../../generated/config_set.md}}

## Next

Once `mostro-pubkey` and `relays` are set, [order list](order_list.md) and the other
networked commands run without `-m` or `-r`. [identity init](identity_init.md) creates the
identity the signing commands need.
