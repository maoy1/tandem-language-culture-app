"""Contract mutation checks; not Power Apps execution or participant runtime code."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.sharepoint.validate_registration import validate
from scripts.power_automate.schema_audit import expected_schema

ROOT=Path(__file__).resolve().parents[1]
def load():
    return (json.loads((ROOT/'config/participant_registration.json').read_text(encoding='utf-8')),
            json.loads((ROOT/'config/sharepoint_schema.json').read_text(encoding='utf-8')))
def field(schema,name):
    return next(f for l in schema['lists'] if l['name']=='Participants' for f in l['fields'] if f['internalName']==name)

@pytest.mark.parametrize('key,value',[
    ('defaultsApplyOnlyToNewProfiles',False),('preserveExistingChoices',False),
    ('validationMayReset',True),('newProfileOpenDefault',False),
    ('newProfileDefault','Paused'),('membershipSideEffects','delete_membership'),
    ('defaultSource','sharepoint_form_new_mode'),('defaultSource','explicit_new_mode_card_default'),
    ('newProfileDefaultType','text'),('newProfileDefaultType','choice_record'),
    ('existingProfileDefaultSource','always_active')])
def test_rejects_contracts_that_reset_availability_or_change_memberships(key,value):
    policy,schema=load();policy['participation'][key]=value
    assert any('Participation contract' in e for e in validate(policy,schema))

@pytest.mark.parametrize('name,property,value',[
    ('ParticipationStatus','type','Text'),('ParticipationStatus','defaultValue','Inactive'),
    ('ParticipationStatus','choices',['Active','Needs review']),
    ('OpenToConnections','type','Choice'),('OpenToConnections','defaultValue',False),
    ('OpenToConnections','required',False)])
def test_rejects_wrong_types_validation_status_mixups_and_defaults(name,property,value):
    policy,schema=load();field(schema,name)[property]=value
    assert validate(policy,schema)

@pytest.mark.parametrize('name',['ParticipationStatus','OpenToConnections'])
def test_availability_controls_cannot_be_hidden_in_form_contract(name):
    policy,schema=load();policy['form']['visibleFields'].remove(name)
    policy['form']['hiddenFields'].append(name)
    assert any('visible/editable' in e for e in validate(policy,schema))

def test_false_boolean_is_not_treated_as_an_absent_new_default():
    policy,schema=load();policy['participation']['newProfileOpenDefault']=1
    assert validate(policy,schema)  # Integer 1 must not be silently accepted as JSON true.

def test_schema_audit_keeps_one_copy_of_newly_promoted_fields():
    schema=expected_schema(ROOT)
    people=next(l for l in schema['lists'] if l['name']=='Participants')
    names=[f['internalName'] for f in people['fields']]
    assert names.count('ParticipationStatus')==names.count('OpenToConnections')==1
    policy,_=load()
    assert validate(policy,schema)==[]
