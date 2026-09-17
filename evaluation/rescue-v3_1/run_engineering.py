"""Run real engineering tests and map specified checks to observed outcomes."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.rows=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.rows.append({'test':test.id(),'status':'PASS'})
    def addFailure(self,test,error):
        super().addFailure(test,error);self.rows.append({'test':test.id(),'status':'FAIL','detail':self._exc_info_to_string(error,test)})
    def addError(self,test,error):
        super().addError(test,error);self.rows.append({'test':test.id(),'status':'ERROR','detail':self._exc_info_to_string(error,test)})
    def addSkip(self,test,reason):
        super().addSkip(test,reason);self.rows.append({'test':test.id(),'status':'SKIP','detail':reason})


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests/parser_rescue'))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordedResult).run(suite)
    specifications=json.loads((ROOT/'rescue/package/contracts/checks.json').read_text())['checks']
    rows=[]
    for item in specifications:
        observed=[x for x in result.rows if x['test'].split('.')[-1]=='test_'+item['id']]
        status=observed[0]['status'] if len(observed)==1 else 'NOT_RUN' if not observed else 'DUPLICATE_CHECK_ID'
        rows.append({'id':item['id'],'status':status,'tests':observed})
    summary={'specified':35,'passed':sum(x['status']=='PASS' for x in rows),'tests_run':result.testsRun,'all_tests_successful':result.wasSuccessful(),'checks':rows,'all_results':result.rows}
    (out/'unittest.log').write_text(stream.getvalue())
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('checks','all_results')},ensure_ascii=False))
    return 0 if summary['passed']==35 and result.wasSuccessful() else 1


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path)
    raise SystemExit(run(ap.parse_args().out))
