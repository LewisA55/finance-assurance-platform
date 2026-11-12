const {createRequire}=require('node:module');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const assert=require('node:assert/strict');
const webRequire=createRequire(path.resolve(__dirname,'../../../../../web/package.json'));
const {chromium}=webRequire('@playwright/test');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  const page=await browser.newPage({viewport:{width:1360,height:800}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.resolve(__dirname,'../.tmp/preview.html')).href);
  assert.deepEqual(await page.locator('.amount').allTextContents(),['GBP 2,288,009.65','GBP 3,082,301.85','GBP 26,800,564.68']);
  await page.screenshot({path:path.resolve(__dirname,'../.tmp/eligible.png'),fullPage:true});
  for(const mode of ['blocked','purpose','missing']) {
   await page.locator(`[data-mode="${mode}"]`).click();
   assert.deepEqual(await page.locator('.amount').allTextContents(),Array(3).fill('Value withheld'));
   assert.doesNotMatch(await page.locator('body').innerText(),/2,288,009.65|3,082,301.85|26,800,564.68/);
  }
  await page.screenshot({path:path.resolve(__dirname,'../.tmp/withheld.png'),fullPage:true});
  await page.locator('[data-mode="eligible"]').click();
  const summary=page.locator('summary').first();await summary.focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('details').first().getAttribute('open'),'');
  await page.setViewportSize({width:900,height:800});
  assert.equal(await page.locator('.amount').count(),3);
  assert.deepEqual(errors,[]);
  console.log('Browser acceptance PASS: three values, three fail states, stale-value removal, keyboard evidence, resize, no console errors.');
 } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
