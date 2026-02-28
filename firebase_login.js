const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Navigate to Firebase login
  await page.goto('https://console.firebase.google.com');
  
  console.log('Browser opened. Please:');
  console.log('1. Sign in with rhuam@aicenterplus.com');
  console.log('2. When prompted, click "Try another way"');
  console.log('3. Select the option to send a message to yourself');
  console.log('4. Approve the login');
  console.log('5. Once logged in, the CLI token will be accessible');
  
  // Wait for user to complete login
  await page.waitForTimeout(60000);
  
  await browser.close();
})();
