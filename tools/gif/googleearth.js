async page => {
  await page.mouse.move(800, 450);
  for (let i = 0; i < 14; i++) { await page.mouse.wheel(0, -120); await page.waitForTimeout(350); }
  await page.waitForTimeout(1500);
}
