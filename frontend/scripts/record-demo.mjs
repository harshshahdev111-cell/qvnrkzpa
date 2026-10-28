import assert from 'node:assert/strict';
import { mkdir, writeFile, stat } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import puppeteer from 'puppeteer';
import ffmpeg from 'ffmpeg-static';

const output = path.resolve('test-results/demo');
await mkdir(output, { recursive: true });
const browser = await puppeteer.launch({
  headless: true,
  executablePath:
    process.env.CHROME_PATH ||
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
  defaultViewport: { width: 1440, height: 1000 },
});
const page = await browser.newPage();
const chapters = [];
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
const hold = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let recorder;
let started;
async function caption(title, description, duration = 6500) {
  chapters.push({
    seconds: Math.round((Date.now() - started) / 1000),
    title,
    description,
  });
  console.log(`Recording: ${title}`);
  await page.evaluate(
    ({ title, description }) => {
      let box = document.getElementById('demo-caption');
      if (!box) {
        box = document.createElement('div');
        box.id = 'demo-caption';
        box.style.cssText =
          'position:fixed;bottom:18px;left:260px;right:24px;z-index:99999;border:1px solid #a8d7ca;border-radius:12px;background:rgba(16,49,43,.97);color:white;padding:18px 24px;box-shadow:0 6px 32px #0003;font-family:Arial,sans-serif;pointer-events:none;';
        document.body.appendChild(box);
      }
      box.replaceChildren();
      const label = document.createElement('div');
      label.textContent = 'WIND DESK  /  PRODUCT DEMO';
      label.style.cssText =
        'font-size:10px;letter-spacing:2px;color:#8bdebf;margin-bottom:7px;';
      const heading = document.createElement('div');
      heading.textContent = title;
      heading.style.cssText =
        'font-size:21px;font-weight:600;margin-bottom:7px;';
      const text = document.createElement('div');
      text.textContent = description;
      text.style.cssText = 'font-size:14px;line-height:1.6;color:#dfebe6;';
      box.append(label, heading, text);
    },
    { title, description },
  );
  await hold(duration);
}
async function setFilter(label, value) {
  await page.$eval(
    `[aria-label="${label}"]`,
    (input, next) => {
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        'value',
      ).set.call(input, next);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    },
    value,
  );
}
async function clickButton(text) {
  for (const button of await page.$$('button')) {
    if ((await button.evaluate((el) => el.textContent.trim())) === text) {
      await button.click();
      return;
    }
  }
  throw Error(`Missing button: ${text}`);
}
try {
  await page.goto(process.env.TEST_BASE_URL || 'http://localhost:8000', {
    waitUntil: 'networkidle0',
  });
  await page.waitForSelector('tbody tr');
  started = Date.now();
  recorder = await page.screencast({
    path: path.join(output, 'recording.webm'),
    ffmpegPath: ffmpeg,
    fps: 24,
    quality: 20,
  });
  await caption(
    'Wind Desk: day-ahead wind intelligence',
    'A working React and Django REST Framework portal using real Elexon wind forecasts and actual generation.',
    7000,
  );
  await page.screenshot({ path: path.join(output, 'poster.png') });
  await caption(
    'Start with the information available when you buy',
    'Decision: 15 January 2026 at 10:00 London time. Delivery: the following day, 16 January.',
    7500,
  );
  await caption(
    'Measure forecast accuracy, with visible coverage',
    'MAE, signed bias and matched coverage explain the size of the miss. The energy total includes available forecast periods only.',
    8000,
  );
  await page.evaluate(() => window.scrollTo({ top: 450, behavior: 'smooth' }));
  await caption(
    'Compare the eligible forecast with delivered generation',
    'Green points show available forecasts; the dashed curve shows actuals. Missing forecast timestamps remain gaps.',
    7500,
  );
  await page.evaluate(() => window.scrollTo({ top: 850, behavior: 'smooth' }));
  await caption(
    'Inspect every half-hour',
    'The table shows forecast MW, actual MW, error and the forecast publication time. RMSE and WAPE provide additional error measures.',
    7500,
  );
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await hold(800);
  await setFilter('Decision date', '2026-01-31');
  await page.waitForFunction(
    () =>
      document.querySelector('.delivery strong')?.textContent === '2026-02-01',
  );
  await caption(
    'Change the date: January 31 buys February 1 delivery',
    'The API recalculates the forecast selection and accuracy metrics for the new decision date.',
    7500,
  );
  await setFilter('Decision cutoff', '09:00');
  await page.waitForFunction(() =>
    document.querySelector('.chart-foot')?.textContent.includes('09:00'),
  );
  await caption(
    'Move the cutoff to 09:00',
    'Only forecasts published at or before this cutoff are eligible. Later forecast revisions are excluded to avoid hindsight.',
    7500,
  );
  const downloadSession = await page.createCDPSession();
  await downloadSession.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: output,
  });
  await page.evaluate(() => window.scrollTo({ top: 850, behavior: 'smooth' }));
  await hold(800);
  await page.click('.export');
  await caption(
    'Export the exact decision view',
    'CSV export contains the same delivery periods and eligible forecast values displayed in the portal.',
    6500,
  );
  assert.ok((await stat(path.join(output, 'wind-2026-01-31.csv'))).size > 0);
  await clickButton('Methodology');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await page.waitForSelector('.method');
  await caption(
    'Understand the method and its limits',
    'The methodology explains forecast selection, error formulas, source coverage and missing data. Exact procurement also requires demand data.',
    9000,
  );
  await clickButton('Decision overview');
  await page.waitForSelector('tbody tr');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await caption(
    'A reproducible decision view, ready for review',
    'React components → versioned DRF API → analysis services → database. Docker runs the app; structured logs include request IDs.',
    8000,
  );
  await recorder.stop();
  recorder = null;
  assert.deepEqual(errors, []);
} finally {
  if (recorder) await recorder.stop();
  await browser.close();
}
const result = spawnSync(
  ffmpeg,
  [
    '-y',
    '-i',
    path.join(output, 'recording.webm'),
    '-c:v',
    'libx264',
    '-preset',
    'medium',
    '-crf',
    '20',
    '-pix_fmt',
    'yuv420p',
    '-movflags',
    '+faststart',
    path.join(output, 'wind-desk-demo.mp4'),
  ],
  { encoding: 'utf8' },
);
if (result.status !== 0) throw Error(result.stderr);
await writeFile(
  path.join(output, 'chapters.json'),
  JSON.stringify(chapters, null, 2),
);
console.log(`Saved ${path.join(output, 'wind-desk-demo.mp4')}`);
