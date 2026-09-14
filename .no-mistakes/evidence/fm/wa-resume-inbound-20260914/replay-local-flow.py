"""Offline product flow: extraction -> authenticated main -> text reply -> simulated receipt."""
import importlib.util, json, sys, io, shutil
from pathlib import Path
from PIL import Image
ROOT=Path.cwd()
OUT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('wa_tests',ROOT/'tests/fm_whatsapp_test.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
records=[]
for mode in ('text','image','pdf','voice','silent-video','txt','docx','xlsx','pptx'):
    t=m.WhatsAppTests(); t.setUp()
    try:
        if mode=='text':
            row=t.receive(t.message('Quanto é 37 + 5?'))
        elif mode=='image':
            image=Image.new('RGBA',(80,80),(0,0,0,0)); image.paste((0,0,0,255),(20,20,60,60))
            b=io.BytesIO(); image.save(b,format='PNG'); row=t.prepared('image','image/png',b.getvalue(),caption='Descreva a forma')
        elif mode=='pdf':
            row=t.prepared('document','application/pdf',t.pdf_bytes('Total: 100',compressed=True))
        elif mode=='voice':
            data=t.ogg_bytes(); row=t.process_attachment('audio',{'id':'voice-evidence','mime_type':'audio/ogg','voice':True,'sha256':m.base64.b64encode(m.hashlib.sha256(data).digest()).decode()},data,'audio/ogg',transcriber=lambda path:'Conte 37 mais 5')
        elif mode=='silent-video':
            data=t.video_bytes(audio=True,silent=True)
            row=t.process_attachment('video',{'id':'video-evidence','mime_type':'video/mp4','caption':'Descreva a cor','sha256':m.base64.b64encode(m.hashlib.sha256(data).digest()).decode()},data,'video/mp4',transcriber=lambda path:'')
        elif mode=='txt':
            row=t.prepared('document','text/plain',b'Total: 100\n')
        elif mode=='docx':
            p='<w:p><w:r><w:t>Total: </w:t></w:r><w:r><w:t>1</w:t></w:r><w:r><w:t>00</w:t></w:r></w:p>'
            word='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><w:body><w:p><mc:AlternateContent><mc:Choice Requires="wps">'+p+'</mc:Choice><mc:Fallback>'+p+'</mc:Fallback></mc:AlternateContent></w:p>'+p+p+'</w:body></w:document>'
            row=t.prepared('document','application/vnd.openxmlformats-officedocument.wordprocessingml.document',t.office_bytes({'word/document.xml':word}))
        elif mode=='xlsx':
            row=t.prepared('document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',t.office_bytes(t.workbook_files([(2,'Receita'),(1,'Despesa')])))
        else:
            row=t.prepared('document','application/vnd.openxmlformats-officedocument.presentationml.presentation',t.office_bytes(t.presentation_files([10,2,1])))
        assert row['state']=='received', (mode,row)
        row,claim=t.claim(row); a=claim.get('attachment') or {}
        samples=OUT/'flow-samples'/mode; samples.mkdir(parents=True,exist_ok=True)
        for i,frame in enumerate(a.get('frames',[])):
            shutil.copyfile(frame['path'],samples/f'preview-{i+1}.jpg')
        if a.get('path'):
            shutil.copyfile(a['path'],samples/Path(a['path']).name)
        if mode in ('text','voice'):
            answer=f'37 + 5 = {37+5}.'
        elif mode=='image':
            with Image.open(a['frames'][0]['path']) as picture:
                assert max(picture.getpixel((40,40)))<15 and min(picture.getpixel((5,5)))>240
            answer='A prévia mostra um quadrado preto sobre fundo branco.'
        elif mode=='silent-video':
            assert a['has_audio'] and not a['speech_detected'] and a['transcript']==''
            with Image.open(a['frames'][0]['path']) as picture:
                r,g,b=picture.getpixel((10,10)); assert r>200 and g+b<40
            answer='Os quadros amostrados mostram vermelho; nenhuma fala foi detectada pelo transcritor de fixture.'
        elif mode=='docx':
            count=a['extracted_text'].count('Total: 100'); assert count==3
            answer=f'O documento contém {count} valores Total: 100; soma {count*100}. A representação alternativa da caixa não foi contada novamente.'
        elif mode=='xlsx':
            text=a['extracted_text']; assert text.index('Receita')<text.index('Despesa')
            assert 'A1: 200' in text and 'A1: 100' in text
            answer='Ordem das abas: Receita (A1: 200), Despesa (A1: 100). Diferença: 100.'
        elif mode=='pptx':
            text=a['extracted_text']; assert text.index('Slide 10')<text.index('Slide 2')<text.index('Slide 1\n') if 'Slide 1\n' in text else text.index('Slide 10')<text.index('Slide 2')<text.rindex('Slide 1')
            answer='A sequência da apresentação é Slide 10, Slide 2, Slide 1.'
        else:
            assert 'Total: 100' in a['extracted_text']; answer='O total informado no arquivo é 100.'
        emitted=t.emit(row,'completed',answer,evidence=[a['path']] if a else ['37 + 5 = 42'])
        t.bridge.transport=m.Simulator(t.store,t.fixture)
        while t.bridge.send_one(): pass
        sends=[json.loads(x['payload']) for x in t.store.rows('SELECT payload FROM sim_sends ORDER BY seq')]
        assert sends and all(x['type']=='text' for x in sends) and sends[-1]['text']['body']==answer
        outgoing=t.store.snapshot()['outbox']
        statuses=[{'id':x['wamid'],'status':'delivered','timestamp':'1','recipient_id':'user:owner'} for x in outgoing]
        t.bridge.ingest(m.poll(statuses=statuses,offset=int(t.store.get('cursor'))+1))
        assert all(x['state']=='delivered' for x in t.store.snapshot()['outbox'])
        records.append({'modality':mode,'claim':claim,'computed_text_reply':answer,'emit_result':emitted,'simulated_sends':sends,'persisted_request':t.store.request(row['request']),'persisted_outbox_after_simulated_receipt':t.store.snapshot()['outbox']})
    finally: t.tearDown()
(OUT/'local-flow.json').write_text(json.dumps({'scope':'LOCAL ONLY. Real decoding, inbox, authenticated main CLI and SQLite. No LLM. Deterministic fixture interpretation; synthetic audio with injected STT. Transport and delivery receipts simulated. Real-account acceptance remains pending with main.', 'flows':records},ensure_ascii=False,indent=2))
print(json.dumps({'completed_local_flows':[r['modality'] for r in records]},ensure_ascii=False))
