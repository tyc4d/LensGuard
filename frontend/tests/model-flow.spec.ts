import { expect, test } from '@playwright/test';
import { backendRun, liveHealth, prepareLive, requestGuard, routePair, separate } from './experience-helpers';
import type { RunState } from '../src/types';

test('Nemotron workflow and actual advisory outcome appear on the demo page', async ({ page, request }) => {
  const result = await backendRun(request, 'clean-navigation');
  result.runtime = 'prototype';
  result.second_opinion = { status: 'disagree', model: 'nvidia/Nemotron-3.5-Super-VL',
    summary: 'The cited evidence is ambiguous.', conflicts: ['Direction is not established.'] };
  await liveHealth(page);
  await routePair(page, result);
  await prepareLive(page, 'uploaded_image', result.scenario_id);
  await separate(page);
  const flow = page.getByRole('region', { name: 'Model workflow' });
  await expect(flow).toContainText('Power it with Nemotron models on Nebius through Token Factory.');
  await expect(flow).toContainText('Disagrees with primary model');
  await expect(flow).toContainText('Direction is not established.');
  await expect(flow).toContainText('cannot verify the original image or authorize actions');
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await flow.scrollIntoViewIfNeeded();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
});

test('sample mode does not claim to run Nemotron', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('region', { name: 'Model workflow' })).toContainText('Sample mode: preset results only.');
  await expect(page.locator('.model-flow .second-opinion')).toHaveCount(0);
});

for (const cloud of [true, false]) {
  for (const guard of [true, false]) {
    test(`${cloud ? 'cloud' : 'local GPU'} Guard ${guard ? 'ON' : 'OFF'} shows the active independent review`, async ({ page, request }) => {
      const protectedRun = await backendRun(request);
      const baseline = await backendRun(request, protectedRun.scenario_id, false);
      const profile = cloud ? 'nebius-glm-5-3-flash' : 'nemotron-nano-vl-8b';
      for (const run of [protectedRun, baseline]) {
        run.runtime = 'prototype';
        run.model_profile = profile;
      }
      const completed = guard ? protectedRun : baseline;
      const reviewing: RunState = { ...completed, status: 'running', stage: 'second_opinion.started',
        action: null, decision: null, outcome: null, final_answer: null, second_opinion: null,
        components: { vlm: 'live', second_opinion: 'running' } };
      await page.route('**/api/health', route => route.fulfill({ json: {
        status: 'ok', runtime: 'prototype', model: 'offline-test-model',
        second_opinion: { configured: true, role: 'advisory_evaluator' },
        prototype: { status: 'ready', device: cloud ? 'cloud' : 'cuda', model_loaded: true,
          model_profile: profile, default_model: profile,
          models: [{ id: profile, name: 'Offline test model', available: true }] },
      } }));
      const submitted: boolean[] = [];
      await page.route('**/api/run', route => {
        const enabled = requestGuard(route.request());
        submitted.push(enabled);
        return route.fulfill({ json: enabled === guard ? reviewing : enabled ? protectedRun : baseline });
      });
      await page.route(`**/api/run/${reviewing.id}`, route => route.fulfill({ json: reviewing }));
      let release!: () => void;
      const ready = new Promise<void>(resolve => { release = resolve; });
      await page.route(`**/api/run/${reviewing.id}/events`, async route => {
        await ready;
        await route.fulfill({ contentType: 'text/event-stream',
          body: `event: runtime\ndata: ${JSON.stringify(completed)}\n\n` });
      });
      await prepareLive(page);
      await page.getByRole('button', { name: 'Start analysis', exact: true }).click();
      try {
        await expect(page.locator('.analysis-indicator')).toContainText('Reviewing the primary output independently');
        await expect(page.locator('.analysis-indicator')).not.toContainText('Reading the scene');
        await expect(page.locator('.analysis-indicator')).not.toContainText('Comparing the unprotected result');
        expect(submitted).toEqual(guard ? [true] : [true, false]);
      } finally { release(); }
      await expect(page.locator('.analysis-indicator')).toHaveCount(0);
    });
  }
}
