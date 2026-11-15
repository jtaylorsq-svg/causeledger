"""Check exported event-chain integrity and materialized case consistency.

This detects inconsistency, not a malicious administrator recomputing the chain.
"""
import hashlib
import json
import sys


def verify(data):
    if data.get('format') != 'causeledger-export' or data.get('schema') != 1:
        raise ValueError('Unsupported export format/schema')
    previous=''; snapshots={}; seq=0
    for event in data['events']:
        expected=hashlib.sha256(json.dumps([previous,event['case_id'],event['at'],event['actor'],event['operation'],event['command'],event['snapshot']]).encode()).hexdigest()
        if event['previous_hash'] != previous or event['hash'] != expected or event['seq'] <= seq:
            raise ValueError('Event chain mismatch')
        snapshot=json.loads(event['snapshot'])
        if snapshot['id'] != event['case_id']:
            raise ValueError('Snapshot case mismatch')
        if snapshot['version'] != snapshots.get(snapshot['id'],{}).get('version',0)+1:
            raise ValueError('Snapshot revision mismatch')
        snapshots[snapshot['id']]=snapshot
        previous=event['hash'];seq=event['seq']
    if snapshots != {c['id']:c for c in data['cases']}:
        raise ValueError('Materialized cases differ from latest event snapshots')
    return len(data['events'])


def main():
    with open(sys.argv[1],encoding='utf-8') as stream:
        count=verify(json.load(stream))
    print(f'Consistent export: {count} events. This is not proof of authenticity.')


if __name__ == '__main__':main()
