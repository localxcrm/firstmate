import importlib.util, json, os, shutil, sys, unittest
from pathlib import Path
ROOT = Path.cwd()
EVIDENCE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('wa_tests', ROOT / 'tests/fm_whatsapp_test.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert m.MEDIA_TOOLS, 'Required media decoders missing'
selected = [
'real_inbox_main_result_and_delivery', 'note_gap_recovery_dedup_and_ack',
'diagnostics_do_not_activate_and_first_poll_preserves_boundary',
'main_auth_and_cross_home_note_refusal', 'decisions_bound_expiring_once_and_ambiguous',
'terminal_outcomes_retire_decisions_and_preserve_consumed_receipts',
'terminal_decision_retirement_rolls_back_with_outcome',
'http_media_url_validated_before_secret', 'tts_flag_still_refused',
'image_pdf_text_and_voice_reach_main', 'voice_without_transcriber_fails_honestly',
'media_failures_and_text_regression', 'media_restart_dedup_and_fairness',
'native_video_frames_and_correlated_text_reply',
'video_audio_requires_transcription_and_keeps_caption',
'silent_video_preserves_frames_but_stt_errors_and_empty_audio_fail',
'transparent_png_previews_preserve_dark_shapes_on_white',
'video_duration_corruption_and_container_limits',
'compressed_and_scanned_pdf_are_readable_with_all_page_previews',
'corrupt_image_and_pdf_page_limit_fail_without_claim',
'office_files_extract_text_cells_and_slides_without_execution',
'office_formatting_runs_preserve_text_and_paragraph_boundaries',
'docx_nested_textbox_paragraphs_preserve_runs_once_in_document_order',
'docx_alternate_content_selects_one_representation_without_deduplicating_text',
'docx_unsupported_choices_select_fallback',
'docx_alternate_content_resolves_scoped_namespace_prefixes',
'docx_nested_alternate_content_only_traverses_selected_branches',
'docx_without_supported_compatibility_representation_fails',
'workbook_rich_strings_match_inline_and_preserve_cached_numbers',
'workbook_names_and_order_follow_internal_relationships',
'workbook_invalid_relationships_fail_without_forwarding',
'presentation_order_uses_slide_relationships_and_positions',
'presentation_missing_or_external_slide_relationship_fails',
'office_macros_entities_and_expansion_bombs_are_refused',
'media_metadata_is_required_and_consistent',
'invalid_media_identifiers_and_surrogates_do_not_poison_cursor',
'media_retry_after_survives_restart_and_preserves_one_note',
'media_storage_budget_preserves_originals_without_downloading',
'image_oversized_dimensions_refused_before_decoder',
'async_processing_does_not_block_text_receipts_or_duplicate_work',
'local_command_bounds_output_environment_and_descendants']
records = []
class Captured(m.WhatsAppTests):
    def main(self, data, ok=True):
        result = super().main(data, ok)
        entry = {'test': self._testMethodName, 'input':data, 'output':result}
        records.append(entry)
        att = result.get('attachment') or {}
        name = self._testMethodName.removeprefix('test_')
        if att and ('alternate_content_selects_one' in name or 'transparent_png' in name or 'native_video' in name or 'image_pdf_text' in name):
            target = EVIDENCE / 'samples' / name / str(len(records))
            target.mkdir(parents=True, exist_ok=True)
            if att.get('path'):
                shutil.copyfile(att['path'], target / Path(att['path']).name)
            for i, frame in enumerate(att.get('frames', [])):
                shutil.copyfile(frame['path'], target / f'preview-{i+1}.jpg')
            entry['preserved_samples'] = str(target)
        return result
    def tearDown(self):
        try:
            records.append({'test':self._testMethodName, 'persisted':self.store.snapshot(),
                            'simulated_text_sends':self.store.rows('SELECT payload FROM sim_sends ORDER BY seq'),
                            'decisions':self.store.rows('SELECT * FROM decisions')})
        finally:
            super().tearDown()
try:
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Captured('test_'+n) for n in selected))
finally:
    (EVIDENCE / 'behavior-transcript.json').write_text(json.dumps({'scope':'Isolated fixtures. Real inbox, SQLite, authenticated CLI and local decoders; simulated transport and injected STT; no live account or LLM.', 'records':records},ensure_ascii=False,indent=2))
    (EVIDENCE / 'selectors.json').write_text(json.dumps(['WhatsAppTests.test_'+n for n in selected],indent=2))
sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
