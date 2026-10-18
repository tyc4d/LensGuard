import type { RunState } from '../../types';
import { SecondOpinion } from '../SecondOpinion';

export function ModelFlow({ real, run }: { real: boolean; run: RunState | null }) {
  return <section className="model-flow" aria-label="Model workflow">
    <p className="model-flow-credit">Power it with Nemotron models on Nebius through Token Factory.</p>
    <ol className="model-flow-steps">
      <li><span>01 · Primary VLM</span><strong>Understand the scene</strong><p>Parse your request, read the image, and select cited evidence.</p></li>
      <li><span>02 · LensGuard</span><strong>Check evidence &amp; permissions</strong><p>Code checks citations and authorization. Guard OFF skips these checks.</p></li>
      <li><span>03 · NVIDIA Nemotron</span><strong>Review the answer</strong><p>Nemotron-3.5-Super-VL on Nebius Token Factory checks the output against its cited text.</p></li>
    </ol>
    <p className="model-flow-note">{real
      ? 'The optional Nemotron review uses text only. It cannot verify the original image or authorize actions.'
      : 'Sample mode: preset results only. Live mode uses the model workflow above.'}</p>
    {real && <SecondOpinion opinion={run?.second_opinion} />}
  </section>;
}
