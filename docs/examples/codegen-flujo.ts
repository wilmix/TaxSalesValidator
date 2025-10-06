import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://login.impuestos.gob.bo/realms/login2/protocol/openid-connect/auth?client_id=app-frontend&redirect_uri=https%3A%2F%2Fsiat.impuestos.gob.bo%2Fv2%2Flauncher%2F&state=383c2e56-bae1-455b-8fb2-0352db1c05f1&response_mode=fragment&response_type=code&scope=openid&nonce=2434bad9-66a4-4fdb-87cd-65e6c0167293');
  await page.getByRole('textbox', { name: 'Usuario o email' }).click();
  await page.getByRole('textbox', { name: 'Usuario o email' }).fill('willy@hergo.com.bo');
  await page.getByRole('textbox', { name: 'Correo Contraseña' }).click();
  await page.getByRole('textbox', { name: 'Correo Contraseña' }).fill('Hergo10');
  await page.getByRole('textbox', { name: 'NIT/CUR/CI' }).click();
  await page.getByRole('textbox', { name: 'NIT/CUR/CI' }).fill('1000991026');
  await page.getByRole('button', { name: 'INGRESAR' }).click();
  await page.getByRole('heading', { name: 'SISTEMA DE FACTURACIÓN', exact: true }).click();
  await page.locator('#mat-menu-panel-6 h4').filter({ hasText: 'Registro de Compras y Ventas' }).click();
  await page.getByRole('link', { name: ' VENTAS ' }).click();
  await page.getByRole('link', { name: ' Registro de Ventas' }).click();
  await page.locator('[id="formPrincipal:pnlCriterios_content"] div').filter({ hasText: 'ENEROFEBREROMARZOABRILMAYOJUNIOJULIOAGOSTOSEPTIEMBREOCTUBRENOVIEMBREDICIEMBREOCT' }).nth(1).click();
  await page.locator('[id="formPrincipal:txtPeriodo_label"]').click();
  await page.locator('[id="formPrincipal:txtPeriodo_label"]').click();
  await page.getByRole('option', { name: 'SEPTIEMBRE' }).click();
  await page.getByRole('button', { name: ' Buscar' }).click();
  const download1Promise = page.waitForEvent('download');
  await page.getByRole('button', { name: ' Descargar Consulta Csv' }).click();
  const download1 = await download1Promise;
  await page.getByRole('link', { name: 'willy@hergo.com.bo' }).click();
  await page.getByRole('button', { name: 'Cerrar sesión' }).click();
  await page.getByRole('button', { name: 'Si', exact: true }).click();
});