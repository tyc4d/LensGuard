import { expect, test } from '@playwright/test';

test('large frames shrink before upload while small frames retain their encoding', async ({ page }) => {
  await page.goto('/');
  const results = await page.evaluate(async () => {
    const modulePath = '/src/imageCompression.ts';
    const { encodeUploadImage } = await import(/* @vite-ignore */ modulePath);
    const check = async (size: number) => {
      const canvas = document.createElement('canvas');
      canvas.width = canvas.height = size;
      const context = canvas.getContext('2d')!;
      const pixels = context.createImageData(size, size);
      let seed = 42;
      for (let i = 0; i < pixels.data.length; i += 4) {
        for (let channel = 0; channel < 3; channel++) {
          seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
          pixels.data[i + channel] = seed >>> 24;
        }
        pixels.data[i + 3] = 255;
      }
      context.putImageData(pixels, 0, 0);
      const original = await new Promise<Blob>(resolve => canvas.toBlob(blob => resolve(blob!), 'image/jpeg', 0.9));
      const compressed: Blob = await encodeUploadImage(canvas);
      const bitmap = await createImageBitmap(compressed);
      const result = { before: original.size, after: compressed.size, type: compressed.type,
        width: bitmap.width, height: bitmap.height,
        unchanged: await original.text() === await compressed.text() };
      bitmap.close();
      return result;
    };
    return { small: await check(100), large: await check(2560) };
  });
  expect(results.small.unchanged).toBe(true);
  expect(results.large.before).toBeGreaterThan(1024 * 1024);
  expect(results.large.after).toBeLessThan(results.large.before * 0.85);
  expect(results.large.type).toBe('image/jpeg');
  expect(results.large.width).toBe(2560);
  expect(results.large.height).toBe(2560);
});
