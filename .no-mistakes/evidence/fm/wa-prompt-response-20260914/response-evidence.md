# WhatsApp response evidence

Validated commit: `f272cb7ec52fafe6ba785afb3a9a731f3a6ba1be`.

## Real Pi, synthetic inbox

Pi 0.85.1 with openai-codex/gpt-5.6-sol used the real lock, watcher, native extension, inbox drain and acknowledgements. No WhatsApp account or API was used.

| Arrival | Synthetic incoming question | Actual model answer | Intake to answer |
| --- | --- | --- | --- |
| Initial idle | 17 + 25 | 42 | 7.512 s |
| Idle successor | 23 + 14 | 37 | 7.900 s |
| During controlled busy tool | 31 - 12 | 19 | 8.286 s |

The busy arrival was delivered as a native followUp while the original tool remained held. The test then released that tool; each note received one answer and its generation-bound acknowledgement. These timings are observed samples, not an SLA or WhatsApp end-to-end latency.

## Simulated WhatsApp transport, real persistence and CLI

Account, media download and delivery receipts are fixtures. Media decoding uses real local tools; speech transcription is injected. Main claim/emit runs through the authenticated public CLI using a structural harness fixture, with no model interpretation.

### test_real_inbox_main_result_and_delivery

```json
{
  "messaging_product": "whatsapp",
  "text": {
    "body": "Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.",
    "preview_url": false
  },
  "to": "user:owner",
  "type": "text"
}
```

```json
{
  "messaging_product": "whatsapp",
  "text": {
    "body": "Análise iniciada",
    "preview_url": false
  },
  "to": "user:owner",
  "type": "text"
}
```

```json
{
  "messaging_product": "whatsapp",
  "text": {
    "body": "O arquivo tem 3 linhas.",
    "preview_url": false
  },
  "to": "user:owner",
  "type": "text"
}
```

Persisted output:

```json
[
  {
    "request": "wa-cd9a792e6ec32fed0c1fa60513878024",
    "body": "Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.",
    "state": "accepted",
    "wamid": "wamid.simulated.1"
  },
  {
    "request": "wa-cd9a792e6ec32fed0c1fa60513878024",
    "body": "Análise iniciada",
    "state": "accepted",
    "wamid": "wamid.simulated.2"
  },
  {
    "request": "wa-cd9a792e6ec32fed0c1fa60513878024",
    "body": "O arquivo tem 3 linhas.",
    "state": "accepted",
    "wamid": "wamid.simulated.3"
  }
]
```

### test_voice_transcript_to_correlated_text_and_delivered_receipt

```json
{
  "messaging_product": "whatsapp",
  "text": {
    "body": "Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.",
    "preview_url": false
  },
  "to": "user:owner",
  "type": "text"
}
```

```json
{
  "messaging_product": "whatsapp",
  "text": {
    "body": "A nota transcrita contém 4 palavras.",
    "preview_url": false
  },
  "to": "user:owner",
  "type": "text"
}
```

Persisted output:

```json
[
  {
    "request": "wa-cd9a792e6ec32fed0c1fa60513878024",
    "body": "Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.",
    "state": "accepted",
    "wamid": "wamid.simulated.1"
  },
  {
    "request": "wa-cd9a792e6ec32fed0c1fa60513878024",
    "body": "A nota transcrita contém 4 palavras.",
    "state": "delivered",
    "wamid": "wamid.simulated.2"
  }
]
```

### test_native_video_frames_and_correlated_text_reply

```json
{
  "messaging_product": "whatsapp",
  "text": {
    "body": "Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.",
    "preview_url": false
  },
  "to": "user:owner",
  "type": "text"
}
```

```json
{
  "messaging_product": "whatsapp",
  "text": {
    "body": "Os quadros amostrados mostram vermelho.",
    "preview_url": false
  },
  "to": "user:owner",
  "type": "text"
}
```

Persisted output:

```json
[
  {
    "request": "wa-cd9a792e6ec32fed0c1fa60513878024",
    "body": "Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.",
    "state": "accepted",
    "wamid": "wamid.simulated.1"
  },
  {
    "request": "wa-cd9a792e6ec32fed0c1fa60513878024",
    "body": "Os quadros amostrados mostram vermelho.",
    "state": "accepted",
    "wamid": "wamid.simulated.2"
  }
]
```

## Counterfactual regression

The current `test_inbox_arrival_reaches_handling_successor` was executed with only WATCH redirected to the watcher from base commit `a6618ddc690b4e613b62c6c4a3f6df4808a778b1`. It failed with `running handling successor left the durable inbox note silent`. The same test on the target passed, including a keyed retry and a subsequent plain-text note.

## Acceptance still pending

The installed user account needs fresh text and real spoken-audio trials while its main is idle and busy, without intervention in a separate chat. Correlate incoming message, transcription, note, claim, substantive text response, outbound wamid and recipient delivery. Preserve the current account, history, cursor and single consumer. Record observed phase latency and representative image/document/video behavior before permanent activation.

No WhatsApp screenshot was captured: this isolated test phase used synthetic transport and did not open or activate the installed account. JSON payloads and the native event timeline are the actual exercised surfaces.

## Reproduction and setup

Create an isolated venv, install `bin/requirements-whatsapp-media.txt`, and run `run_whatsapp_checks.py` from the worktree. The script lists every selected case and retains protocol output. An initial selector typo and a missing checksum in the added voice fixture were corrected; the final 26 focused cases completed without failures or skips. No product code changes were needed.

Native proof: `FM_PI_INBOX_LIVE_E2E=1 FM_PI_INBOX_EVIDENCE=<evidence>/pi-native PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.no-mistakes/test-tmp" bash tests/fm-inbox-pi-live-e2e.test.sh`.

Watcher checks: `bash tests/fm-watch-triage.test.sh test_inbox_arrival_reaches_handling_successor test_inbox_and_process_results_share_check_delivery test_procevent_captured_result_surfaces_proactively test_procevent_surface_crash_boundaries test_procevent_marker_failure_exits_and_replays`. The runner also executes six baseline classifier checks. Broken-pipe and killed-process output in crash cases was expected fault injection.
