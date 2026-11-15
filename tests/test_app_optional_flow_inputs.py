"""Regress the native Text-versus-Record failure reported on Discovery Send."""
from scripts.build_integrated_app import repair_discovery, LEGACY_JOIN_CALL, FIXED_JOIN_CALL
from scripts import build_discovery_app as discovery
from scripts.verify_integrated_app import run_arguments, optional_arguments_valid


SCHEMA={'properties':{'number':{},'text':{},'text_1':{}},'required':['number','text']}


def test_rejects_old_positional_optional_text():
    _,args=next(run_arguments(LEGACY_JOIN_CALL))
    assert not optional_arguments_valid(SCHEMA,args)


def test_accepts_optional_record_and_omission():
    _,args=next(run_arguments(FIXED_JOIN_CALL))
    assert optional_arguments_valid(SCHEMA,args)
    assert optional_arguments_valid(SCHEMA,args[:2])
    assert not optional_arguments_valid(SCHEMA,args[:2]+['{wrong_key: "value"}'])


def test_nested_argument_and_quoted_comma_are_single_arguments():
    _,args=next(run_arguments('TandemExample.Run(Value("1"), "a,b", {text_1: If(true, "a,b", "c")})'))
    assert len(args)==3
    assert optional_arguments_valid(SCHEMA,args)


def test_repair_changes_only_send_formula_and_preserves_original():
    original=discovery.screen()
    result=repair_discovery(original)
    assert original==discovery.screen()
    button=next(c['btnDiscoverySend'] for c in result['Screens']['scrDiscovery']['Children'] if 'btnDiscoverySend' in c)
    assert FIXED_JOIN_CALL in button['Properties']['OnSelect']
    button['Properties']['OnSelect']=button['Properties']['OnSelect'].replace(FIXED_JOIN_CALL,LEGACY_JOIN_CALL)
    assert result==original
