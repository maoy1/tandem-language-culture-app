"""Build issue 66's disposable metadata inspector; cloud execution stays in Power Automate."""
import argparse
from pathlib import Path
from schema_audit import build_package

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--site-url',required=True)
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'artifacts/schema_alignment/TandemSchemaAudit.zip')
args=parser.parse_args()
_,review=build_package(args.output,args.site_url)
print('Prepared:',args.output)
print('Actions:',review['actions'],'Maximum depth:',review['maximumActionDepth'])
print('Read-only SCHEMA-001 inspector; no tenant run or full #66 alignment pass claimed.')
