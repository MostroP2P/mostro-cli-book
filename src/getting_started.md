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
| Proof of work | `POW` | `--pow BITS` (`-p`) | no | Bits of PoW to put on requests, 0-255, default 0 |
| Transport | `TRANSPORT` | `--transport nip44` (`-t`) | no | Only `nip44` (protocol v2) is supported |
| Data directory | `MCLI_DIR` | — | no | Where `mcli.db` lives; default `~/.mcli` |

A root option overrides its environment variable. An **empty or invalid** option does not
fall back to the environment: it fails with `configuration_invalid`. Root options go
**before** the command (`mostro-cli --relays wss://a order list`), while `--output` may go
anywhere.

```sh
export MOSTRO_PUBKEY=<hex public key of the Mostro node you trade with>
export RELAYS=wss://relay.example.com,wss://relay2.example.com
mostro-cli --output json order list
```

The examples in this book assume `MOSTRO_PUBKEY` and `RELAYS` are exported.

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
