async page => {
  await page.waitForTimeout(3000);
  await page.mouse.move(800, 450);
  for (let i = 0; i < 4; i++) { await page.mouse.wheel(0, -240); await page.waitForTimeout(1200); }
  await page.waitForTimeout(2500);
}
