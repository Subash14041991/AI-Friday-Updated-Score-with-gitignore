import json
from argparse import Namespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import run_pipeline as pipeline
from scripts import pipeline_support as support
from pipeline_fixtures import response, SCENARIO


def args_for(root):
    scenario=root/'scenario.html';scenario.write_text(SCENARIO,encoding='utf-8')
    return Namespace(scenario=str(scenario),prompt_dir=str(pipeline.PROJECT_ROOT/'prompts'),
        api_key_env='TEST_KEY',base_url='https://gateway.example/v1',timeout=10,
        output_dir=str(root/'runs'),model='test-model',available_models=['test-model'],
        max_output_tokens=None,max_context_chars=120000,poc_question=None,interactive=False,
        execute_poc_tests=False,repair_attempts=1,http_retries=0,resume=None,test_timeout=60)


class FakeClient:
    calls=[]; fail_stage=None; invalid_once=False
    def __init__(self,*args):pass
    def complete(self,*,model,system_prompt,user_prompt,max_tokens):
        stage=next(stage for stage,_,name,_ in pipeline.AGENTS if ('# Agent '+stage[1]+' ') in system_prompt)
        self.calls.append((stage,user_prompt,max_tokens))
        if stage==self.fail_stage:raise RuntimeError('Temporary fixture failure')
        if self.invalid_once:
            FakeClient.invalid_once=False
            return json.dumps({'markdown':'Invalid outline','artifacts':[]}),{'completion_tokens':1}
        return json.dumps(response(stage)),{'completion_tokens':2}


def fake_adapter(runtime,operation,*args,**kwargs):
    if operation=='diagram':Path(args[1]).write_text('<svg class="architecture-diagram" xmlns="http://www.w3.org/2000/svg"><text>Fixture architecture</text></svg>',encoding='utf-8')
    return {'status':'PASS'}


class Helpers(unittest.TestCase):
    def test_all_scenario_neutral_fixtures_meet_prompt_contracts(self):
        for stage,_,_,_ in pipeline.AGENTS:
            result=pipeline.parse_agent_json(json.dumps(response(stage)),stage)
            self.assertTrue(result['markdown'])

    def test_json_errors_and_stage_artifact_rejection(self):
        with self.assertRaises(ValueError):pipeline.parse_agent_json('bad JSON','D1')
        data=response('D1');data['artifacts']=[{'path':'poc/extra.html','content':'x'}]
        with self.assertRaisesRegex(ValueError,'must not return'):pipeline.parse_agent_json(json.dumps(data),'D1')

    def test_missing_sections_and_wrong_counts_rejected(self):
        data=response('D1');data['markdown']=data['markdown'].replace('3. Business owners','Business owners')
        with self.assertRaisesRegex(ValueError,'assumptions'):pipeline.parse_agent_json(json.dumps(data),'D1')
        data=response('D5');data['markdown']=data['markdown'].replace('| Transition overload.', '| Extra risk | Mitigate | Owner |\n| Transition overload.')
        with self.assertRaisesRegex(ValueError,'five risks|5 rows'):pipeline.parse_agent_json(json.dumps(data),'D5')

    def test_word_limit_enforced(self):
        data=response('D2');data['markdown']+=' word'*800
        with self.assertRaisesRegex(ValueError,'word limit'):pipeline.parse_agent_json(json.dumps(data),'D2')

    def test_d4_readme_only_not_runnable(self):
        data=response('D4');data['artifacts']=[{'path':'poc/README.txt','content':'Instructions'}];data['poc']['entrypoint']='poc/README.txt'
        with self.assertRaisesRegex(ValueError,'runnable entrypoint'):pipeline.parse_agent_json(json.dumps(data),'D4')

    def test_d4_missing_dependencies_and_tests_rejected(self):
        data=response('D4');data['artifacts']=[x for x in data['artifacts'] if x['path']!='poc/application/app.js']
        with self.assertRaisesRegex(ValueError,'Missing'):pipeline.parse_agent_json(json.dumps(data),'D4')
        data=response('D4');data['poc']['engine_tests']=[]
        with self.assertRaisesRegex(ValueError,'engine test'):pipeline.parse_agent_json(json.dumps(data),'D4')

    def test_duplicate_artifact_names_and_external_runtime_references_rejected(self):
        data=response('D4');data['artifacts'].append(data['artifacts'][0].copy())
        with self.assertRaisesRegex(ValueError,'Duplicate artifact'):pipeline.parse_agent_json(json.dumps(data),'D4')
        data=response('D4');data['artifacts'][0]['content']+='<script src="https://example.com/library.js"></script>'
        with self.assertRaisesRegex(ValueError,'External runtime'):pipeline.parse_agent_json(json.dumps(data),'D4')

    def test_external_packages_and_null_entrypoints_rejected(self):
        data=response('D4');data['poc']['entrypoint']=None
        with self.assertRaisesRegex(ValueError,'non-empty string'):pipeline.parse_agent_json(json.dumps(data),'D4')
        data=response('D4');data['artifacts'][-2]['content']+="\nrequire('uninstalled-package');"
        with self.assertRaisesRegex(ValueError,'external Node dependency'):pipeline.parse_agent_json(json.dumps(data),'D4')

    def test_optional_third_option_is_supported(self):
        data=response('D2');data['markdown']=data['markdown'].replace('#### Trade-off comparison','#### Option C — Limited partner portal\nA portal supports human-entered updates but requires extra coordination.\n#### Trade-off comparison')
        lines=[];in_table=False
        for line in data['markdown'].splitlines():
            if line.startswith('|'):
                if '| Criterion ' in line:line=line+' Option C |'
                elif set(line.replace('|','').replace('-','').strip())==set():line=line+'---|'
                else:line=line+' Depends on portal adoption. |'
            lines.append(line)
        data['markdown']='\n'.join(lines)
        pipeline.parse_agent_json(json.dumps(data),'D2')

    def test_generated_evidence_replaces_not_run_without_claiming_assertion_count(self):
        md=support.with_execution_evidence(response('D4')['markdown'],{'status':'PASS','execution_checks':2,'executedAt':'2026-10-08T00:00:00Z'})
        self.assertNotIn('NOT RUN',md);self.assertIn('not individual assertions',md);support.validate_markdown(md,'D4')

    def test_artifact_paths_cross_platform(self):
        for value in ['../secret.txt','poc/../../outside.js','poc\\..\\outside.js','C:\\poc\\x.js','poc/x.js:stream','poc/CON.txt','output/x.html']:
            with self.subTest(value=value),self.assertRaises(ValueError):pipeline.validate_artifact({'path':value,'content':'x'})
        self.assertEqual(pipeline.validate_artifact({'path':'poc/tests/test.cjs','content':'x'})[0].as_posix(),'poc/tests/test.cjs')

    def test_safe_clickable_links_and_html_escape(self):
        text=pipeline.markdown_to_html('[Open](poc/application/index.html)\n\n<script>alert(1)</script>')
        self.assertIn('<a href="poc/application/index.html">',text);self.assertNotIn('<script>',text)
        self.assertNotIn('href=',pipeline.render_inline('[Unsafe](javascript:alert)'))

    def test_context_no_claimed_approval_and_explicit_execution_contract(self):
        text=pipeline.context_for_stage('D4','Scenario',{'D1':'Draft'},None)
        self.assertIn('human approval not established',text);self.assertIn('NOT RUN',text)
        self.assertIn('engine_tests',text);self.assertIn('browser_test',text)

    def test_extraction_skips_nested_code_and_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'s.html';file.write_text('<nav>skip<script>code</script></nav><section id="challenge"><h1>Warehouse</h1><p>Keep records</p></section>',encoding='utf-8')
            value=pipeline.extract_scenario_text(file)
            self.assertNotIn('skip',value);self.assertNotIn('code',value);self.assertIn('[SECTION: challenge]',value)

    def test_api_payload_and_finish_reason(self):
        class Reply:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return json.dumps({'choices':[{'message':{'content':'{}'},'finish_reason':'stop'}],'usage':{'completion_tokens':5}}).encode()
        client=pipeline.OpenAICompatibleClient('https://gateway.example/v1','key',retries=0)
        with patch('scripts.run_pipeline.urlopen',return_value=Reply()) as call:
            content,usage=client.complete(model='model',system_prompt='system',user_prompt='user',max_tokens=1000)
        payload=json.loads(call.call_args.args[0].data);self.assertEqual(payload['response_format'],{'type':'json_object'});self.assertEqual(usage['completion_tokens'],5)
        class Truncated(Reply):
            def read(self):return json.dumps({'choices':[{'message':{'content':'{}'},'finish_reason':'length'}]}).encode()
        with patch('scripts.run_pipeline.urlopen',return_value=Truncated()),self.assertRaises(pipeline.CompletionTruncated):client.complete(model='model',system_prompt='x',user_prompt='y',max_tokens=500)

    def test_transient_gateway_retry_bounded(self):
        class Reply:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return b'{"data":[]}'
        client=pipeline.OpenAICompatibleClient('https://gateway.example/v1','key',retries=1)
        with patch('scripts.run_pipeline.urlopen',side_effect=[HTTPError('url',503,'busy',{},None),Reply()]) as call,patch('scripts.run_pipeline.time.sleep'):
            client.check_models([])
        self.assertEqual(call.call_count,2)

    def test_env_does_not_override_existing_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'settings.env';file.write_text('OPENAI_BASE_URL=https://file.example/v1\n',encoding='utf-8')
            with patch.dict('os.environ',{'OPENAI_BASE_URL':'https://shell.example/v1'},clear=True):
                pipeline.load_env_file(file)
                import os
                self.assertEqual(os.environ['OPENAI_BASE_URL'],'https://shell.example/v1')

    def test_runtime_discovery_prefers_checkout_packages_without_codex(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);node=root/'node.exe';node.write_text('placeholder')
            for name in ['playwright','@viz-js/viz']:
                package=root/'node_modules'/name;package.mkdir(parents=True);(package/'package.json').write_text('{}')
            with patch('scripts.pipeline_support.ROOT',root),patch('scripts.pipeline_support.shutil.which',return_value=str(node)),patch('pathlib.Path.home',return_value=root/'no-codex'),patch.dict('os.environ',{},clear=True):
                found=support.runtime_paths(Namespace(node_path=None,node_modules=None))
            self.assertEqual(Path(found['modules']),root/'node_modules');self.assertEqual(Path(found['node']),node)

    def test_runtime_overrides_work_when_home_and_codex_are_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);node=root/'node.exe';node.write_text('placeholder');modules=root/'packages'
            for name in ['playwright','@viz-js/viz']:
                package=modules/name;package.mkdir(parents=True);(package/'package.json').write_text('{}')
            with patch('pathlib.Path.home',side_effect=RuntimeError('No home')),patch.dict('os.environ',{},clear=True):
                found=support.runtime_paths(Namespace(node_path=str(node),node_modules=str(modules)))
            self.assertEqual(Path(found['modules']),modules)


class Orchestration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.args=args_for(self.root);FakeClient.calls=[];FakeClient.fail_stage=None;FakeClient.invalid_once=False
        env=patch.dict('os.environ',{'TEST_KEY':'fixture-key'},clear=True);env.start();self.addCleanup(env.stop)
        for target,value in [('scripts.run_pipeline.OpenAICompatibleClient',FakeClient),('scripts.pipeline_support.runtime_paths',lambda args:{'node':'fixture','modules':'fixture'}),('scripts.pipeline_support.run_node',fake_adapter),('scripts.pipeline_support.static_check_bundle',lambda *args:None)]:
            mocked=patch(target,value);mocked.start();self.addCleanup(mocked.stop)

    def test_full_run_creates_report_bundle_and_unexecuted_evidence(self):
        folder=pipeline.run_pipeline(self.args)
        self.assertEqual([x[0] for x in FakeClient.calls],['D1','D2','D3','D4','D5'])
        self.assertIn('Warehouse teams',FakeClient.calls[-1][1]);self.assertIn('NOT RUN',FakeClient.calls[-1][1])
        for name in ['D1.md','D2.md','D3.md','D4.md','D5.md','manifest.json','architecture.svg','final-submission-report.html','final-pack.html','poc-validation.json','README.md']:
            self.assertTrue((folder/name).is_file(),name)
        manifest=json.loads((folder/'manifest.json').read_text());self.assertEqual(manifest['status'],'complete');self.assertEqual(manifest['poc_execution'],'NOT RUN')
        self.assertIn('<svg',(folder/'final-submission-report.html').read_text());self.assertIn('poc/application/index.html',(folder/'final-submission-report.html').read_text())

    def test_failure_records_manifest_and_resume_skips_paid_completed_stages(self):
        FakeClient.fail_stage='D3'
        with self.assertRaises(RuntimeError):pipeline.run_pipeline(self.args)
        folder=next((self.root/'runs').iterdir());manifest=json.loads((folder/'manifest.json').read_text());self.assertEqual(manifest['status'],'failed')
        FakeClient.fail_stage=None;FakeClient.calls=[];self.args.resume=str(folder)
        pipeline.run_pipeline(self.args);self.assertEqual([x[0] for x in FakeClient.calls],['D3','D4','D5'])

    def test_tampered_saved_markdown_blocks_resume(self):
        FakeClient.fail_stage='D3'
        with self.assertRaises(RuntimeError):pipeline.run_pipeline(self.args)
        folder=next((self.root/'runs').iterdir());(folder/'D1.md').write_text('changed')
        self.args.resume=str(folder);FakeClient.fail_stage=None;FakeClient.calls=[]
        with self.assertRaisesRegex(ValueError,'Markdown changed'):pipeline.run_pipeline(self.args)
        self.assertEqual(FakeClient.calls,[])

    def test_all_model_slots_checked_before_any_call(self):
        self.args.model=None;self.args.model_d1='test-model'
        with self.assertRaisesRegex(ValueError,'No model configured'):pipeline.run_pipeline(self.args)
        self.assertEqual(FakeClient.calls,[]);self.assertFalse((self.root/'runs').exists())

    def test_bounded_content_repair_records_usage(self):
        FakeClient.invalid_once=True;folder=pipeline.run_pipeline(self.args)
        manifest=json.loads((folder/'manifest.json').read_text());self.assertEqual(len(FakeClient.calls),6)
        self.assertEqual(manifest['attempts'][0]['status'],'rejected');self.assertEqual(len(manifest['usage_reported_by_gateway']['D1']),2)

    def test_report_qa_failure_is_not_complete_and_resume_avoids_model_calls(self):
        def adapter(runtime,operation,*args,**kwargs):
            if operation=='report':raise RuntimeError('Page 3 overlaps footer')
            return fake_adapter(runtime,operation,*args,**kwargs)
        with patch('scripts.pipeline_support.run_node',adapter),self.assertRaisesRegex(RuntimeError,'overlaps'):pipeline.run_pipeline(self.args)
        folder=next((self.root/'runs').iterdir());self.assertEqual(json.loads((folder/'manifest.json').read_text())['status'],'failed')
        self.args.resume=str(folder);FakeClient.calls=[];pipeline.run_pipeline(self.args);self.assertEqual(FakeClient.calls,[])

    def test_poc_failure_stops_d5_and_resume_retests_without_regenerating_d4(self):
        self.args.execute_poc_tests=True
        with patch('scripts.pipeline_support.execute_poc',side_effect=RuntimeError('POC failed')),self.assertRaisesRegex(RuntimeError,'POC failed'):pipeline.run_pipeline(self.args)
        folder=next((self.root/'runs').iterdir());self.assertNotIn('D5',[x[0] for x in FakeClient.calls]);self.args.resume=str(folder);FakeClient.calls=[]
        def evidence(root,*args):
            result={'status':'PASS','execution_checks':2,'executedAt':'2026-10-08T00:00:00Z','results':[]}
            support.write_json(root/'poc-validation.json',result);return result
        with patch('scripts.pipeline_support.execute_poc',evidence):pipeline.run_pipeline(self.args)
        self.assertEqual([x[0] for x in FakeClient.calls],['D5']);self.assertIn('Verified POC execution status',FakeClient.calls[0][1])

    def test_reviewed_unexecuted_run_can_be_promoted_and_regenerates_only_d5(self):
        folder=pipeline.run_pipeline(self.args);self.args.resume=str(folder);self.args.execute_poc_tests=True;FakeClient.calls=[]
        def evidence(root,*args):
            result={'status':'PASS','execution_checks':2,'executedAt':'2026-10-08T00:00:00Z','results':[]}
            support.write_json(root/'poc-validation.json',result);return result
        with patch('scripts.pipeline_support.execute_poc',evidence):pipeline.run_pipeline(self.args)
        self.assertEqual([x[0] for x in FakeClient.calls],['D5'])
        self.assertIn('Execution status: **PASS**',(folder/'D4.md').read_text())

if __name__=='__main__':unittest.main()
