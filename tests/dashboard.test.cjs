// Exercises the shipped application and its event handlers without a browser.
// This harness verifies logic and exports, not CSS layout or real DOM semantics.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const elements = new Map();
class Element {
  constructor(){this.innerHTML='';this.textContent='';this.value='';this.type='search';this.events={};this.dataset={};this.attributes={};this.classList={add(){},remove(){},toggle(){}};}
  addEventListener(event,fn){this.events[event]=fn;}
  setAttribute(key,value){this.attributes[key]=value;}
  removeAttribute(key){delete this.attributes[key];}
  focus(){} setSelectionRange(){} append(){} remove(){}
  click(){this.clicked=true;}
}
const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const links=['overview','customers','products','methodology'].map(page=>Object.assign(new Element(),{dataset:{page}}));
let exported;
const window={events:{},scrollTo(){},addEventListener(event,fn){this.events[event]=fn;}};
const location={hash:'#overview'};
const sandbox={window,location,document:{querySelector:selector=>get(selector.slice(1)),querySelectorAll:()=>links,getElementById:get,createElement:()=>new Element(),body:new Element()},Intl,console,Blob,URL:{createObjectURL(blob){exported=blob;return 'blob:test';},revokeObjectURL(){}},setTimeout(fn){fn();}};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root,'dist/data.js'),'utf8'),sandbox);
vm.runInContext(fs.readFileSync(path.join(root,'dist/app.js'),'utf8'),sandbox);
const html=()=>get('content').innerHTML;
const change=(id,value)=>{get(id).value=value;get(id).events.change({target:get(id)});};
const route=page=>{location.hash='#'+page;window.events.hashchange();};
const format=p=>new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP',maximumFractionDigits:0}).format(p/100);
const d=window.RETAIL_DATA;
(async()=>{
  assert.ok(html().includes('£10,247,219'));
  assert.ok(html().includes('19,773'));
  assert.ok(html().includes('4,334'));
  change('country','France');
  change('from','2011-02');
  change('to','2011-04');
  const selected=d.invoices.filter(r=>r[0]==='France'&&r[1]>='2011-02'&&r[1]<='2011-04');
  assert.ok(html().includes(format(selected.reduce((a,r)=>a+r[2],0))));
  get('export').events.click();
  let csv=await exported.text();
  assert.ok(csv.includes('France'));
  assert.ok(csv.includes('2011-02'));
  assert.ok(!csv.includes('2011-05'));
  change('from','2011-11'); // Inverted range must be corrected.
  assert.ok(html().includes('value="2011-11" selected'));
  route('customers');
  assert.ok(html().includes('Do customers come back?'));
  assert.ok(html().includes('Not yet observable'));
  change('customer-country','France');
  get('export').events.click();
  csv=await exported.text();
  assert.ok(csv.includes('Champions'));
  assert.ok(csv.includes('France'));
  assert.equal(csv.split('\r\n').length,7);
  route('products');
  change('product-country','United Kingdom');
  const before=html();get('next').events.click();
  assert.notEqual(html(),before);
  assert.ok(html().includes('Page 2 /'));
  get('search').value='zzzz_no_such_product_987';
  get('search').events.input({target:get('search')});
  assert.ok(html().includes('No matching products'));
  get('search').value='WHITE HANGING HEART';
  get('search').events.input({target:get('search')});
  assert.ok(html().includes('WHITE HANGING HEART'));
  change('sort','units');
  get('export').events.click();
  csv=await exported.text();
  assert.ok(csv.includes('WHITE HANGING HEART'));
  assert.ok(csv.includes('United Kingdom'));
  route('methodology');
  assert.ok(html().includes('541,909'));
  assert.ok(html().includes('£1,631.63'));
  get('export').events.click();
  assert.ok((await exported.text()).includes('Exact duplicate rows'));
  route('unknown');
  assert.ok(html().includes('Sales over time'));
  console.log('PASS: all routes, country/date filtering, range correction, segment exports, product search/sort/pagination, empty state, CSV exports and fallback routing.');
})().catch(error=>{console.error(error);process.exitCode=1;});
