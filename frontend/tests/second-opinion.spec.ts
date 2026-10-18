import { expect, test } from '@playwright/test';
import { backendRun, routePair, separate } from './experience-helpers';

for (const width of [390, 1280]) {
  test(`independent opinion displays actual evidence and survives repeated drawer open at ${width}px`, async ({ page, request }) => {
    await page.setViewportSize({ width, height: 900 });
    const guarded = await backendRun(request);
    guarded.second_opinion = {
      status: 'disagree', model: 'nvidia/Nemotron-3-Ultra-550b-a55b',
      provider: 'nebius', provider_origin: 'https://provider.test',
      provider_model: 'nvidia/Nemotron-3-Ultra-550b-a55b',
      response_id: 'chatcmpl-provider-proof', provider_request_id: 'provider-request-proof',
      elapsed_ms: 125.5, usage: { total_tokens: 70 },
      summary: 'The selected claim conflicts with its quoted evidence.',
      conflicts: ['The quote says RIGHT.'],
    };
    await routePair(page, guarded);
    await page.goto('/');
    await separate(page);
    for (let i = 0; i < 2; i++) {
      await page.keyboard.press('d');
      const drawer = page.getByRole('dialog', { name: 'Technical trace' });
      await expect(drawer).toBeVisible();
      const disclosure = drawer.locator('details.technical-trace');
      if (!await disclosure.getAttribute('open').then(value => value !== null)) {
        await drawer.getByText('View technical details', { exact: true }).click();
      }
      const opinion = drawer.getByLabel('Independent second opinion');
      await expect(opinion).toContainText('Disagrees with primary model');
      await expect(opinion).toContainText('chatcmpl-provider-proof');
      await expect(opinion).toContainText('provider-request-proof');
      await expect(opinion).toContainText('https://provider.test');
      await expect(opinion).toContainText('125.5 ms');
      await expect(opinion).toContainText('does not independently inspect the image or authorize actions');
      await expect(opinion).not.toContainText('Nemotron-3.5-Super-VL');
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await page.keyboard.press('Escape');
      await expect(drawer).not.toBeVisible();
    }
  });
}
