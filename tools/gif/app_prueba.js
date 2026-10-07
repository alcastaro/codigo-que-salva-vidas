async page => {
  // 1 · Cargar el lugar (Constanza, con copia)
  await page.getByRole('button', { name: /Cargar el lugar/ }).click();
  await page.waitForTimeout(25000);
  // 2 · Marcar ejemplos haciendo clic sobre la imagen de AlphaEarth (primera imagen de la página)
  const img = page.locator('img').filter({ hasNot: page.locator('svg') }).first();
  const caja = await img.boundingBox();
  const clic = async (fila, col) => {
    await page.mouse.click(caja.x + caja.width * col / 300, caja.y + caja.height * fila / 300);
    await page.waitForTimeout(400);
  };
  const clase = async (n) => { await page.getByLabel(n, { exact: true }).check(); await page.waitForTimeout(300); };
  await clase('Bosque');          for (const [f, c] of [[20, 40], [40, 250], [275, 30], [60, 15]]) await clic(f, c);
  await clase('Construido');      for (const [f, c] of [[150, 150], [185, 140], [120, 170]]) await clic(f, c);
  await clase('Cultivo / pasto'); for (const [f, c] of [[195, 215], [105, 215], [240, 282]]) await clic(f, c);
  await clase('Suelo desnudo');   for (const [f, c] of [[218, 268], [268, 168], [130, 95]]) await clic(f, c);
  // 3 · Clasificar
  await page.getByRole('button', { name: /Clasificar/ }).click();
  await page.waitForTimeout(8000);
}
