"""Entirely fictional training examples, not production data."""
from .domain import ready


def seed(store):
    actor = 'Demo facilitator (fictional)'
    case = store.write(dict(title='DEMO · Washer omitted at assembly',
                            problem='Fictional training case: expected one washer per handwheel. A bench check found 3 missing washers in a lot of 60 training assemblies.',
                            owner='Demo quality lead', due='2026-11-20', actor=actor))

    def run(operation, **data):
        nonlocal case
        case = store.write(dict(operation=operation, actor=actor, version=case['version'], **data), case['id'])
        return case

    def proof(title, observation):
        run('add_evidence', title=title, source='Fictional training record / '+title, observation=observation)
        identity = case['evidence'][-1]['id']
        run('review_evidence', id=identity, status='accepted', rationale='Fictional example reviewed for training; no real product tested.')
        return identity

    p1 = proof('Lot reconciliation', 'Training lot T-017: all 60 units held and counted. 57 conforming, 3 reworked; no external stock in this fictional scenario.')
    run('contain', scope='All 60 units in fictional training lot T-017', identification='Labeled HOLD tray; segregated at the demonstration bench', owner='Demo production lead', due='2026-11-01')
    containment = case['containment'][-1]['id']
    run('confirm_containment', id=containment, proof=p1)
    p2 = proof('Disposition review', 'Demo quality lead reviewed 60/60 washer checks, including 3 reworked units; approved release of fictional training population.')
    run('release_containment', id=containment, proof=p2, disposition='Demo quality lead approved the training lot after 100% reconciliation and recheck.')
    for kind, claim, mechanism, test, result, action, control, metric, target in [
        ('occurrence', 'The fixture allows handwheel assembly without a washer', 'The locating pin accepts the handwheel with an empty washer pocket.', 'Challenge fixture with and without washer, 10 trials per condition.', 'Assembly possible in all 10 missing-washer trials before fixture change.', 'Install washer-presence pin in training fixture', 'prevention', 'Assembly permitted without washer', '0 successful assemblies without washer in 30 challenges'),
        ('escape', 'Final rotation check does not distinguish a missing washer', 'Handwheel rotation remains possible with a washer absent.', 'Blind challenge the rotation check using 10 missing and 10 present washers.', 'The original rotation check accepted 10/10 missing-washer units.', 'Add validated washer-presence check to final inspection', 'detection', 'Missing-washer challenge detection', '30/30 challenge units rejected')
    ]:
        run('add_cause', kind=kind, claim=claim, mechanism=mechanism)
        cause = case['causes'][-1]['id']
        p = proof(kind+' challenge', result)
        run('verify_cause', id=cause, proof=p, verification=test, result=result)
        run('add_action', cause=cause, title=action, control=control, owner='Demo manufacturing engineer', due='2026-11-10', deliverable='Revised fixture or inspection method, validation record and controlled instruction', metric=metric, target=target, window='30 challenges followed by 3 training lots of 60 units')
        identity=case['actions'][-1]['id']
        p=proof(kind+' implementation', 'Fictional fixture/check revision installed and validation completed; revision logged in training record.')
        run('implement_action', id=identity, proof=p)
        if kind == 'occurrence':
            p=proof('Occurrence effectiveness', 'Fictional result: 0/30 missing-washer challenges assembled; 0 missing washers across 3 lots of 60 units.')
            run('record_effectiveness', id=identity, proof=p, start='2026-10-01', end='2026-10-08', outcome='pass', result='0/30 invalid assemblies permitted and 0 missing washers in 180 training units. Planned sample window completed.')
    store.write(dict(title='DEMO · Inspection lamp drift', problem='Fictional training example: illumination at a visual check varied from 400 to 700 lux against a demonstration target of 600 ±50 lux. Effect on detection is not yet verified.', owner='Demo process engineer', due='2026-11-25', actor=actor))
    return case
