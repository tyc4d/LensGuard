import { expect, test } from '@playwright/test';
import { backendRun, liveHealth, prepareLive, routePair, separate } from './experience-helpers';

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
