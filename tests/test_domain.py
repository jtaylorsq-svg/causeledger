import copy
import tempfile
import unittest
from pathlib import Path
from causeledger.demo import seed
from causeledger.domain import RuleError, apply, new_case, ready
from causeledger.store import Store, Conflict


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name)/'test.sqlite3')
        self.case = seed(self.store)

    def write(self, operation, **data):
        self.case = self.store.write(dict(operation=operation, version=self.case['version'], actor='Test reviewer', **data), self.case['id'])
        return self.case

    def accepted(self):
        self.write('add_evidence', title='Test result', source='Test source', observation='Measured result')
        identity = self.case['evidence'][-1]['id']
        self.write('review_evidence', id=identity, status='accepted', rationale='Reviewed source and method')
        return identity

    def finish(self):
        identity = self.accepted()
        self.write('record_effectiveness', id=self.case['actions'][-1]['id'], proof=identity,
                   start='2026-01-01', end='2026-01-03', outcome='pass', result='30/30 challenge defects rejected across planned window')

    def test_demo_stops_at_real_gap(self):
        self.assertEqual(len(ready(self.case)), 1)
        self.assertIn('effectiveness', ready(self.case)[0])

    def test_close_rejects_incomplete_atomically(self):
        before=self.store.export()
        with self.assertRaises(RuleError): self.write('close', reason='Looks done')
        self.assertEqual(before['events'], self.store.export()['events'])

    def test_full_close_and_reopen(self):
        self.finish()
        self.assertEqual(ready(self.case), [])
        self.write('close', reason='All planned criteria met')
        self.assertTrue(self.case['closed'])
        with self.assertRaises(RuleError): self.accepted()
        self.write('reopen', reason='Additional information')
        self.assertFalse(self.case['closed'])

    def test_withdrawal_reblocks_cause(self):
        self.finish()
        self.write('review_evidence', id=self.case['causes'][0]['proof'], status='withdrawn', rationale='Invalid source')
        self.assertTrue(any('occurrence' in g for g in ready(self.case)))
        with self.assertRaises(RuleError): self.write('close', reason='Ignore invalid proof')

    def test_rejection_reblocks_effectiveness(self):
        self.finish()
        self.write('review_evidence',id=self.case['actions'][-1]['effectiveness']['proof'],status='rejected',rationale='Wrong lot')
        self.assertTrue(ready(self.case))

    def test_failed_effectiveness_blocks(self):
        self.finish()
        a=self.case['actions'][-1]
        self.write('record_effectiveness', id=a['id'],proof=a['effectiveness']['proof'],start='2026-01-01',end='2026-01-03',outcome='fail',result='One missed challenge')
        with self.assertRaises(RuleError): self.write('close',reason='Done')

    def test_reimplementation_clears_effectiveness(self):
        self.finish();a=self.case['actions'][-1]
        self.write('implement_action',id=a['id'],proof=a['proof'])
        self.assertNotIn('effectiveness',self.case['actions'][-1])
        self.assertTrue(ready(self.case))

    def test_stale_revision(self):
        old=self.case['version'];self.accepted()
        with self.assertRaises(Conflict):self.store.write(dict(operation='close',version=old,actor='Reviewer',reason='Test'),self.case['id'])

    def test_unverified_cause_cannot_get_action(self):
        self.write('add_cause',kind='occurrence',claim='Hypothesis',mechanism='Interaction')
        with self.assertRaises(RuleError):self.write('add_action',cause=self.case['causes'][-1]['id'])

    def test_reported_is_not_accepted(self):
        self.write('add_evidence',title='Unreviewed',source='Sheet',observation='Observation')
        with self.assertRaises(RuleError):self.write('verify_cause',id=self.case['causes'][0]['id'],proof=self.case['evidence'][-1]['id'],verification='Test',result='Result')

    def test_foreign_reference(self):
        with self.assertRaises(RuleError):self.write('verify_cause',id='foreign-case-id',proof=self.case['evidence'][0]['id'])

    def test_bad_due_date(self):
        with self.assertRaises(RuleError):self.write('contain',scope='Lot',identification='Hold',owner='Lead',due='bad')

    def test_bad_observation_dates(self):
        a=self.case['actions'][-1]
        for start,end in [('2026-04-02','2026-04-01'),('2099-01-01','2099-01-02'),('bad','2026-01-01')]:
            with self.subTest(start=start):
                with self.assertRaises(RuleError):self.write('record_effectiveness',id=a['id'],proof=a['proof'],start=start,end=end,outcome='pass',result='Result')

    def test_requires_actor(self):
        with self.assertRaises(RuleError):self.store.write(dict(title='Title',problem='Problem',owner='Owner',due='2026-11-01'))

    def test_invalid_shape(self):
        with self.assertRaises(RuleError):self.store.write([])
        with self.assertRaises(RuleError):self.write('unsupported')

    def test_failure_does_not_mutate(self):
        before=copy.deepcopy(self.case)
        with self.assertRaises(RuleError):apply(self.case,dict(operation='verify_cause',id=self.case['causes'][0]['id'],proof=self.case['evidence'][0]['id']))
        self.assertEqual(before,self.case)

    def test_event_history_append_only(self):
        import sqlite3
        with self.store.connect() as db:
            with self.assertRaises(sqlite3.IntegrityError):db.execute('DELETE FROM events')
            with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE events SET actor='Other'")

    def test_reload_export(self):
        self.finish()
        self.assertEqual(Store(self.store.path).get(self.case['id']),self.case)
        out=self.store.export()
        self.assertEqual(out['schema'],1)
        self.assertGreater(len(out['events']),20)
        self.assertEqual(len(out['cases']),2)

    def test_every_containment_needs_disposition(self):
        self.finish()
        self.write('contain',scope='Additional lot',identification='Hold',owner='Lead',due='2026-11-01')
        self.assertTrue(ready(self.case))

    def test_empty_case_gaps(self):
        c=new_case(dict(title='Title',problem='Expected vs observed',owner='Owner',due='2026-11-01'))
        self.assertEqual(len(ready(c)),4)

    def test_extra_hypothesis_blocks(self):
        self.finish()
        self.write('add_cause',kind='escape',claim='Open hypothesis',mechanism='Unknown interaction')
        self.assertTrue(any('Unverified cause' in g for g in ready(self.case)))

    def test_reverified_cause_invalidates_downstream(self):
        self.finish();cause=self.case['causes'][0]
        self.write('verify_cause',id=cause['id'],proof=cause['proof'],verification='New challenge method',result='Revised result')
        action=self.case['actions'][0]
        self.assertNotIn('proof',action)
        self.assertNotIn('effectiveness',action)
        self.assertTrue(ready(self.case))

    def test_correct_facts_preserves_history(self):
        before=len(self.store.history(self.case['id']))
        self.write('update_case',title='Corrected title',problem='Corrected problem',owner='New owner',due='2026-11-30')
        self.assertEqual(self.case['owner'],'New owner')
        self.assertEqual(len(self.store.history(self.case['id'])),before+1)

    def test_export_integrity_detects_tamper(self):
        from causeledger.verify import verify
        data=self.store.export()
        self.assertGreater(verify(data),20)
        data['events'][0]['actor']='Altered'
        with self.assertRaises(ValueError):verify(data)

    def test_export_detects_projection_mismatch(self):
        from causeledger.verify import verify
        data=self.store.export();data['cases'][0]['owner']='Altered'
        with self.assertRaises(ValueError):verify(data)
