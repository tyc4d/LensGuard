const TARGET_BYTES = 1024 * 1024;

// Keep the existing capture quality for small frames. Larger frames get a
// bounded quality reduction, without further shrinking text in the scene.
export async function encodeUploadImage(canvas: HTMLCanvasElement): Promise<Blob> {
  const encode = (quality: number) => new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(value => value ? resolve(value) : reject(new Error('Image compression failed.')),
      'image/jpeg', quality);
  });
  let best = await encode(0.9);
  for (const quality of [0.85, 0.8, 0.75]) {
    if (best.size <= TARGET_BYTES) break;
    const candidate = await encode(quality);
    if (candidate.size < best.size) best = candidate;
  }
  if (best.size > 10 * 1024 * 1024) {
    throw new Error('The compressed image is still too large. Choose a smaller image.');
  }
  return best;
}
