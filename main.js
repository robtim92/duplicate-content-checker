const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto('https://example.com');
    await page.screenshot({ path: 'C:/Users/tpsuc/Downloads/Duplicate Content Checker/screenshots/screenshot.png', fullPage: true });
    await browser.close();
})();
