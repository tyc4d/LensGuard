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
    {!!opinion.conflicts?.length && <ul>{opinion.conflicts.map(conflict => <li key={conflict}>{conflict}</li>)}</ul>}
  </section>;
}
