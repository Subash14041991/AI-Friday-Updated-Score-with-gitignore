"""Real offline adapters with a deterministic, in-process model fixture.

No paid API or external gateway is used. Generated fixture tests are executed
only with the explicit execution flag, in an isolated loopback browser profile.
"""
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))
from scripts import run_pipeline
from pipeline_fixtures import SCENARIO,response

calls=[]
class FixtureClient:
    def __init__(self,*args):pass
    def complete(self,*,model,system_prompt,user_prompt,max_tokens):
        stage=next(stage for stage,_,_,_ in run_pipeline.AGENTS if '# Agent '+stage[1]+' ' in system_prompt)
        calls.append((stage,user_prompt))
        return json.dumps(response(stage)),{'completion_tokens':100,'fixture':True}

def main():
    target=ROOT/'.review/pipeline-integration'
    target.mkdir(parents=True,exist_ok=True)
    scenario=target/'warehouse.html';scenario.write_text(SCENARIO,encoding='utf-8')
    args=run_pipeline.make_parser().parse_args([str(scenario),'--output-dir',str(target/'runs'),
        '--base-url','https://fixture.invalid/v1','--model','fixture-model','--available-models','fixture-model',
        '--api-key-env','FIXTURE_KEY','--execute-poc-tests','--repair-attempts','0'])
    for index in range(1,6):setattr(args,f'model_d{index}','fixture-model')
    with patch.dict(os.environ,{'FIXTURE_KEY':'not-a-real-key'}),patch('scripts.run_pipeline.OpenAICompatibleClient',FixtureClient):
        folder=run_pipeline.run_pipeline(args)
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    evidence=json.loads((folder/'poc-validation.json').read_text(encoding='utf-8'))
    assert manifest['status']=='complete' and manifest['report_validation']=='PASS'
    assert evidence['status']=='PASS' and evidence['execution_checks']==2
    assert '"status": "PASS"' in calls[-1][1]
    assert 'Execution status: **PASS**' in (folder/'D4.md').read_text(encoding='utf-8')
    assert 'NOT RUN' not in (folder/'D4.md').read_text(encoding='utf-8')
    run_pipeline.support.write_json(target/'integration-result.json',{'status':'PASS','run_directory':str(folder),
        'checks':['Five scenario-neutral stages','Actual graph rendering','Generated engine test executed','Generated browser test executed',
                  'Verified evidence supplied before D5','Clickable POC links','Five-page browser/print QA','PDF and page previews'],
        'limitation':'Fixture model responses, not a live gateway/model-quality validation.'})
    print('Offline integration passed: '+str(folder))

if __name__=='__main__':main()
