import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import { STAGES, STAGE_NAMES, locateEvidenceLabel, presentEvidence, presentBaseline, presentProtectedOutcome, type Stage, type Presentation, type Piece } from '../../experience';
import type { RunState } from '../../types';

interface Props {
  stage: Stage;
  presentation: Presentation;
  baseline: RunState | null;
  showComparison: boolean;
  imageUrl: string | null;
  imageAlt: string;
  query: string;
  sourceLabel: string;
  busy: boolean;
  comparing: boolean;
  cloud?: boolean;
  inferenceStage?: string | null;
  error: string | null;
  onChooseInput: () => void;
  onShowDetails: () => void;
}

function Mark({ piece }: { piece: Piece }) {
  return <span className={`piece-mark piece-mark--${piece.disposition}`} aria-hidden="true">{piece.disposition === 'ignore' ? '×' : piece.disposition === 'unknown' ? '?' : '✓'}</span>;
}

const roleLabels: Record<Piece['label'], string> = {
  OBSERVATION: 'Observation', CONTACT: 'Contact information', INSTRUCTION: 'Injected instruction', QUOTED: 'Quoted text', UNRESOLVED: 'Unresolved',
};

function LocatedLabel({ box, plane, children }: { box: NonNullable<Piece['bbox']>; plane: { width: number; height: number }; children: ReactNode }) {
  const label = useRef<HTMLSpanElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  useLayoutEffect(() => {
    const element = label.current!;
    const measure = () => setSize(previous => {
      const width = element.offsetWidth, height = element.offsetHeight;
      return previous.width === width && previous.height === height ? previous : { width, height };
    });
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const position = locateEvidenceLabel(box, plane, size);
  return <span ref={label} className="semantic-label semantic-label--located" style={{
    // Absolute offsets start inside the evidence box's one-pixel border.
    left: position.left - 1, top: position.top - 1,
    maxWidth: Math.min(260, plane.width), maxHeight: plane.height,
  }}>{children}</span>;
}

export function DemoExperience({ stage, presentation, baseline, showComparison, imageUrl, imageAlt, query, sourceLabel, busy, comparing, cloud, inferenceStage, error, onChooseInput, onShowDetails }: Props) {
  const viewport = useRef<HTMLDivElement>(null);
  const [bounds, setBounds] = useState({ width: 1000, height: 625 });
  const [imageSize, setImageSize] = useState({ width: 1000, height: 625 });
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    setElapsed(0);
    if (!busy) return;
    const started = Date.now();
    const timer = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(timer);
  }, [busy, comparing]);
  const phaseLabels: Record<string, string> = {
    task: '1/3 · Understanding your request', perception: '2/3 · Reading the image',
    selection: '3/3 · Selecting cited evidence', unprotected: 'Running the unprotected comparison',
    second_opinion: 'Nemotron · Reviewing the answer and citations',
  };
  useEffect(() => {
    if (!viewport.current) return;
    const observer = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setBounds({ width, height });
    });
    observer.observe(viewport.current);
    return () => observer.disconnect();
  }, []);
  const scale = Math.min(bounds.width / imageSize.width, bounds.height / imageSize.height);
  const planeStyle = stage === 'decide' || stage === 'result' ? bounds
    : { width: imageSize.width * scale, height: imageSize.height * scale };
  const { pieces, result } = presentation;
  const { focus, displayed, extraRegions, extracted } = presentEvidence(pieces);
  // A mixed set must not put an opaque text panel over located evidence.
  // Show one extracted-text list when any displayed region lacks coordinates.
  const spatial = extracted ? [] : displayed;
  const unlocated = extracted ? displayed : [];
  const showPieces = stage === 'separate';
  const longResult = result.heading.length > (/[\u3400-\u9fff]/u.test(result.heading) ? 4 : 12);
  const numericAnswer = /^[+\d ()-]+$/.test(result.heading);
  const without = presentBaseline(baseline);
  const withGuard = presentProtectedOutcome(presentation);
  const normalize = (value: string) => value.replace(/[\s()-]/g, '').toLocaleLowerCase();
  const sameOutcome = without.value !== null && withGuard.value !== null && without.kind === withGuard.kind
    && normalize(without.value) === normalize(withGuard.value);

  function pieceStyle(piece: Piece, index: number): CSSProperties {
    if (stage === 'decide') return {};
    if (extracted) return { left: '8%', top: `${unlocated.length === 1 ? 34 : 15 + index * 37}%`, width: '84%', height: '22%' };
    return piece.bbox ? {
      left: `${piece.bbox.x * 100}%`, top: `${piece.bbox.y * 100}%`,
      width: `${piece.bbox.width * 100}%`, height: `${piece.bbox.height * 100}%`,
    } : { left: '8%', top: `${unlocated.length === 1 ? 34 : 15 + index * 37}%`, width: '84%', height: '22%' };
  }
  function token(piece: Piece, index: number) {
    const label = <>{stage === 'separate' && <Mark piece={piece} />}{stage === 'separate' ? roleLabels[piece.label] : piece.disposition === 'ignore' ? 'Unsafe instruction' : ['use', 'keep'].includes(piece.disposition) ? 'Usable information' : 'Unresolved'}</>;
    return <div key={piece.id} className={`semantic-piece${stage === 'separate' && extracted ? ' semantic-piece--unlocated' : ''}`}
      data-disposition={piece.disposition} data-region-id={piece.id} style={pieceStyle(piece, index)}
      aria-label={`${roleLabels[piece.label]}: ${piece.content}`}>
      <span className="semantic-value">{(stage === 'decide' ? piece.value : piece.content).replace(/\s+/gu, ' ').trim()}</span>
      {stage === 'separate' && !extracted && piece.bbox
        ? <LocatedLabel box={piece.bbox} plane={planeStyle}>{label}</LocatedLabel>
        : <span className="semantic-label">{label}</span>}
    </div>;
  }

  return <section className="demo-experience" aria-label="LensGuard interactive demo">
    {stage !== 'input' && <button className="evidence-button" onClick={onShowDetails} aria-keyshortcuts="d">View evidence</button>}
    <div className="stage-index" aria-live="polite" aria-atomic="true"><span>{String(STAGES.indexOf(stage) + 1).padStart(2, '0')} <i>/ 04</i></span><strong>{STAGE_NAMES[STAGES.indexOf(stage)]}</strong></div>
    <div ref={viewport} className="central-stage" data-stage={stage} data-comparison={showComparison} aria-busy={busy}>
      <div className="scene-plane" style={planeStyle}>
        {imageUrl && <img className="scene-image" src={imageUrl} alt={imageAlt} aria-hidden={stage === 'result' || stage === 'decide'}
          onLoad={event => setImageSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} />}
        {showPieces && spatial.map(token)}
      </div>
      {!imageUrl && stage === 'input' && <button className="empty-scene" onClick={onChooseInput}><span className="empty-viewfinder" aria-hidden="true">⌜<i />⌟</span><span>Let the AI see the scene</span><small>Choose an image or start the camera</small></button>}
      {showPieces && unlocated.length > 0 && <div className="unlocated-evidence">{stage === 'separate' && <small className="extraction-caption">Extracted text</small>}{unlocated.map(token)}</div>}
      {stage === 'separate' && extraRegions > 0 && <button className="more-regions" onClick={onShowDetails}>{extraRegions} more items</button>}
      {stage === 'separate' && <div className="stage-message" role="status">{presentation.clean ? <><span className="confirmation">✓</span> No injected instructions detected.</> : !presentation.hasSemantics ? 'No text classifications available yet.' : pieces.some(piece => piece.disposition === 'unknown') ? 'Some text remains unresolved.' : null}</div>}
      {stage === 'decide' && <div className="decision-effects" aria-label="Information selection results">
        {focus.map((piece, index) => <div className="decision-item" key={piece.id}>
          {token(piece, index)}
          <div className="decision-effect" data-disposition={piece.disposition}>
            <Mark piece={piece} /><span>{piece.disposition === 'ignore' ? 'Ignore' : piece.disposition === 'use' ? 'Use' : 'Keep'}</span>
          </div>
        </div>)}
        {!focus.length && <p className="stage-empty-message">No usable information is available yet.</p>}
      </div>}
      {stage === 'decide' && showComparison && <div className="decision-comparison" aria-label="LensGuard result comparison">
        <div className="comparison-row" data-guard="off"><span>Without LensGuard{without.detail && <small>{without.detail}</small>}</span><strong title={without.text}>{without.text}</strong></div>
        <div className="comparison-row" data-guard="on"><span>With LensGuard{withGuard.detail && <small>{withGuard.detail}</small>}</span><strong title={withGuard.text}>{withGuard.text}</strong></div>
        <small>{sameOutcome ? 'Same output this time' : 'Same image and request'} · {baseline?.runtime === 'mock' ? 'Sample comparison' : 'Actual run results'}</small>
      </div>}
      {stage === 'result' && <div className="stage-result" data-long={longResult} data-has-value={!!result.value} role="status">
        {result.confirmed && <span className="result-check" aria-label="Confirmed">✓</span>}
        {result.value ? <><p className="result-kicker">{result.simulation && result.heading === 'Calling' ? 'Simulating a call' : result.heading}</p><h1 className="result-contact">{result.value}</h1></> : <h1 className={numericAnswer ? 'result-contact' : undefined}>{result.heading}</h1>}
        <p className="result-caption">{result.caption}</p>
        {result.note && <p className="result-note">{result.note}</p>}
      </div>}
      {stage === 'input' && imageUrl && <span className="scene-source">{sourceLabel}</span>}
      {busy && <div className="analysis-indicator" role="status">
        <span>{inferenceStage === 'second_opinion' ? phaseLabels.second_opinion : cloud ? phaseLabels[inferenceStage ?? ''] ?? 'Waiting for the cloud service'
          : comparing ? 'Comparing the unprotected result' : 'Reading the scene'}…</span>
        <span aria-live="off"> {elapsed}s elapsed</span>
        {cloud && <small>{elapsed >= 60 ? 'The cloud is taking longer. A timeout will show an error; no result is substituted.'
          : inferenceStage === 'second_opinion' ? 'Text-only second opinion via Nebius Token Factory. The Guard decision remains unchanged.'
          : comparing ? 'One separate primary model call with Guard OFF, followed by the configured review.' : 'Three primary model calls, Guard checks, then the configured Nemotron review. This can take a minute or longer.'}</small>}
      </div>}
    </div>
    <div className="stage-undertext">
      {error ? <p className="experience-error" role="alert">{error}</p> : stage === 'input' && <p className="scene-request">{query ? `“${query}”` : 'Choose a scene and enter your request.'}</p>}
    </div>
  </section>;
}
