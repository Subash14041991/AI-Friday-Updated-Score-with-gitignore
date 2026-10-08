// Trusted runtime adapter: graph rendering, report QA, and opt-in POC tests.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {pathToFileURL,fileURLToPath}=require('node:url');
const http=require('node:http');
const [operation,modules,...args]=process.argv.slice(2);
const load=name=>require(path.join(modules,name));

function parseDiagram(source){
  const groups=[],nodes=[],edges=[];let group=null;
  for(const raw of source.split('\n')){
    const line=raw.trim().replace(/;$/,'');if(!line||line.startsWith('%%'))continue;
    if(line==='flowchart LR'||line==='graph LR')continue;
    let m;
    if((m=line.match(/^subgraph\s+(\w+)\s*\["([^"]+)"\]$/))){
      if(group)throw new Error('Nested groups are not supported. Use at most three simple groups.');
      group={id:m[1],label:m[2]};groups.push(group);
    }else if(line==='end'){if(!group)throw new Error('Unexpected end.');group=null;
    }else if((m=line.match(/^(\w+)\s*\["([^"]+)"\]$/))){
      nodes.push({id:m[1],label:m[2].replace(/<br\s*\/?\s*>/g,'\n'),group:group?.id});
    }else if((m=line.match(/^(\w+)\s*(-->|<-->)\s*(?:\|"([^"]*)"\|\s*)?(\w+)$/))){
      edges.push({from:m[1],to:m[4],both:m[2]==='<-->',label:m[3]||''});
    }else throw new Error('Unsupported diagram line: '+line+'. Use separately declared quoted boxes and labeled --> or <--> flows.');
  }
  if(group)throw new Error('Unclosed diagram group.');
  if(nodes.length<2||nodes.length>10||groups.length>3)throw new Error('Use 2–10 boxes and at most three groups.');
  const ids=new Set(nodes.map(n=>n.id));
  if(ids.size!==nodes.length||new Set(groups.map(g=>g.id)).size!==groups.length)throw new Error('Duplicate diagram IDs.');
  for(const e of edges)if(!ids.has(e.from)||!ids.has(e.to))throw new Error('Unknown diagram endpoint.');
  for(const n of nodes)if(!edges.some(e=>e.from===n.id||e.to===n.id))throw new Error('Disconnected diagram box: '+n.id);
  return {groups,nodes,edges};
}

async function diagram(){
  const [input,output]=args,md=fs.readFileSync(input,'utf8');
  const blocks=[...md.matchAll(/```mermaid\s*\n([\s\S]*?)```/g)];
  if(blocks.length!==1)throw new Error('Expected one Mermaid flowchart.');
  const {groups,nodes,edges}=parseDiagram(blocks[0][1]),q=JSON.stringify;
  const people=new Set(nodes.filter(n=>groups.some(g=>g.id===n.group&&/people|users|participants|channels/i.test(g.label))).map(n=>n.id));
  let dot='digraph Architecture { graph [rankdir=LR,bgcolor="transparent",pad=0.2,nodesep=0.5,ranksep=0.7,splines=polyline,fontname="Arial",fontsize=24]; node [shape=box,style="rounded,filled",fillcolor="white",color="#50798c",fontcolor="#173047",fontname="Arial",fontsize=22,margin="0.2,0.15"]; edge [color="#315b73",fontcolor="#315b73",fontname="Arial",fontsize=17,penwidth=1.5];\n';
  for(const g of groups){
    dot+=`subgraph cluster_${g.id} { label=${q(g.label)}; style="rounded,filled"; color="#a4becb"; fillcolor="#f1f7fa"; margin=18;\n`;
    if(/people|users|participants|channels/i.test(g.label))dot+='rank=same;\n';
    for(const n of nodes.filter(n=>n.group===g.id))dot+=`${n.id} [label=${q(n.label)}];\n`;
    dot+='}\n';
  }
  for(const n of nodes.filter(n=>!n.group))dot+=`${n.id} [label=${q(n.label)}];\n`;
  for(const e of edges)dot+=`${e.from} -> ${e.to} [label=${q(e.label)}${e.both?',dir=both':''}${people.has(e.to)?',constraint=false':''}];\n`;
  const viz=await load('@viz-js/viz').instance();
  let svg=viz.renderString(dot+'}',{format:'svg'});
  svg=svg.slice(svg.indexOf('<svg')).replace(/width="[^"]+" height="[^"]+"/,'class="architecture-diagram" role="img" aria-label="Proposed target-state architecture"');
  fs.writeFileSync(output,svg);
  return {status:'PASS',nodes:nodes.length,flows:edges.length,source:'D3 Mermaid subset; labels, groups and directions preserved'};
}

async function withBrowser(fn){
  const browser=await require('./node_runtime.cjs').launchBrowser(modules);
  try{return await fn(browser);}finally{await browser.close();}
}

async function report(){
  const [file,outputDir]=args;
  return withBrowser(async browser=>{
    const page=await browser.newPage({viewport:{width:1600,height:1200}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',route=>{const url=new URL(route.request().url());return ['file:','data:','about:'].includes(url.protocol)?route.continue():route.abort();});
    await page.goto(pathToFileURL(path.resolve(file)).href);await page.waitForLoadState('load');
    assert.equal(await page.locator('section.page').count(),5,'Report must have five sections.');
    assert.equal(await page.locator('.architecture-diagram').count(),1,'Diagram must be rendered.');
    const links=await page.locator('a').evaluateAll(els=>els.map(el=>el.href));
    for(const href of links)if(href.startsWith('file:')){
      const target=fileURLToPath(href);
      assert.ok(target.startsWith(path.dirname(path.resolve(file))+path.sep),'Report link escapes its run folder: '+href);
      assert.equal(fs.existsSync(target),true,'Missing report link: '+href);
    }
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Screen overflow.');
    for(let i=0;i<5;i++)await page.locator('section.page').nth(i).screenshot({path:path.join(outputDir,`page-${i+1}.png`)});
    await page.emulateMedia({media:'print'});
    const layouts=await page.locator('section.page').evaluateAll(els=>els.map((el,i)=>{
      const box=el.getBoundingClientRect(),foot=el.querySelector('footer').getBoundingClientRect();
      const content=[...el.querySelectorAll('article, .report-body')].map(x=>x.getBoundingClientRect());
      return {page:i+1,width:el.clientWidth,height:el.clientHeight,scrollWidth:el.scrollWidth,scrollHeight:el.scrollHeight,
        contentBottom:Math.max(box.top,...content.map(x=>x.bottom))-box.top,footerTop:foot.top-box.top};
    }));
    for(const l of layouts){assert.ok(l.scrollWidth<=l.width+1,`Page ${l.page} width overflow`);assert.ok(l.scrollHeight<=l.height+1,`Page ${l.page} height overflow`);assert.ok(l.contentBottom<=l.footerTop,`Page ${l.page} overlaps footer`);}
    assert.deepEqual(errors,[]);
    await page.pdf({path:path.join(outputDir,'final-submission-report.pdf'),preferCSSPageSize:true,printBackground:true});
    await page.setViewportSize({width:390,height:844});await page.emulateMedia({media:'screen'});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Mobile report overflow.');
    return {executedAt:new Date().toISOString(),status:'PASS',checks:['Five report sections','Rendered architecture','Local links exist','Desktop/mobile width fits','All five print pages fit without clipping or footer overlap','No script errors'],layouts};
  });
}

async function poc(){
  const [root,entry,test,seconds]=args;
  // Loopback transport is controlled by this trusted wrapper. Generated code
  // is explicitly opted into by the caller; this is not an OS sandbox.
  const server=http.createServer((req,res)=>{
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=path.resolve(root,'.'+pathname);
    if(!file.startsWith(path.resolve(root)+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
    const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'};
    res.setHeader('Content-Type',types[path.extname(file)]||'text/plain');fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin=`http://127.0.0.1:${server.address().port}`;
  try{return await withBrowser(async browser=>{
    const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.setDefaultTimeout(Math.min(Number(seconds)*1000,30000));
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',route=>{const url=route.request().url();return url.startsWith(origin+'/')||url.startsWith('data:')?route.continue():route.abort();});
    await page.goto(origin+'/'+entry);
    const run=require(path.resolve(root,test));assert.equal(typeof run,'function','Browser test must export an async function.');
    await run({page,assert,baseURL:origin,root});
    assert.deepEqual(errors,[]);
    return {path:test,result:'PASS',output:'Browser test completed in an isolated profile; external browser requests blocked.'};
  });}finally{await new Promise(resolve=>server.close(resolve));}
}

(async()=>{
  const result=operation==='preflight'?(await load('@viz-js/viz').instance(),await withBrowser(async()=>({status:'PASS',graph:'ready',browser:'ready'}))):operation==='diagram'?await diagram():operation==='report'?await report():operation==='poc'?await poc():(()=>{throw new Error('Unknown operation.');})();
  process.stdout.write(JSON.stringify(result));
})().catch(error=>{process.stderr.write(error.stack||String(error));process.exitCode=1;});
