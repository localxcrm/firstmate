import json, os, subprocess, sys
from pathlib import Path
root=Path.cwd(); evidence=Path(__file__).parent
before=root/'.wa-test-scratch/extract-before.py'
before.write_bytes(subprocess.check_output(['git','show','d417e30:bin/fm_whatsapp_extract.py']))
source=evidence/'samples/docx_alternate_content_selects_one_representation_without_deduplicating_text/121/payload.docx'
outputs={}
for name, script in [('before_d417e30',before),('target_272ec4e',root/'bin/fm_whatsapp_extract.py')]:
    r=subprocess.run([sys.executable,str(script),'document','application/vnd.openxmlformats-officedocument.wordprocessingml.document',str(source)],env={**os.environ,'PYTHONPATH':str(root/'bin')},capture_output=True,text=True,check=True)
    outputs[name]=json.loads(r.stdout)
expected='[word/document.xml]\nBefore\nTotal: 100\nAfter\nTotal: 100\nTotal: 100'
assert outputs['before_d417e30']['extracted_text']!=expected
assert outputs['target_272ec4e']['extracted_text']==expected
(evidence/'docx-before-after.json').write_text(json.dumps({'input':str(source),'expected':expected,'outputs':outputs},ensure_ascii=False,indent=2))
print(json.dumps(outputs,ensure_ascii=False,indent=2))
