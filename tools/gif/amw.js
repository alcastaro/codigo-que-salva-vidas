async page => {
  const b = page.getByText(/explor/i).first();
  if (await b.count()) { await b.click(); }
  await page.waitForTimeout(6000);
  await page.mouse.move(1000, 520);
  for (let i = 0; i < 5; i++) { await page.mouse.wheel(0, -300); await page.waitForTimeout(1200); }
  await page.waitForTimeout(2500);
}
