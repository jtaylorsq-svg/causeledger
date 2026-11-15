const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function harness() {
  const requests = [], rendered = [], elements = {};
  const document = { querySelector: s => elements[s] ||= {value:'', innerHTML:'', textContent:''}, querySelectorAll:()=>[] };
  const ctx = vm.createContext({document, window:{}, console, fetch:path=>new Promise(resolve=>requests.push({path,resolve}))});
  const source = fs.readFileSync('causeledger/static/app.js','utf8').replace("load().catch(e=>notice(e.message));",'');
  vm.runInContext(source,ctx);
  ctx.rendered=rendered;
  vm.runInContext('render=(c)=>rendered.push(c.id);',ctx);
  const reply=(i,data)=>requests[i].resolve({ok:true,json:async()=>data});
  const tick=()=>new Promise(resolve=>setImmediate(resolve));
  return {ctx,requests,rendered,elements,reply,tick};
}
const rows=[{case:{id:'A',title:'A',owner:'Demo',closed:false},gaps:[]},{case:{id:'B',title:'B',owner:'Demo',closed:false},gaps:[]}];
test('newer case selection wins over delayed prior response',async()=>{
  const h=harness(); const first=vm.runInContext("load('A')",h.ctx);
  h.reply(0,rows); await h.tick();
  const second=vm.runInContext("load('B')",h.ctx); h.reply(2,rows); await h.tick();
  h.reply(3,{case:rows[1].case,gaps:[],history:[]}); await second;
  h.reply(1,{case:rows[0].case,gaps:[],history:[]}); await first;
  assert.deepEqual(h.rendered,['B']);
});
test('New case cancels pending case view',async()=>{
  const h=harness(); const first=vm.runInContext("load('A')",h.ctx); h.reply(0,rows); await h.tick();
  vm.runInContext('newCase()',h.ctx);
  h.reply(1,{case:rows[0].case,gaps:[],history:[]}); await first;
  assert.deepEqual(h.rendered,[]); assert.match(h.elements['#main'].innerHTML,/New corrective-action case/);
});
test('delayed older list response cannot replace current selection',async()=>{
  const h=harness(); const first=vm.runInContext("load('A')",h.ctx);
  const second=vm.runInContext("load('B')",h.ctx); h.reply(1,rows); await h.tick();
  h.reply(2,{case:rows[1].case,gaps:[],history:[]}); await second;
  h.reply(0,rows); await first;
  assert.deepEqual(h.rendered,['B']); assert.equal(h.requests.length,3);
});
test('normal initial load still selects and renders first case',async()=>{
  const h=harness(); const first=vm.runInContext('load()',h.ctx);
  h.reply(0,rows); await h.tick(); h.reply(1,{case:rows[0].case,gaps:[],history:[]}); await first;
  assert.deepEqual(h.rendered,['A']);
});
test('empty initial list opens new case form',async()=>{
  const h=harness(); const first=vm.runInContext('load()',h.ctx); h.reply(0,[]); await first;
  assert.deepEqual(h.rendered,[]); assert.match(h.elements['#main'].innerHTML,/New corrective-action case/);
});
