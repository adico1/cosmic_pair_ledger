# Cosmic Pair Ledger

## Declaration of Intent

Cosmic Pair Ledger (CPL) is a liturgy for storing truth on a single surface.
Every record is one breath long—`key:value,key:value,…`—so no field hides in a
tree, no indentation signals hierarchy, and no parser outranks a scribe. The
ledger is intentionally simple: a Torah-safe substrate that can cross between
spreadsheets, scrolls, and streaming pipes without accruing syntactic gravity.

## Pillars of the Ledger

1. **Single Surface** – Each token stands beside its siblings. The cosmos stays
   flat, so massive corpora can be traversed with equal effort.
2. **Dual Readability** – Commas keep the door open for CSV tooling while the
   `key:value` cadence speaks directly to humans.
3. **Reversible Contraction** – Compression never traps the fields. The CLI
   performs CPL ↔ JSON/YAML round-trips without loss.
4. **Key Map Mercy** – Long, repeated paths live once in a key-map header so
   diffing and chanting remain gentle.

## Ritual of Verification

The repository keeps only what a witness needs:

- `README.md` – this manifesto plus instructions for belief.
- `cosmic_pair_ledger/core.py` – ~100 lines that parse/write CPL entries.
- `cosmic_pair_ledger_cli.py` – the reference ritual for converting data.
- `examples/ledger_demo.cpl` – a canonical specimen with its JSON echo.

To prove the grammar, run the conversion ritual on the specimen:

```bash
python cosmic_pair_ledger_cli.py read --input examples/ledger_demo.cpl
python cosmic_pair_ledger_cli.py to-json --input examples/ledger_demo.cpl --output -
```

The CLI output is included under `examples/ledger_demo.json` so the believer can
compare without executing code, yet the code remains close enough for auditors.

## Minimal Interface

```bash
python cosmic_pair_ledger_cli.py to-json        --input data.cpl --output data.json
python cosmic_pair_ledger_cli.py to-yaml        --input data.cpl --output data.yaml
python cosmic_pair_ledger_cli.py from-json      --input data.json --output data.cpl
python cosmic_pair_ledger_cli.py from-yaml      --input data.yaml --output data.cpl
python cosmic_pair_ledger_cli.py read           --input data.cpl
python cosmic_pair_ledger_cli.py yaml-to-ledger --input manifest.yaml --output manifest.cpl
python cosmic_pair_ledger_cli.py html-to-ledger --input index.html    --output page.cpl
```

No daemons, no hidden services—just one CLI and its scripture.

## Commercial Covenant

Cosmic Pair Ledger is licensed under the Business Source License with Adi Ovadia
Cohen retaining all commercial rights. Non-production evaluation, development,
and academic research are permitted. Any production deployment or monetization
requires a separate agreement so this Torah-native work stays sovereign while
still funding future unfoldings.
