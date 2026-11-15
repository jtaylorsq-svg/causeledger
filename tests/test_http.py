import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from causeledger.server import make_server
from causeledger.store import Store

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.temp.name)/'test.sqlite3')
        self.server=make_server(self.store,0)
        self.port=self.server.server_port
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start();self.addCleanup(self.cleanup)
    def cleanup(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def request(self,method,path,data=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        h={'Content-Type':'application/json','Origin':f'http://127.0.0.1:{self.port}'}
        if headers:h.update(headers)
        conn.request(method,path,json.dumps(data) if data is not None else None,h)
        response=conn.getresponse();result=response.status,dict(response.getheaders()),response.read();conn.close();return result
    def test_create_reload_export(self):
        status,_,raw=self.request('POST','/api/cases',dict(actor='Tester',title='Case',problem='Expected vs observed',owner='Lead',due='2026-11-01'))
        self.assertEqual(status,200);c=json.loads(raw)['case']
        self.assertEqual(self.request('GET','/api/cases/'+c['id'])[0],200)
        self.assertEqual(len(json.loads(self.request('GET','/api/export')[2])['events']),1)
    def test_cross_origin_blocked(self):
        for origin in ('https://evil.example',''):
            self.assertEqual(self.request('POST','/api/cases',{}, {'Origin':origin})[0],403)
    def test_host_blocked(self):
        self.assertEqual(self.request('GET','/api/export',headers={'Host':'evil.example'})[0],403)
    def test_bad_shape(self):
        self.assertEqual(self.request('POST','/api/cases',[])[0],400)
    def test_content_type(self):
        self.assertEqual(self.request('POST','/api/cases',{}, {'Content-Type':'text/plain'})[0],415)
    def test_size_limit(self):
        self.assertEqual(self.request('POST','/api/cases',{'value':'x'*66000})[0],413)
    def test_static_security_and_traversal(self):
        status,headers,body=self.request('GET','/')
        self.assertEqual(status,200);self.assertIn(b'CauseLedger',body)
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertEqual(self.request('GET','/../store.py')[0],404)
        self.assertEqual(self.request('GET','/api/cases/missing')[0],404)
