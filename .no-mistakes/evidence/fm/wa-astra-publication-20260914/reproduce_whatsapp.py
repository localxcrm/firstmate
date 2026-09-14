"""Run from the gate worktree; fixture-only product evidence, never a live account."""
import io
import json
import os
from pathlib import Path
import plistlib
import sqlite3
import subprocess
import sys
import types
import unittest

ROOT = Path.cwd()
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'tests'))
import fm_whatsapp_test as tests

runs = []
class Recorded(tests.WhatsAppTests):
    def setUp(self):
        self.events = []
        super().setUp()

    def receive(self, message=None, offset=None):
        result = super().receive(message, offset)
        self.events.append({'interface': 'incoming WhatsApp update (simulated)',
                            'input': message, 'persisted_request': result})
        return result

    def main(self, data, ok=True):
        result = super().main(data, ok)
        self.events.append({'interface': 'authenticated main CLI',
                            'operation': data, 'response': result})
        return result

    def cli(self, *args, ok=True):
        result = super().cli(*args, ok=ok)
        self.events.append({'interface': 'bridge CLI', 'arguments': args, 'response': result})
        return result

    def tearDown(self):
        runs.append({'scenario': self._testMethodName, 'events': self.events,
                     'outgoing_simulated_messages': [json.loads(r['payload']) for r in
                         self.store.rows('SELECT payload FROM sim_sends ORDER BY seq')],
                     'persisted_state': self.store.snapshot(),
                     'decisions': self.store.rows('SELECT id,state,answer_wamid,expires FROM decisions')})
        super().tearDown()

    def test_cli_poll_backup_disabled_service(self):
        fixture = self.dir / 'cli-script.json'
        fixture.write_text(json.dumps([{'endpoint': 'updates', 'http': 200,
                                       'body': tests.poll([self.message()]).body}]))
        self.values['state_dir'] = str(self.dir / 'cli-state')
        self.values['simulator_file'] = str(fixture)
        self.path.write_text(json.dumps(self.values))
        first = self.cli('run', '--once', '--fixture', str(fixture))
        second = self.cli('run', '--once', '--fixture', str(fixture))
        self.assertEqual(first['cursor'], 1)
        self.assertEqual(len(second['requests']), 1)
        backup = self.dir / 'backup.sqlite3'
        self.cli('backup', '--output', str(backup))
        with sqlite3.connect(backup) as db:
            saved = db.execute('SELECT wamid,state FROM inbound').fetchall()
        self.assertEqual(len(saved), 1)
        self.events.append({'interface': 'persisted SQLite backup', 'inbound_rows': saved})
        if sys.platform == 'darwin':
            target = self.dir / 'bridge.plist'
            result = self.cli('service-render', '--output', str(target))
            rendered = plistlib.loads(target.read_bytes())
            self.assertTrue(rendered['Disabled'])
            self.assertTrue(result['disabled'])
            self.assertEqual(rendered['ProgramArguments'][0], str(Path(sys.executable).resolve()))
            self.assertIn(str(fixture), rendered['ProgramArguments'])
            self.assertIsNone(self.harness.poll())
            self.events.append({'interface': 'generated launchd configuration, parsed semantically',
                                'configuration': rendered, 'installed': False})

selectors = ['test_real_inbox_main_result_and_delivery',
             'test_expired_pending_decision_preserves_conversational_confirmations',
             'test_decisions_bound_expiring_once_and_ambiguous',
             'test_cli_poll_backup_disabled_service']
current = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Recorded(n) for n in selectors))
(OUT / 'whatsapp-product-evidence.json').write_text(json.dumps({
    'scope': 'Local text bridge only. Real inbox, authenticated CLI and SQLite; simulated WhatsApp transport and structural harness. No model, account, production service or attachments activated.',
    'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'runs': runs}, ensure_ascii=False, indent=2) + '\n')
if not current.wasSuccessful():
    sys.exit(1)

# Execute the pre-R1 bridge implementation against the new behavioral regression.
# Companion modules and authenticated main CLI are unchanged by R1.
old_source = subprocess.check_output(['git', 'show', '684c61bc:bin/fm_whatsapp_bridge.py'], text=True)
old = types.ModuleType('pre_r1_whatsapp_bridge')
old.__file__ = str(ROOT / 'bin/fm_whatsapp_bridge.py')
exec(compile(old_source, '684c61bc:bin/fm_whatsapp_bridge.py', 'exec'), old.__dict__)
tests.Bridge = old.Bridge
baseline_log = io.StringIO()
baseline = unittest.TextTestRunner(stream=baseline_log, verbosity=2).run(unittest.TestSuite([
    tests.WhatsAppTests('test_expired_pending_decision_preserves_conversational_confirmations')]))
(OUT / 'r1-before-fix.txt').write_text('Pre-R1 bridge (684c61bc), target behavioral regression:\n' + baseline_log.getvalue())
assert not baseline.errors, baseline.errors
assert len(baseline.failures) == 6, baseline_log.getvalue()
assert all("'answered' != 'received'" in details for _, details in baseline.failures)
print('Pre-R1 reproduced: all six expired conversational confirmations intercepted. Target: all reach authenticated main; explicit expired code rejected. Product evidence saved.')
