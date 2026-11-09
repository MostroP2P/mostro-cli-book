# Getting started

## Install

mostro-cli 0.17.0 is the first release with the JSON interface. Install it from crates.io
(Rust 1.94 or later), or take a binary from the
[release page](https://github.com/MostroP2P/mostro-cli/releases/tag/v0.17.0):

```sh
cargo install --locked mostro-cli
mostro-cli --version              # mostro-cli 0.17.0
```

0.16.3 and earlier have no JSON interface: `mostro-cli --output json schema` is the check,
since only a build that has it answers.

## Discover what your binary supports

The `schema` command needs nothing: no configuration, no identity, no network. It is the
first thing a wrapper should call.

```sh
mostro-cli --output json schema | jq '.data.commands[] | select(.output_modes | index("json")) | .name'
```

```text
"bond.add-invoice"
"dispute.open"
"identity.init"
"identity.show"
"message.list"
"order.add-invoice"
"order.cancel"
"order.fiat-sent"
"order.info"
"order.list"
"order.mine"
"order.new"
"order.rate"
"order.release"
"order.sync"
"order.take-buy"
"order.take-sell"
"schema"
```

See [schema](commands/schema.md) for the full document.

## Configure the node

Every command except `schema`, `identity init`, `identity show` and `order mine` needs the
node's public key and the relays. `order list`, `message list` and `order sync` only read
events from the relays; the other commands also send the node one signed request through
them.

| Setting | Environment variable | Root option | Required | Meaning |
| --- | --- | --- | --- | --- |
| Node public key | `MOSTRO_PUBKEY` | `--mostro-pubkey KEY` (`-m`) | yes | The Mostro daemon to trade with, hex or `npub` |
| Relays | `RELAYS` | `--relays URL[,URL...]` (`-r`) | yes | Comma-separated `wss://` URLs |
| Proof of work | `POW` | `--pow BITS` (`-p`) | no | The least PoW put on requests, 0-255, default 0. The commands raise it to what the node advertises, up to 20 bits, so you rarely need it ([Proof of work](errors.md#proof-of-work)) |
| Transport | `TRANSPORT` | `--transport nip44` (`-t`) | no | Only `nip44` (protocol v2) is supported |
| Data directory | `MCLI_DIR` | — | no | Where `mcli.db` and the [config file](#the-config-file) live; default `~/.mcli` |

Each of the first four settings comes from its root option, even an empty one; else from its
environment variable when that is set, even to an empty value; else from the
[config file](#the-config-file). A value given in one place never falls back to the next.
An **empty** value counts as not given: an empty node key or relay list is
`configuration_missing`, an empty `POW` is 0 and an empty `TRANSPORT` means detect. An
**invalid** value (an unparsable key or relay URL, a `POW` outside 0-255, a transport other
than `nip44`) is `configuration_invalid`; `order list`, `message list` and `order sync`
send no request and do not look at `POW` or `TRANSPORT` given as an option or a variable
(a config file line is always checked). Root options go **before** the command
(`mostro-cli --relays wss://a order list`), while `--output` may go anywhere.

```sh
export MOSTRO_PUBKEY=<hex public key of the Mostro node you trade with>
export RELAYS=wss://relay.example.com,wss://relay2.example.com
mostro-cli --output json order list
```

The examples in this book assume `MOSTRO_PUBKEY` and `RELAYS` are exported or in the config
file.

### The config file

> After 0.17.0, not yet released: mostro-cli 0.17.0 reads no config file.

The JSON-capable commands that talk to the node (every one except `schema`,
`identity init`, `identity show` and `order mine`) also read the four node settings from
`config` in the data directory: `$MCLI_DIR/config`, else `~/.mcli/config`
(on Windows the profile folder, normally `%USERPROFILE%\.mcli\config`). A program that runs each command in a fresh
process, as coding agents and MCP hosts do, can write the settings there once instead of
passing `-m`, `-r` and `-p` on every call.

```sh
mkdir -m 700 -p ~/.mcli
cat > ~/.mcli/config <<'EOF'
# node settings of mostro-cli
MOSTRO_PUBKEY=<hex public key of the Mostro node you trade with>
RELAYS=wss://relay.example.com,wss://relay2.example.com
EOF
chmod 600 ~/.mcli/config
mostro-cli --output json order list
```

The format:

- One `KEY=VALUE` per line, with the variable names as keys. Blank lines and lines
  starting with `#` are skipped, an `export ` prefix is dropped, key and value are trimmed
  and one pair of matching `"` or `'` quotes around the value is removed. LF or CRLF; a
  leading byte order mark is ignored.
- No inline comments (a `#` after a value is part of the value), escapes or variable
  expansion.
- An empty value means unset. When a key is repeated, its last line wins.
- Only `MOSTRO_PUBKEY`, `RELAYS`, `POW` and `TRANSPORT`. Any other key, `ADMIN_NSEC` and
  `MOSTRO_RPC_TOKEN` included, refuses the file, so secrets stay in the environment.
- Every value is checked, by every command that reads the file: a key in hex or `npub`,
  `ws://` or `wss://` relay URLs, 0-255, `nip44`, no control character.

A file with another key, a line that is not `KEY=VALUE`, a value its setting refuses, or a
`config` that is not a readable UTF-8 file is refused **as a whole**: the command fails with
`configuration_invalid` (exit 1) after its own argument checks (an `invalid_arguments`
comes first) and before it touches the identity, the store or the network, even when the
options give every value. Stderr then has one line naming the file and the problem, with
the line number when a line is at fault, never the file's content:

```text
hint: /home/alice/.mcli/config: line 2 sets a key other than MOSTRO_PUBKEY, RELAYS, POW or TRANSPORT
```

When the file or the data directory does not exist, or the process may not look into the
directory, there is no file and nothing changes. Reading the file never creates the data
directory or anything in it. The [human-only commands](commands/legacy.md) do not read it
yet: give them `MOSTRO_PUBKEY` and `RELAYS` in the environment or with `-m` and `-r`.

## Create an identity

Commands that act for you (everything except `order list` and `schema`) need a local
identity: a BIP-39 mnemonic in `mcli.db` from which the identity key and one trade key per
order are derived. Only [`identity init`](commands/identity_init.md) creates it; the
other commands that need it fail with `identity_missing` instead. Create it once:

```sh
mostro-cli --output json identity init   # creates $MCLI_DIR (else ~/.mcli) and mcli.db
mostro-cli --output json identity show   # identity public key and last trade index
```

`identity init` needs no node, relay or `--yes`, publishes nothing and never prints the
mnemonic. If a store already exists it changes nothing and fails with `identity_exists`.

Back up `~/.mcli/mcli.db` (or the mnemonic in it). A copy of the database also carries your
in-flight trades; the mnemonic alone recovers the identity but not the local order rows.

## Your first calls

```sh
# public, read-only: no identity needed
mostro-cli --output json order list --side sell --currency USD

# ask the node about specific orders (needs the identity, writes nothing)
mostro-cli --output json order info --order 2b0c3f3e-6d0c-4b8e-9f0a-3c1d5e7f9a11

# what has the node told me lately?
mostro-cli --output json message list --since 120
```

In a program, always check three things after each run: the **exit code**, that stdout
parsed as **one JSON object**, and its **`status`**. The [wrapper chapter](wrapper/README.md)
shows complete code.

## What is not in JSON yet

Chat, the dispute conversation, `restore`, user info and the admin commands are human-only
today.
Asking them for JSON returns `output_not_supported` (exit 2) before anything runs. See
[Human-only commands](commands/legacy.md).
