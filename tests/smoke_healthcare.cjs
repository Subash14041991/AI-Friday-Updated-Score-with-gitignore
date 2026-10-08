const {launchBrowser}=require('../scripts/node_runtime.cjs');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
(async () => {
  const browser = await launchBrowser();
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    const folder = path.resolve(__dirname, '../output/healthcare');
    await page.goto(pathToFileURL(path.join(folder,'poc-referral-validation.html')).href);
    await page.locator('#validate').click(); assert.equal(await page.locator('.record').count(),5);
    const first = page.locator('.record').filter({has:page.getByRole('heading',{name:'REF-SYN-001',exact:true})});
    await first.getByRole('button',{name:'Simulate send'}).click();
    await first.getByRole('button',{name:'Simulate partner receipt'}).click();
    assert.match(await first.innerText(), /Partner acknowledged/);
    const silent = page.locator('.record').filter({has:page.getByRole('heading',{name:'REF-SYN-005',exact:true})});
    await silent.getByRole('button',{name:'Simulate send'}).click();
    await page.locator('#advance').click(); assert.match(await silent.innerText(), /Acknowledgement overdue/);
    await silent.locator('[data-actor]').fill('Synthetic coordinator');
    await silent.locator('[data-reason]').fill('Mock partner contacted; retry approved');
    await silent.getByRole('button',{name:'Approve retry'}).click();
    await silent.getByRole('button',{name:'Simulate send'}).click();
    await silent.getByRole('button',{name:'Simulate partner receipt'}).click();
    await page.locator('#duplicate').click(); assert.equal(await page.locator('.record').count(),5);
    assert.match(await page.locator('#audit').innerText(), /Human retry approval/);
    assert.match(await page.locator('#audit').innerText(), /Duplicate ignored/);
    await page.screenshot({path:path.join(folder,'poc-validated.png'),fullPage:true});
    await page.goto(pathToFileURL(path.join(folder,'final-submission-report.html')).href);
    assert.equal(await page.locator('section.page').count(),5);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    // Wide A3 report is intentionally scaled by width; no horizontal document overflow expected.
    assert.equal(overflow,false);
    await page.screenshot({path:path.join(folder,'report-preview.png'),fullPage:true});
    await page.emulateMedia({media:'print'});
    await page.pdf({path:path.join(folder,'final-submission-report.pdf'),preferCSSPageSize:true,printBackground:true});
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(folder,'browser-validation.json'),JSON.stringify({executedAt:new Date().toISOString(),result:'PASS',checks:['Five intake records','Mock send and receipt','Timeout ownership','Human reason and retry','Duplicate preserves record count','Decision history','Five report sections','No horizontal overflow','No browser JavaScript errors'],limits:'Chromium smoke test with synthetic data; no clinical or real interface validation.'},null,2)+'\n');
    console.log('Browser workflow and report smoke checks passed; screenshots and printable PDF saved.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode=1; });
