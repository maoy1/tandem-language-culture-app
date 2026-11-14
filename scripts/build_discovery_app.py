"""Build the #16 canvas-source candidate; Power Apps Studio validation is required.

Uses Microsoft's PAC SourceCode layout. No participant runtime dependencies.
The supplied .msapp is never overwritten. Run PAC unpack first, then this script,
then PAC pack. Only Discovery YAML, its entry button and three flow bindings change.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "artifacts/app_discovery/v1"


def label_array(expr):
    return f'Concat(Table({expr}) As x, Text(x.Value.label), ", ")'


def profile_text(p):
    fields = [("Teaches", "teachLanguages"), ("Learning", "learnLanguages"),
              ("Cultures to share", "shareCultures"), ("Cultures of interest", "learnCultures")]
    parts = [f'"{title}: " & {label_array(p+"."+field)}' for title, field in fields]
    parts += [f'"Time zone: " & Coalesce(Text({p}.timeZone.label), "Not specified")',
              f'"Learning focus: " & Text({p}.learningFocus)', f'"Comments: " & Text({p}.comments)']
    return ' & Char(10) & '.join(parts)


LOAD = '''Set(varDiscoveryBusy, true);
Set(varDiscoveryError, "");
Clear(colDiscoveryPeople); Clear(colDiscoveryGroups);
IfError(
    Set(varDiscoveryResponse, TandemDiscovery.Run(varDiscoveryActorId));
    If(varDiscoveryResponse.resultcode = "OK",
        ClearCollect(colDiscoveryPeople,
            ForAll(Table(ParseJSON(varDiscoveryResponse.candidatesjson)) As r,
                {kind: "Person", targetId: Value(r.Value.profileId),
                 title: Text(r.Value.displayName), summary: Text(r.Value.fitType),
                 detail: PERSON_DETAIL}));
        ClearCollect(colDiscoveryGroups,
            ForAll(Table(ParseJSON(varDiscoveryResponse.groupsjson)) As r,
                {kind: "Group", targetId: Value(r.Value.groupId),
                 title: Text(r.Value.name),
                 summary: Text(r.Value.memberCount) & "/" & Text(r.Value.capacity) & " members · " & Text(r.Value.freeSlots) & " places available",
                 detail: GROUP_DETAIL})),
        Set(varDiscoveryError, Switch(varDiscoveryResponse.resultcode,
            "PROFILE_UNAVAILABLE", "Your saved profile is not currently available for discovery. Review your registration and availability.",
            "Discovery could not load. Reference: " & varDiscoveryResponse.runreference))
    ),
    Clear(colDiscoveryPeople); Clear(colDiscoveryGroups);
    Set(varDiscoveryError, "Discovery could not load. Select Refresh to try again.")
);
Set(varDiscoveryBusy, false)'''
def match_text():
    parts=[]
    for reason, field, ids in [
        ('You can learn', 'teachLanguages', 'canLearnLanguageIds'),
        ('You can teach', 'learnLanguages', 'canShareLanguageIds'),
        ('You can learn about', 'shareCultures', 'canLearnCultureIds'),
        ('You can share about', 'learnCultures', 'canShareCultureIds')]:
        labels=(f'Concat(Filter(Table(r.Value.profile.{field}) As x, '
                f'Value(x.Value.id) in ForAll(Table(r.Value.match.{ids}) As mid, Value(mid.Value))) '
                'As matched, Text(matched.Value.label), ", ")')
        parts.append(f'If(!IsEmpty(Table(r.Value.match.{ids})), "{reason}: " & {labels} & Char(10), "")')
    return ' & '.join(parts)


PERSON = profile_text('r.Value.profile') + ' & Char(10) & Char(10) & ' + match_text()
GROUP = ('Text(r.Value.exchangeType) & " exchange · Open" & Char(10) & '
         f'"Languages: " & {label_array("r.Value.languageFocus")} & Char(10) & '
         f'"Cultures: " & {label_array("r.Value.cultureFocus")} & Char(10) & '
         'Text(r.Value.description) & Char(10) & Char(10) & "Members" & Char(10) & '
         'Concat(Table(r.Value.members) As m, Text(m.Value.displayName) & Char(10) & '
         + profile_text('m.Value') + ', Char(10) & Char(10))')
LOAD = LOAD.replace('PERSON_DETAIL', PERSON).replace('GROUP_DETAIL', GROUP)

# The intent and its complete payload remain stable until a confirmed result or
# explicit new intent. Neither a transport error nor Refresh replaces the UUID.
SEND = '''Set(varDiscoverySending, true);
Set(varDiscoveryOutcome, "");
If(IsBlank(varDiscoveryIntent),
    Set(varDiscoveryIntent, Text(GUID()));
    Set(varDiscoveryIntentKind, galDiscovery.Selected.kind);
    Set(varDiscoveryIntentTarget, galDiscovery.Selected.targetId);
    Set(varDiscoveryIntentActor, varDiscoveryActorId);
    Set(varDiscoveryIntentIntroduction, txtDiscoveryIntroduction.Text)
);
IfError(
    If(varDiscoveryIntentKind = "Person",
        Set(varDiscoveryPersonResult, TandemSendRequest.Run(varDiscoveryIntentActor, varDiscoveryIntentTarget, varDiscoveryIntent));
        Set(varDiscoverySendSuccess, varDiscoveryPersonResult.success);
        Set(varDiscoverySendCode, varDiscoveryPersonResult.resultcode);
        Set(varDiscoverySendId, varDiscoveryPersonResult.requestid);
        Set(varDiscoverySendReference, varDiscoveryPersonResult.runreference),
        Set(varDiscoveryGroupResult, TandemSendGroupJoinRequest.Run(varDiscoveryIntentTarget, varDiscoveryIntent, varDiscoveryIntentIntroduction));
        Set(varDiscoverySendSuccess, varDiscoveryGroupResult.success);
        Set(varDiscoverySendCode, varDiscoveryGroupResult.resultcode);
        Set(varDiscoverySendId, varDiscoveryGroupResult.requestid);
        Set(varDiscoverySendReference, varDiscoveryGroupResult.runreference)
    );
    If(varDiscoverySendSuccess,
        Set(varDiscoveryOutcome, "Request recorded (#" & varDiscoverySendId & "). Check My requests for its current status.");
        Set(varDiscoveryIntent, Blank());
        Set(varDiscoveryConfirmed, true),
        Set(varDiscoveryOutcome, "Request not confirmed (" & varDiscoverySendCode & "). Reference: " & varDiscoverySendReference & ". Retry keeps the same request intent.")
    ),
    Set(varDiscoveryOutcome, "No confirmation received. Retry keeps the same request intent; check My requests before starting another.")
);
Set(varDiscoverySending, false)'''


def control(name, kind, props, children=None, variant=None):
    d = {"Control": kind, "Properties": {k: "=" + str(v) for k, v in props.items()}}
    if variant:
        d["Variant"] = variant
    if children:
        d["Children"] = children
    return {name: d}


def screen():
    label = lambda n, p: control(n, "Label@2.5.1", {"Font": "Font.'Segoe UI'", "Size": "12", **p})
    button = lambda n, p: control(n, "Classic/Button@2.2.0", {"Height": "40", "Size": "12", **p})
    available = '!varDiscoveryBusy && !varDiscoverySending && IsBlank(varDiscoveryIntent)'
    select = 'If(IsBlank(varDiscoveryIntent), Set(varDiscoveryConfirmed, false); Set(varDiscoveryOutcome, ""); Reset(txtDiscoveryIntroduction))'
    items = 'If(varDiscoveryTab = "People", colDiscoveryPeople, colDiscoveryGroups)'
    c = [label("lblDiscoveryTitle", {"Text": '"Find an exchange"', "X": "24", "Y": "16", "Width": "Parent.Width - 340", "Height": "44", "Size": "24", "FontWeight": "FontWeight.Semibold"}),
         button("btnDiscoveryBack", {"Text": '"My registration"', "X": "Parent.Width - 300", "Y": "20", "Width": "160", "DisplayMode": 'If(varDiscoverySending, DisplayMode.Disabled, DisplayMode.Edit)', "OnSelect": "Navigate(MainScreen1, ScreenTransition.None)"}),
         button("btnDiscoveryRefresh", {"Text": '"Refresh"', "X": "Parent.Width - 128", "Y": "20", "Width": "104", "DisplayMode": 'If(varDiscoveryBusy || varDiscoverySending, DisplayMode.Disabled, DisplayMode.Edit)', "OnSelect": LOAD}),
         label("lblDiscoveryState", {"Text": 'If(varDiscoveryBusy, "Loading compatible people and groups…", varDiscoveryError)', "X": "24", "Y": "68", "Width": "Parent.Width - 48", "Height": "56", "Color": 'If(IsBlank(varDiscoveryError), RGBA(50,49,48,1), RGBA(164,38,44,1))'}),
         button("btnDiscoveryPeople", {"Text": '"People (" & CountRows(colDiscoveryPeople) & ")"', "X": "24", "Y": "128", "Width": "160", "OnSelect": 'Set(varDiscoveryTab, "People"); ' + select, "DisplayMode": f'If({available}, DisplayMode.Edit, DisplayMode.Disabled)'}),
         button("btnDiscoveryGroups", {"Text": '"Groups (" & CountRows(colDiscoveryGroups) & ")"', "X": "196", "Y": "128", "Width": "160", "OnSelect": 'Set(varDiscoveryTab, "Groups"); ' + select, "DisplayMode": f'If({available}, DisplayMode.Edit, DisplayMode.Disabled)'}),
         control("galDiscovery", "Gallery@2.15.0", {"Items": items, "X": "24", "Y": "184", "Width": "Min(380, Parent.Width * 0.32)", "Height": "Parent.Height - 208", "TemplateSize": "108", "TemplateFill": "If(ThisItem.IsSelected, RGBA(225,239,250,1), RGBA(255,255,255,1))", "OnSelect": select, "DisplayMode": f'If({available}, DisplayMode.Edit, DisplayMode.Disabled)', "AccessibleLabel": '"Compatible people and groups"'}, [
             label("lblDiscoveryRowTitle", {"Text": "ThisItem.title", "X": "12", "Y": "8", "Width": "Parent.TemplateWidth - 24", "Height": "44", "FontWeight": "FontWeight.Semibold", "OnSelect": "Select(Parent)"}),
             label("lblDiscoveryRowSummary", {"Text": "ThisItem.summary", "X": "12", "Y": "54", "Width": "Parent.TemplateWidth - 24", "Height": "48", "OnSelect": "Select(Parent)"})], "BrowseLayout_Vertical_TwoTextVariant_ver5.0"),
         label("lblDiscoveryEmpty", {"Text": '"No compatible " & Lower(varDiscoveryTab) & " are available right now."', "X": "24", "Y": "192", "Width": "galDiscovery.Width", "Height": "100", "Visible": f'!varDiscoveryBusy && IsBlank(varDiscoveryError) && IsEmpty({items})'}),
         label("lblDiscoverySelected", {"Text": "galDiscovery.Selected.title", "X": "galDiscovery.X + galDiscovery.Width + 24", "Y": "184", "Width": "Parent.Width - Self.X - 24", "Height": "48", "Size": "20", "FontWeight": "FontWeight.Semibold"}),
         # A read-only multiline text input provides native scrolling and treats
         # Comments/introductions as plain text rather than HTML.
         control("txtDiscoveryDetails", "Classic/TextInput@2.3.2", {"Default": "galDiscovery.Selected.detail", "DisplayMode": "DisplayMode.View", "Mode": "TextMode.MultiLine", "X": "lblDiscoverySelected.X", "Y": "240", "Width": "Parent.Width - Self.X - 24", "Height": "Max(100, Parent.Height - 520)", "Size": "12", "AccessibleLabel": '"Exchange and member details"'}),
         label("lblDiscoveryIntroduction", {"Text": '"Introduction (optional, up to 2,000 characters)"', "X": "lblDiscoverySelected.X", "Y": "txtDiscoveryDetails.Y + txtDiscoveryDetails.Height + 8", "Width": "txtDiscoveryDetails.Width", "Height": "32", "Visible": 'varDiscoveryTab = "Groups" && !IsBlank(galDiscovery.Selected.targetId)'}),
         control("txtDiscoveryIntroduction", "Classic/TextInput@2.3.2", {"Default": '""', "Mode": "TextMode.MultiLine", "MaxLength": "2000", "X": "lblDiscoverySelected.X", "Y": "lblDiscoveryIntroduction.Y + 32", "Width": "txtDiscoveryDetails.Width", "Height": "64", "Visible": "lblDiscoveryIntroduction.Visible", "DisplayMode": 'If(IsBlank(varDiscoveryIntent) && !varDiscoverySending, DisplayMode.Edit, DisplayMode.Disabled)', "AccessibleLabel": '"Optional group introduction"'}),
         button("btnDiscoverySend", {"Text": 'If(varDiscoverySending, "Sending…", If(!IsBlank(varDiscoveryIntent), "Retry same request", If(varDiscoveryTab = "Groups", "Request to join", "Send request")))', "X": "lblDiscoverySelected.X", "Y": "txtDiscoveryIntroduction.Y + 76", "Width": "210", "DisplayMode": 'If(varDiscoveryBusy || varDiscoverySending || varDiscoveryConfirmed || (IsBlank(varDiscoveryIntent) && IsBlank(galDiscovery.Selected.targetId)), DisplayMode.Disabled, DisplayMode.Edit)', "OnSelect": SEND}),
         button("btnDiscoveryNewIntent", {"Text": '"Start a new request"', "X": "btnDiscoverySend.X + 222", "Y": "btnDiscoverySend.Y", "Width": "190", "Visible": "!IsBlank(varDiscoveryIntent)", "DisplayMode": 'If(varDiscoverySending, DisplayMode.Disabled, DisplayMode.Edit)', "OnSelect": 'Set(varDiscoveryIntent, Blank()); Set(varDiscoveryConfirmed, false); Set(varDiscoveryOutcome, "New request intent started. Check My requests first if the earlier result was uncertain."); Reset(txtDiscoveryIntroduction)'}),
         label("lblDiscoveryOutcome", {"Text": "varDiscoveryOutcome", "X": "lblDiscoverySelected.X", "Y": "btnDiscoverySend.Y + 48", "Width": "txtDiscoveryDetails.Width", "Height": "84"})]
    return {"Screens": {"scrDiscovery": {"Properties": {"Fill": "=RGBA(250,250,250,1)"}, "Children": c}}}


def dump_yaml(value, depth=0):
    """Emit only the JSON-compatible YAML subset, without a build dependency."""
    pad = "  " * depth
    if isinstance(value, dict):
        return "".join(pad + str(k) + ":" + ("\n" + dump_yaml(v, depth + 1) if isinstance(v, (dict, list)) else " " + json.dumps(v, ensure_ascii=False) + "\n") for k, v in value.items())
    return "".join(pad + "-\n" + dump_yaml(v, depth + 1) for v in value)


def flow_binding(template, name, spec, flow_id):
    d = deepcopy(template)
    d.update(Name=name, FlowNameId=flow_id, WorkflowEntityId=flow_id)
    root = ET.fromstring(d['WadlMetadata']['WadlXml'])
    ns = {'w': 'http://wadl.dev.java.net/2009/02', 's': 'http://schemas.microsoft.com/MicrosoftProjectSiena/WADL/2014/11'}
    root.set('{'+ns['s']+'}serviceId', name)
    root.find('w:doc', ns).set('title', name)
    types = root.find('w:grammars/s:jsonTypes', ns)
    types.clear(); types.set('targetNamespace', 'https://msmanaged-na.azure-apim.net/apim/logicflows')
    trigger = next(iter(spec['trigger'].values()))['inputs']['schema']
    output = next(iter(spec['responses'].values()))
    for objname, schema in [('ManualTriggerInput', trigger), ('ResponseActionOutput', output)]:
        obj = ET.SubElement(types, '{'+ns['s']+'}object', name=objname)
        for k, prop in schema['properties'].items():
            ET.SubElement(obj, '{'+ns['s']+'}property', name=k, type=prop['type'])
    request = root.find('.//w:request/w:representation', ns)
    request.clear();request.set('mediaType','application/json')
    for k, prop in trigger['properties'].items():
        ET.SubElement(request, '{'+ns['w']+'}param', style='plain', name=k, path='/'+k,
                      type='xs:double' if prop['type']=='number' else 'xs:string', required=str(k in trigger.get('required',[])).lower())
    # ElementTree rewrites prefixes, so keep the response element QName valid.
    response = root.find('.//w:response/w:representation', ns)
    response.set('element','service:ResponseActionOutput')
    root.set('xmlns:service','https://msmanaged-na.azure-apim.net/apim/logicflows')
    root.set('xmlns:xs','http://www.w3.org/2001/XMLSchema')
    d['WadlMetadata']['WadlXml'] = ET.tostring(root,encoding='unicode')
    return d


def build(source_dir, output_dir):
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    src = source_dir/'Src'
    original = src/'MainScreen1.pa.yaml'
    text = original.read_text(encoding='utf-8')
    start = text.index('                              - Discovery:')
    end = text.index('                              - SubmitFormButton1:', start)
    entry = '''If(Form1.Unsaved || newMode || IsBlank(RecordsGallery1.Selected.ID),
    Notify("Save or cancel your registration changes before opening Discovery.", NotificationType.Warning),
    If(!IsBlank(varDiscoveryIntent) && varDiscoveryActorId <> RecordsGallery1.Selected.ID,
        Notify("Finish or clear the earlier request intent before changing profiles.", NotificationType.Warning),
        Set(varDiscoveryActorId, RecordsGallery1.Selected.ID);
        Set(varDiscoveryTab, If(!IsBlank(varDiscoveryIntent) && varDiscoveryIntentKind = "Group", "Groups", "People"));
        Navigate(scrDiscovery, ScreenTransition.None);
        ''' + LOAD + '\n    )\n)'
    block = text[start:end]
    block = re.sub(r'(?s)(                                    OnSelect: \|-\r?\n).*?(                                    Text:)', lambda m:m[1]+'\n'.join('                                      '+l for l in ('='+entry).splitlines())+'\n'+m[2],block)
    original.write_text(text[:start]+block+text[end:],encoding='utf-8')
    (src/'scrDiscovery.pa.yaml').write_text(dump_yaml(screen()),encoding='utf-8')
    # The .msapr contains native references retained by PAC SourceCode packaging.
    archive = next(source_dir.glob('*.msapr'))
    with ZipFile(archive) as z: entries={n:z.read(n) for n in z.namelist()}
    data=json.loads(entries['msapp/References/DataSources.json'])
    properties=json.loads(entries['msapp/Properties.json'])
    refs=json.loads(properties['LocalConnectionReferences'])
    io=json.loads((ROOT/'artifacts/core_batch/v1.0.0.1/flow-io.json').read_text())
    review=json.loads((ROOT/'artifacts/core_batch/v1.0.0.1/TandemCoreBatch-v1.review.json').read_text())
    template=next(x for x in data['DataSources'] if x['Name']=='TandemSendRequest')
    ref_template=next(v for v in refs.values() if v.get('dataSources')==['TandemSendRequest'])
    mapping={}
    for name in ['TandemDiscovery','TandemSendRequest','TandemSendGroupJoinRequest']:
        flow_id=review['flows'][name]['id']; mapping[name]=flow_id
        data['DataSources']=[x for x in data['DataSources'] if x['Name']!=name]
        data['DataSources'].append(flow_binding(template,name,io[name],flow_id))
        old_ids=[k for k,v in refs.items() if v.get('dataSources')==[name]]
        for k in old_ids:del refs[k]
        ref=deepcopy(ref_template);key=str(uuid5(NAMESPACE_URL,'tandem-app16:'+name))
        ref.update(id=key,connectionInstanceId='/providers/microsoft.powerapps/apis/shared_logicflows/connections/'+flow_id,dataSources=[name])
        for hints in ['parameterHints','parameterHintsV2']:
            ref['connectionRef'][hints]['workflowName']={'value':flow_id}
            ref['connectionRef'][hints]['workflowEntityId']={'value':flow_id}
            ref['connectionRef'][hints]['workflowDisplayName']={'value':name}
        refs[key]=ref
        # Keep the participant connector's dependency graph consistent.
        for parent in refs.values():
            if name=='TandemSendGroupJoinRequest' and parent.get('dataSources')==['Participants']:
                parent.setdefault('dependents',[]).append(key)
            elif parent.get('dataSources')==['Participants']:
                parent['dependents']=[key if d in old_ids else d for d in parent.get('dependents',[])]
    properties['LocalConnectionReferences']=json.dumps(refs,separators=(',',':'))
    entries['msapp/Properties.json']=json.dumps(properties,ensure_ascii=False).encode()
    entries['msapp/References/DataSources.json']=json.dumps(data,ensure_ascii=False).encode()
    with ZipFile(archive,'w',ZIP_DEFLATED) as z:
        for n,b in entries.items():z.writestr(n,b)
    for n in ['MainScreen1.pa.yaml','scrDiscovery.pa.yaml']:
        (output_dir/n).write_bytes((src/n).read_bytes())
    (output_dir/'flow-bindings.json').write_text(json.dumps({'sourceTicket':16,'coreSolution':'TandemCoreBatch 1.0.0.1','sharedBuildId':review['sharedBuildId'],'bindings':mapping,'nativeBindingStatus':'NOT RUN: verify resolved flow IDs/connections in Power Apps Studio before executing'},indent=2)+'\n')
    print(json.dumps({'sourceTicket':16,'screenControls':len(screen()['Screens']['scrDiscovery']['Children']),'flowBindings':mapping,'nativeImport':'NOT RUN'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source_dir');p.add_argument('--output',default=str(DELIVERY));a=p.parse_args();build(a.source_dir,a.output)
