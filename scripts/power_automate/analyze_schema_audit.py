"""Analyze a returned issue-66 metadata report locally; never changes SharePoint."""
import argparse
import json
from pathlib import Path
from schema_audit import analyze

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('report',type=Path)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
if args.output.exists():raise FileExistsError(args.output)
result=analyze(json.loads(args.report.read_text(encoding='utf-8-sig')))
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_bytes((json.dumps(result,indent=2)+'\n').encode('utf-8'))
print(result['status']+':',len(result['findings']),'findings. Mapping:',args.output)
print('No changes applied; inspect evidence before preparing any concrete setup delta.')
