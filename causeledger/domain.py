"""Pure domain rules. No UI, storage, network or organization-specific rules."""
from copy import deepcopy
from datetime import date, datetime, timezone
from uuid import uuid4


class RuleError(ValueError):
    pass


def text(data, key, limit=4000):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise RuleError(f'{key} is required (1–{limit} characters)')
    return value.strip()


def choice(data, key, values):
    value = text(data, key)
    if value not in values:
        raise RuleError(f'{key} must be one of: {", ".join(values)}')
    return value


def due(data):
    value = text(data, 'due')
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError()
    except ValueError as exc:
        raise RuleError('due must be YYYY-MM-DD') from exc
    return value


def ref(items, identity):
    for item in items:
        if item['id'] == identity:
            return item
    raise RuleError('Referenced record does not exist in this case')


def evidence(case, identity):
    item = ref(case['evidence'], identity)
    if item['status'] != 'accepted':
        raise RuleError('Evidence must be explicitly reviewed and accepted')
    return item


def ready(case):
    """Always derived, including after evidence is withdrawn."""
    accepted = {e['id'] for e in case['evidence'] if e['status'] == 'accepted'}
    gaps = []
    if not case['containment'] or not all(
            c.get('proof') in accepted and c.get('release_proof') in accepted
            and c.get('disposition') for c in case['containment']):
        gaps.append('Containment scope, execution proof and release/disposition proof')
    verified = {c['id'] for c in case['causes']
                if c.get('proof') in accepted and c.get('verification') and c.get('result')}
    for kind in ('occurrence', 'escape'):
        if not any(c['kind'] == kind and c['id'] in verified for c in case['causes']):
            gaps.append(f'Verified {kind} cause with failure mechanism and test result')
    for cause in case['causes']:
        if cause['id'] not in verified:
            gaps.append(f'Unverified cause: {cause["claim"]}')
        actions = [a for a in case['actions'] if a['cause'] == cause['id']]
        if not actions:
            gaps.append(f'Corrective action for cause: {cause["claim"]}')
    if not case['actions']:
        gaps.append('At least one corrective action')
    for action in case['actions']:
        if action.get('proof') not in accepted:
            gaps.append(f'Implementation proof: {action["title"]}')
        result = action.get('effectiveness', {})
        if result.get('proof') not in accepted or result.get('outcome') != 'pass':
            gaps.append(f'Passing effectiveness result: {action["title"]}')
        elif date.fromisoformat(result['end']) > date.today():
            gaps.append(f'Effectiveness observation window still open: {action["title"]}')
    return gaps


def apply(case, data):
    """Return a new aggregate or raise, leaving the original unchanged."""
    c = deepcopy(case)
    operation = text(data, 'operation')
    if operation == 'reopen':
        if not c.get('closed'):
            raise RuleError('Case is already open')
        text(data, 'reason')
        c['closed'] = False
        return c
    if c.get('closed'):
        raise RuleError('Reopen the case before changing its records')
    item_id = str(uuid4())
    if operation == 'update_case':
        c.update(title=text(data, 'title', 200), problem=text(data, 'problem'),
                 owner=text(data, 'owner', 200), due=due(data))
    elif operation == 'add_evidence':
        c['evidence'].append(dict(id=item_id, title=text(data, 'title'),
                                 source=text(data, 'source'), observation=text(data, 'observation'),
                                 status='reported'))
    elif operation == 'review_evidence':
        item = ref(c['evidence'], text(data, 'id'))
        item.update(status=choice(data, 'status', ('accepted', 'rejected', 'withdrawn')),
                    reviewer=text(data, 'actor'), rationale=text(data, 'rationale'))
    elif operation == 'contain':
        c['containment'].append(dict(id=item_id, scope=text(data, 'scope'),
                                    identification=text(data, 'identification'),
                                    owner=text(data, 'owner'), due=due(data)))
    elif operation == 'confirm_containment':
        item = ref(c['containment'], text(data, 'id'))
        proof = text(data, 'proof'); evidence(c, proof)
        item['proof'] = proof
    elif operation == 'release_containment':
        item = ref(c['containment'], text(data, 'id'))
        evidence(c, item.get('proof'))
        proof = text(data, 'proof'); evidence(c, proof)
        item.update(release_proof=proof, disposition=text(data, 'disposition'))
    elif operation == 'add_cause':
        c['causes'].append(dict(id=item_id, kind=choice(data, 'kind', ('occurrence', 'escape')),
                               claim=text(data, 'claim'), mechanism=text(data, 'mechanism')))
    elif operation == 'verify_cause':
        item = ref(c['causes'], text(data, 'id'))
        proof = text(data, 'proof'); evidence(c, proof)
        item.update(proof=proof, verification=text(data, 'verification'), result=text(data, 'result'))
        for action in c['actions']:
            if action['cause'] == item['id']:
                action.pop('proof', None)
                action.pop('effectiveness', None)
    elif operation == 'add_action':
        cause = ref(c['causes'], text(data, 'cause'))
        evidence(c, cause.get('proof'))
        c['actions'].append(dict(id=item_id, cause=cause['id'], title=text(data, 'title'),
                                control=choice(data, 'control', ('prevention', 'detection')),
                                owner=text(data, 'owner'), due=due(data),
                                deliverable=text(data, 'deliverable'),
                                metric=text(data, 'metric'), target=text(data, 'target'),
                                window=text(data, 'window')))
    elif operation == 'implement_action':
        item = ref(c['actions'], text(data, 'id'))
        proof = text(data, 'proof'); evidence(c, proof)
        item['proof'] = proof
        item.pop('effectiveness', None)
    elif operation == 'record_effectiveness':
        item = ref(c['actions'], text(data, 'id'))
        evidence(c, item.get('proof'))
        proof = text(data, 'proof'); evidence(c, proof)
        start = text(data, 'start'); end = text(data, 'end')
        try:
            if not date.fromisoformat(start) <= date.fromisoformat(end) <= date.today():
                raise ValueError()
        except ValueError as exc:
            raise RuleError('Observation dates must be valid, ordered, and not in the future') from exc
        item['effectiveness'] = dict(proof=proof, start=start, end=end,
                                     outcome=choice(data, 'outcome', ('pass', 'fail')),
                                     result=text(data, 'result'))
    elif operation == 'close':
        gaps = ready(c)
        if gaps:
            raise RuleError('Closure blocked: ' + '; '.join(gaps))
        text(data, 'reason')
        c['closed'] = True
    else:
        raise RuleError('Unknown operation')
    return c


def new_case(data):
    return dict(id=str(uuid4()), title=text(data, 'title', 200),
                problem=text(data, 'problem'), owner=text(data, 'owner', 200),
                due=due(data), version=0, closed=False,
                evidence=[], containment=[], causes=[], actions=[])


def timestamp():
    return datetime.now(timezone.utc).isoformat()
