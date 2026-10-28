import assert from 'node:assert/strict';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import puppeteer from 'puppeteer';

const baseURL = process.env.TEST_BASE_URL || 'http://localhost:8000';
const output = path.resolve('test-results');
await mkdir(output, { recursive: true });
const browser = await puppeteer.launch({
  headless: false,
  executablePath:
    process.env.CHROME_PATH ||
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
  defaultViewport: { width: 1440, height: 1050 },
});
const page = await browser.newPage();
const errors = [];
const passed = [];
page.on('pageerror', (error) => errors.push(error.message));
async function check(name, action) {
  await action();
  passed.push(name);
  console.log(`PASS: ${name}`);
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
async function ready() {
  await page.waitForSelector('tbody tr');
  await page.waitForFunction(
    () =>
      !document.querySelector('[role="status"]') &&
      !document.querySelector('[role="alert"]'),
  );
}
async function clickButton(text) {
  for (const button of await page.$$('button')) {
    if (
      (await button.evaluate((element) => element.textContent.trim())) === text
    ) {
      await button.click();
      return;
    }
  }
  throw new Error(`Button not found: ${text}`);
}

try {
  await page.goto(baseURL, { waitUntil: 'networkidle0' });
  await check('Dashboard loads real data and 48 half-hour rows', async () => {
    await ready();
    assert.equal(await page.$$eval('tbody tr', (rows) => rows.length), 48);
    assert.equal(
      await page.$eval('.delivery strong', (el) => el.textContent),
      '2026-01-16',
    );
    assert.equal(
      await page.$$eval('.metric', (elements) => elements.length),
      4,
    );
    assert.ok(
      (await page.$$eval('svg circle', (elements) => elements.length)) > 0,
    );
  });
  await check(
    'January 31 decision updates delivery to February 1',
    async () => {
      await setFilter('Decision date', '2026-01-31');
      await page.waitForFunction(
        () =>
          document.querySelector('.delivery strong')?.textContent ===
          '2026-02-01',
      );
      await ready();
      assert.match(
        await page.$eval('.export', (el) => el.href),
        /decision_date=2026-01-31/,
      );
    },
  );
  await check('Cutoff change updates the displayed analysis', async () => {
    await setFilter('Decision cutoff', '09:00');
    await page.waitForFunction(() =>
      document.querySelector('.chart-foot')?.textContent.includes('09:00'),
    );
    await ready();
    assert.match(
      await page.$eval('.export', (el) => el.href),
      /cutoff=09%3A00|cutoff=09:00/,
    );
  });
  await check('Methodology navigation preserves decision filters', async () => {
    await clickButton('Methodology');
    await page.waitForSelector('.method');
    assert.match(
      await page.$eval('.method', (el) => el.textContent),
      /Accuracy and coverage/,
    );
    await clickButton('Decision overview');
    await ready();
    assert.equal(
      await page.$eval('[aria-label="Decision date"]', (el) => el.value),
      '2026-01-31',
    );
    assert.equal(
      await page.$eval('[aria-label="Decision cutoff"]', (el) => el.value),
      '09:00',
    );
  });
  await check(
    'CSV download has the correct header and 48 periods',
    async () => {
      const client = await page.createCDPSession();
      await client.send('Page.setDownloadBehavior', {
        behavior: 'allow',
        downloadPath: output,
      });
      await page.click('.export');
      await page.waitForFunction(() => true);
      const filename = 'wind-2026-01-31.csv';
      let csv;
      for (let count = 0; count < 100; count += 1) {
        if ((await readdir(output)).includes(filename)) {
          csv = await readFile(path.join(output, filename), 'utf8');
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      assert.ok(csv, 'CSV download was not completed');
      assert.ok(
        csv.startsWith('start_time,forecast,actual,publish_time,error'),
      );
      assert.equal(csv.trim().split(/\r?\n/).length, 49);
    },
  );
  await page.screenshot({
    path: path.join(output, 'dashboard-desktop.png'),
    fullPage: true,
  });
  await check('Mobile layout fits the viewport', async () => {
    await page.setViewport({ width: 390, height: 844 });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    );
    await page.screenshot({
      path: path.join(output, 'dashboard-mobile.png'),
      fullPage: true,
    });
  });
  await check(
    'Invalid input is rejected without sending an API request',
    async () => {
      let requests = 0;
      const track = (request) => {
        if (request.url().includes('/api/v1/')) requests += 1;
      };
      page.on('request', track);
      await setFilter('Decision date', '2026-02-01');
      await page.waitForSelector('[aria-invalid="true"]');
      await new Promise((resolve) => setTimeout(resolve, 300));
      assert.equal(requests, 0);
      assert.equal(await page.$('.export'), null);
      page.off('request', track);
      await setFilter('Decision date', '2026-01-31');
      await ready();
    },
  );
  await check(
    'Malformed API payload is rejected with a visible error',
    async () => {
      await page.setRequestInterception(true);
      const intercept = (request) => {
        if (request.url().includes('/api/v1/dashboard/')) {
          return request.respond({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              success: true,
              status_code: 200,
              message: 'OK',
              data: { rows: 'bad payload' },
              errors: null,
            }),
          });
        }
        return request.continue();
      };
      page.on('request', intercept);
      await page.reload({ waitUntil: 'networkidle0' });
      await page.waitForSelector('[role="alert"]');
      assert.match(
        await page.$eval('[role="alert"]', (el) => el.textContent),
        /invalid data/,
      );
      assert.equal(await page.$('tbody'), null);
      page.off('request', intercept);
      await page.setRequestInterception(false);
      await clickButton('Retry');
      await ready();
    },
  );
  await check('No browser JavaScript exceptions', async () =>
    assert.deepEqual(errors, []),
  );
  await writeFile(
    path.join(output, 'report.json'),
    JSON.stringify({ baseURL, passed, errors }, null, 2),
  );
  console.log(
    `${passed.length} browser checks passed. Screenshots and report: ${output}`,
  );
} catch (error) {
  await page.screenshot({
    path: path.join(output, 'failure.png'),
    fullPage: true,
  });
  await writeFile(
    path.join(output, 'report.json'),
    JSON.stringify(
      { baseURL, passed, errors, failure: error.message },
      null,
      2,
    ),
  );
  throw error;
} finally {
  await browser.close();
}
