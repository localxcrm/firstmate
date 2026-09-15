"""Focused public-interface checks with synthetic WhatsApp transport evidence.
Run from the gate worktree using its temporary media-enabled Python environment.
"""
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path.cwd()
OUT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('wa_tests', ROOT / 'tests/fm_whatsapp_test.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
records = []

class EvidenceChecks(m.WhatsAppTests):
    def setUp(self):
        super().setUp()
        self.observed = []

    def main(self, data, ok=True):
        result = super().main(data, ok)
        if self._testMethodName in CAPTURE:
            self.observed.append({'operation': data, 'result': result})
        return result

    def tearDown(self):
        try:
            if self._testMethodName in CAPTURE:
                records.append({
                    'scenario': self._testMethodName,
                    'main_protocol': self.observed,
                    'inbound': self.store.rows('SELECT request,wamid,kind,body,state,note_id FROM inbound ORDER BY rowid'),
                    'responses': self.store.rows('SELECT request,kind,body FROM responses ORDER BY rowid'),
                    'outgoing_transport_payloads': [json.loads(r['payload']) for r in self.store.rows('SELECT payload FROM sim_sends ORDER BY seq')],
                    'outbox': self.store.rows('SELECT request,body,state,wamid FROM outbox ORDER BY rowid'),
                    'receipts': self.store.rows('SELECT * FROM receipts'),
                })
        finally:
            super().tearDown()

    def test_voice_transcript_to_correlated_text_and_delivered_receipt(self):
        # Local OGG decoding is real. Speech recognition and API are injected.
        # The reply is computed from the claimed transcript, not from the receipt.
        audio = self.ogg_bytes()
        checksum = m.base64.b64encode(m.hashlib.sha256(audio).digest()).decode()
        row = self.process_attachment('audio', {'id': 'voice-evidence', 'mime_type': 'audio/ogg', 'voice': True, 'sha256': checksum},
                                      audio, 'audio/ogg', transcriber=lambda p: 'um dois tres quatro')
        self.assertEqual(row['state'], 'received')
        row, claimed = self.claim(row)
        transcript = claimed['attachment']['transcript']
        self.assertEqual(transcript, 'um dois tres quatro')
        body = f'A nota transcrita contém {len(transcript.split())} palavras.'
        self.emit(row, 'completed', body, evidence=[claimed['attachment']['path']])
        self.bridge.transport = m.Simulator(self.store, self.fixture)
        while self.bridge.send_one():
            pass
        sent = self.store.rows('SELECT * FROM outbox WHERE request=? ORDER BY rowid', (row['request'],))
        self.assertEqual(sent[-1]['body'], 'A nota transcrita contém 4 palavras.')
        self.assertEqual(sent[-1]['state'], 'accepted')
        self.bridge.ingest(m.poll(statuses=[{'id': sent[-1]['wamid'], 'status': 'delivered',
                                            'timestamp': str(int(self.now)), 'recipient_id': 'user:owner'}], offset=99))
        current = self.store.rows('SELECT * FROM outbox WHERE wamid=?', (sent[-1]['wamid'],))[0]
        self.assertEqual(current['state'], 'delivered')
        self.assertEqual(self.store.request(row['request'])['state'], 'completed')
        outputs = [json.loads(r['payload']) for r in self.store.rows('SELECT payload FROM sim_sends')]
        self.assertTrue(all(p['type'] == 'text' for p in outputs))
        self.assertEqual(outputs[-1]['text']['body'], body)

CAPTURE = {
    'test_real_inbox_main_result_and_delivery',
    'test_image_pdf_text_and_voice_reach_main',
    'test_native_video_frames_and_correlated_text_reply',
    'test_voice_transcript_to_correlated_text_and_delivered_receipt',
    'test_office_files_extract_text_cells_and_slides_without_execution',
}
NAMES = [
    'test_real_inbox_main_result_and_delivery',
    'test_note_gap_recovery_dedup_and_ack',
    'test_key_receipt_prepublication_gap_and_conflict',
    'test_cursor_empty_receipts_profiles_and_integer',
    'test_old_backlog_and_restart_identity',
    'test_diagnostics_do_not_activate_and_first_poll_preserves_boundary',
    'test_replay_configuration_is_rejected_without_executing_history',
    'test_singleton_and_persistent_conflict_halt',
    'test_main_auth_and_cross_home_note_refusal',
    'test_unavailable_preserves_without_false_start',
    'test_ready_multipart_output_avoids_long_poll_and_keeps_idle_timeout',
    'test_poll_uses_idle_timeout_unless_ordered_head_is_sendable',
    'test_stop_during_forward_finishes_current_note_only',
    'test_image_pdf_text_and_voice_reach_main',
    'test_voice_transcript_to_correlated_text_and_delivered_receipt',
    'test_voice_without_transcriber_fails_honestly',
    'test_media_failures_and_text_regression',
    'test_tts_flag_still_refused',
    'test_native_video_frames_and_correlated_text_reply',
    'test_video_audio_requires_transcription_and_keeps_caption',
    'test_silent_video_preserves_frames_but_stt_errors_and_empty_audio_fail',
    'test_transparent_png_previews_preserve_dark_shapes_on_white',
    'test_compressed_and_scanned_pdf_are_readable_with_all_page_previews',
    'test_office_files_extract_text_cells_and_slides_without_execution',
    'test_media_retry_after_survives_restart_and_preserves_one_note',
    'test_async_processing_does_not_block_text_receipts_or_duplicate_work',
]
start = time.monotonic()
result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(EvidenceChecks(n) for n in NAMES))
(OUT / 'whatsapp-protocol-evidence.json').write_text(json.dumps({
    'scope': 'Synthetic account and API; real SQLite, inbox helpers, authenticated fixture main CLI, local media decoders; injected speech transcription; no live WhatsApp delivery.',
    'scenarios': records,
}, indent=2, ensure_ascii=False) + '\n')
(OUT / 'focused-test-result.json').write_text(json.dumps({
    'tests': NAMES, 'run': result.testsRun, 'failures': len(result.failures),
    'errors': len(result.errors), 'skipped': result.skipped,
    'elapsed_seconds': round(time.monotonic()-start, 3),
}, indent=2) + '\n')
sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
