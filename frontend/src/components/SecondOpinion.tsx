import type { RunState } from '../types';

export function SecondOpinion({ opinion }: { opinion: RunState['second_opinion'] }) {
  if (!opinion) return null;
  const label = opinion.status === 'agree' ? 'Agrees with primary model'
    : opinion.status === 'disagree' ? 'Disagrees with primary model'
    : opinion.status === 'uncertain' ? 'Uncertain'
    : opinion.status === 'unavailable' ? 'Not configured' : 'Evaluator error';
  return <section className={`second-opinion second-opinion--${opinion.status}`} aria-label="Independent second opinion">
    <h3>Independent second opinion</h3>
    <p><strong>{label}</strong>{opinion.model ? ` · ${opinion.model}` : ''}</p>
    <p>{opinion.summary}</p>
    <p>Advisory text review only. It does not independently inspect the image or authorize actions.</p>
    {(opinion.provider_origin || opinion.provider_model || opinion.response_id || opinion.provider_request_id || opinion.elapsed_ms != null) &&
      <dl className="details-drawer-facts" aria-label="Evaluator execution evidence">
        {opinion.provider_origin && <div><dt>Provider origin (server-reported)</dt><dd>{opinion.provider_origin}</dd></div>}
        {opinion.provider_model && <div><dt>Provider-reported model</dt><dd>{opinion.provider_model}</dd></div>}
        {opinion.response_id && <div><dt>Provider response ID</dt><dd>{opinion.response_id}</dd></div>}
        {opinion.provider_request_id && <div><dt>Provider request ID</dt><dd>{opinion.provider_request_id}</dd></div>}
        {opinion.elapsed_ms != null && <div><dt>Evaluator API round trip</dt><dd>{opinion.elapsed_ms.toFixed(1)} ms</dd></div>}
      </dl>}
    {!!opinion.conflicts?.length && <ul>{opinion.conflicts.map(conflict => <li key={conflict}>{conflict}</li>)}</ul>}
  </section>;
}
