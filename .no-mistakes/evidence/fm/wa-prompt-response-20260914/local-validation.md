# Local WhatsApp conversation evidence

Candidate: e951681bca106d9f7c0292406318a7131236f756.

Scope: independent disposable homes; real inbox CLI, authenticated fixture-main CLI, SQLite and local audio decoding. Transport, receipts and transcription are simulated. No installed account or real speech recognition was exercised.

## text

Input: Conte as linhas do arquivo local

Request: wa-cd9a792e6ec32fed0c1fa60513878024; note: key-8da0b03951e713f1bd788f90689b04a8c37805ac786fe26375b5b4b002a91f3b

- Simulated text output: Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.
- Simulated text output: Análise iniciada
- Simulated text output: O arquivo tem 3 linhas.

Simulated receipt: wamid.simulated.3 / delivered; persisted after SQLite reopen. Inbox note acknowledged and retained as handled.

Observed local claim: 399 ms; total: 703 ms. Fixture execution time, not WhatsApp latency or an SLA.

## voice

Input: Nota de voz recebida.

Conte as linhas do arquivo local

Request: wa-cd9a792e6ec32fed0c1fa60513878024; note: key-8da0b03951e713f1bd788f90689b04a8c37805ac786fe26375b5b4b002a91f3b

- Simulated text output: Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.
- Simulated text output: Análise iniciada
- Simulated text output: O arquivo tem 3 linhas.

Simulated receipt: wamid.simulated.3 / delivered; persisted after SQLite reopen. Inbox note acknowledged and retained as handled.

Observed local claim: 645 ms; total: 934 ms. Fixture execution time, not WhatsApp latency or an SLA.

## Regression and boundaries

The current test_inbox_arrival_reaches_handling_successor executed against an isolated executable copy of the base watcher failed: running handling successor left the durable inbox note silent. The candidate passes the same test, plus mixed inbox/process delivery and marker crash/replay cases. Deliberately induced broken-pipe and killed-process output occurred in passing crash cases.

All 17 selected WhatsApp tests passed without skips. Missing media dependencies were supplied in a temporary worktree virtual environment. The manual evidence driver initially supplied an invalid synthetic audio checksum; the envelope was corrected to Base64 and the proof passed. No candidate source change was required.

Manually inspected the complete verification document and HEAD diff: local validation/publication precedes main-owned controlled installation and real acceptance; permanent activation requires real idle/busy text and speech trials with substantive delivered replies, no separate-chat prompt, measured timing, preserved account/history/media, one consumer and reconciled supervisor delta.

Native Pi and installed WhatsApp trials were not rerun. Installed acceptance remains mandatory before permanent activation. No screenshot: the exercised interface was CLI/SQLite with simulated transport; this phase cannot operate the installed WhatsApp surface.
