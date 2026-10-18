import { expect, test } from '@playwright/test';
import { backendRun, liveHealth, prepareLive, routePair, separate } from './experience-helpers';

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
      await expect(page.getByRole('button', { name: 'View evidence', exact: true })).toBeFocused();
    }
  });
}

for (const entry of [
  { reason: 'not_configured', summary: 'No independent evaluator is configured.', label: 'Not configured' },
  { reason: 'primary_output_invalid', summary: 'Primary model output failed validation; no review was requested.', label: 'Not run' },
  { reason: undefined, summary: 'Legacy service did not provide a reason.', label: 'Not available' },
] as const) {
  test(`unavailable review explains ${entry.reason ?? 'legacy unknown reason'}`, async ({ page, request }) => {
    const run = await backendRun(request);
    run.runtime = 'prototype';
    run.second_opinion = { status: 'unavailable', summary: entry.summary,
      ...(entry.reason ? { unavailable_reason: entry.reason } : {}) };
    if (entry.reason === 'primary_output_invalid') {
      run.status = 'failed';
      run.action = null;
      run.outcome = null;
      run.decision = null;
      run.error = 'The model returned incomplete or invalid JSON while reading the image.';
      run.error_code = 'model_output_parse_failed';
    }
    await liveHealth(page);
    await routePair(page, run);
    await prepareLive(page);
    await page.getByRole('button', { name: 'Start analysis', exact: true }).click();
    const flowOpinion = page.getByLabel('Model workflow').getByLabel('Independent second opinion');
    await expect(flowOpinion.locator('strong')).toHaveText(entry.label);
    await expect(flowOpinion).toContainText(entry.summary);
    if (entry.reason !== 'not_configured') await expect(flowOpinion).not.toContainText('Not configured');
    await page.keyboard.press('d');
    const drawer = page.getByRole('dialog', { name: 'Technical trace' });
    await drawer.getByText('View technical details', { exact: true }).click();
    await expect(drawer.getByLabel('Independent second opinion').locator('strong')).toHaveText(entry.label);
  });
}
