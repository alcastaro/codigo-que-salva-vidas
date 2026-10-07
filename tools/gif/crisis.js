async page => {
  for (let i = 0; i < 12; i++) { await page.mouse.wheel(0, 260); await page.waitForTimeout(500); }
  await page.waitForTimeout(800);
}
