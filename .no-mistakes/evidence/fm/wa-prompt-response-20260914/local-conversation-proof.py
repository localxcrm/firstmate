"""Run from the candidate worktree with the local media Python environment.
Only fixture messages, injected STT and simulated transport; no installed account.
"""
import json
import hashlib
import base64
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'tests'))
from fm_whatsapp_test import WhatsAppTests, Simulator, poll, Store

out = Path(__file__).parent
report = {'scope': 'Local executable interfaces only; fixture main, simulated transport and receipts, injected STT over a generated tone. No real recipient or real speech recognition.', 'trials': []}
for mode in ('text', 'voice'):
    case = WhatsAppTests()
    case.setUp()
    started = time.monotonic()
    try:
        sample = case.dir / 'sample.txt'
        sample.write_text('one\ntwo\nthree\n')
        instruction = 'Conte as linhas do arquivo local'
        if mode == 'text':
            row = case.receive(case.message(instruction))
        else:
            audio = case.ogg_bytes()
            row = case.process_attachment('audio', {'id': 'voice-proof', 'mime_type': 'audio/ogg', 'voice': True, 'sha256': base64.b64encode(hashlib.sha256(audio).digest()).decode()}, audio, 'audio/ogg', transcriber=lambda path: instruction)
        row, claim = case.claim(row)
        assert claim['fresh_claim']
        claimed_ms = round((time.monotonic() - started) * 1000)
        case.emit(row, 'started', 'Análise iniciada', task=case.task())
        body = f'O arquivo tem {len(sample.read_text().splitlines())} linhas.'
        emitted = case.emit(row, 'completed', body, evidence=[str(sample)], task=case.task())
        ack = subprocess.run([str(ROOT / 'bin/fm-inbox.sh'), 'drain', '--ack', row['note_id']], env=case.config.environment(), capture_output=True, text=True, check=True)
        case.bridge.transport = Simulator(case.store, case.fixture)
        while case.bridge.send_one():
            pass
        sent = [json.loads(r['payload']) for r in case.store.rows('SELECT payload FROM sim_sends ORDER BY seq')]
        assert sent[-1]['text']['body'] == body
        assert all(p['type'] == 'text' for p in sent)
        final = case.store.rows('SELECT * FROM outbox WHERE event=?', (emitted['event'],))[-1]
        status = {'id': final['wamid'], 'status': 'delivered', 'timestamp': str(int(time.time())), 'recipient_id': 'user:owner'}
        case.bridge.ingest(poll(statuses=[status], offset=int(case.store.get('cursor')) + 1))
        reopened = Store(case.config)
        try:
            final_state = reopened.rows('SELECT state,wamid FROM outbox WHERE event=?', (emitted['event'],))[-1]
            assert final_state['state'] == 'delivered'
            snapshot = reopened.snapshot()
        finally:
            reopened.db.close()
        assert not list((case.home / 'state/inbox').glob('*.note'))
        assert len(list((case.home / 'state/inbox/handled').glob('*.note'))) == 1
        trial = {'input_kind': mode, 'input_wamid': row['wamid'], 'request': row['request'], 'note_id': row['note_id'], 'claim': {'fresh_claim': claim['fresh_claim'], 'text': claim['text'], 'transcript': (claim.get('attachment') or {}).get('transcript')}, 'simulated_recipient_messages': sent, 'persisted_after_reopen': snapshot, 'simulated_final_receipt': status, 'note_acknowledged': True, 'observed_local_claim_ms': claimed_ms, 'observed_local_total_ms': round((time.monotonic() - started) * 1000)}
        report['trials'].append(trial)
    finally:
        case.tearDown()
(out / 'local-conversation-proof.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
for trial in report['trials']:
    print(json.dumps({k: trial[k] for k in ('input_kind', 'request', 'claim', 'simulated_recipient_messages', 'simulated_final_receipt', 'observed_local_total_ms')}, ensure_ascii=False))
