async page => {
  await page.mouse.move(980, 470);
  for (let i = 0; i < 6; i++) { await page.mouse.wheel(0, -240); await page.waitForTimeout(900); }
  await page.waitForTimeout(2000);
}
