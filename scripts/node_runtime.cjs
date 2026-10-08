// Portable package/browser discovery for the pipeline and optional helpers.
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const root=path.resolve(__dirname,'..');
function moduleDirectory(){
  if(process.env.PIPELINE_NODE_MODULES)return path.resolve(process.env.PIPELINE_NODE_MODULES);
  const local=path.join(root,'node_modules');
  if(['playwright','@viz-js/viz'].every(name=>fs.existsSync(path.join(local,name,'package.json'))))return local;
  return path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
}
function load(name,modules=moduleDirectory()){return require(path.join(modules,name));}
async function launchBrowser(modules=moduleDirectory()){
  const chromium=load('playwright',modules).chromium;
  const channel=process.env.PIPELINE_BROWSER_CHANNEL||'auto';
  if(channel!=='auto')return chromium.launch({headless:true,...(channel==='chromium'?{}:{channel})});
  try{return await chromium.launch({headless:true});}
  catch{
    try{return await chromium.launch({headless:true,channel:'msedge'});}
    catch{throw new Error('No usable browser. Run npm run install:browsers, or configure an installed PIPELINE_BROWSER_CHANNEL.');}
  }
}
module.exports={load,launchBrowser,moduleDirectory};
