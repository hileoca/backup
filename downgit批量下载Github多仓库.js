// download_seq_with_timeout_v2.js
// 需要：npm i playwright
// Node.js + Playwright

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const linksFile = 'links.txt'; //downgit下载链接列表，一行一个，与本脚本在同一目录
  const downloadDir = path.resolve(__dirname, 'downloads'); //下载保存到目录
  fs.mkdirSync(downloadDir, { recursive: true });

  const content = fs.readFileSync(linksFile, 'utf-8');
  const links = content.split(/\r?\n/).map(s => s.trim()).filter(Boolean);

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    acceptDownloads: true,
    downloadsPath: downloadDir
  });
  const page = await context.newPage();

  for (let i = 0; i < links.length; i++) {
    const url = links[i];
    console.log(`开始处理 #${i + 1} / ${links.length}: ${url}`);

    let didTimeout = false;
    let downloadObj = null;

    // 1) 尝试导航到下载页
    try {
      await page.goto(url, { timeout: 15000, waitUntil: 'load' });
    } catch (err) {
      console.error(`导航失败 #${i + 1}: ${err.message}`);
      console.log(`跳过链接 #${i + 1}`);
      continue;
    }

    // 2) 设定一个 1500ms 的超时等待下载信号
    try {
      downloadObj = await Promise.race([
        page.waitForEvent('download', { timeout: 1500 }).then(d => ({ ok: true, download: d })),
        new Promise(resolve => setTimeout(() => resolve({ ok: false }), 1500))
      ]);
    } catch (err) {
      // 若等待下载事件抛出错误，视为超时/失败
      downloadObj = { ok: false };
    }

    if (!downloadObj || !downloadObj.ok) {
      console.log(`在规定时间内未检测到下载动作，跳过链接 #${i + 1}`);
      didTimeout = true;
      continue;
    }

    // 3) 下载已触发，等待并保存
    const download = downloadObj.download;
    const suggested = download.suggestedFilename();
    const savePath = path.join(downloadDir, suggested || `download_${Date.now()}`);
    try {
      await download.saveAs(savePath);
      console.log(`下载完成：${savePath}`);
    } catch (err) {
      console.error(`下载失败 #${i + 1}: ${err}`);
    }
  }

  await browser.close();
})();
