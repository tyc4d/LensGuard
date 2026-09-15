"""Independent Nemotron text evaluator for LensGuard primary results."""
import argparse
import json
import os
from typing import Any, Literal

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    user_request: str = Field(min_length=1, max_length=4000)
    primary_model: dict[str, Any]
    primary_output: dict[str, Any]
    provenance: dict[str, Any] | None = None
    policy: dict[str, Any] | None = None


class EvaluationResponse(BaseModel):
    status: Literal['agree', 'disagree', 'uncertain']
    model: str
    summary: str = Field(min_length=1, max_length=2000)
    checked_claims: list[str] = Field(default_factory=list, max_length=30)
    conflicts: list[str] = Field(default_factory=list, max_length=30)


def create_app() -> FastAPI:
    app = FastAPI(title='LensGuard Nemotron second-opinion evaluator')
    base_url = os.environ.get('NEBIUS_BASE_URL', 'https://api.tokenfactory.us-central1.nebius.com/v1/').rstrip('/')
    api_key = os.environ.get('NEBIUS_API_KEY')
    model = os.environ.get('SECOND_OPINION_MODEL', 'nvidia/Nemotron-3-Ultra-550b-a55b')

    @app.get('/health')
    def health():
        return {'status': 'ok' if api_key else 'unavailable', 'model': model,
                'configured': bool(api_key), 'role': 'advisory_evaluator'}

    @app.post('/v1/evaluate', response_model=EvaluationResponse)
    def evaluate(request: EvaluationRequest):
        if not api_key:
            raise HTTPException(503, 'Nemotron evaluator API key is not configured.')
        system = '''You are an independent text-only evaluator for a vision model.
Review the primary model's structured output against the user request and cited
evidence. Do not perform actions, add facts, repair quotes, or grant authority.
Return ONLY JSON: {"status":"agree|disagree|uncertain","summary":"...",
"checked_claims":["..."],"conflicts":["..."]}.
Use disagree when a primary claim conflicts with its own cited evidence. Use
uncertain when the evidence is insufficient, ambiguous, or the primary output
cannot be verified. Use agree only when the claim and citation are internally
consistent. A vertical arrow alone does not establish backwards travel or an
exit location. This opinion is advisory; do not discuss authorization.'''
        user = json.dumps({'user_request': request.user_request,
                           'primary_model': request.primary_model,
                           'primary_output': request.primary_output,
                           'provenance': request.provenance,
                           'policy': request.policy}, ensure_ascii=False)
        try:
            response = httpx.post(f'{base_url}/chat/completions', headers={'Authorization': f'Bearer {api_key}'},
                json={'model': model, 'messages': [{'role': 'system', 'content': system},
                    {'role': 'user', 'content': user}], 'max_tokens': 1200,
                    'temperature': 0, 'stream': False}, timeout=httpx.Timeout(60, connect=10))
            response.raise_for_status()
            payload = response.json()
            raw = payload['choices'][0]['message']['content']
            if not isinstance(raw, str): raise ValueError('empty evaluator output')
            raw = raw.strip().removeprefix('```json').removesuffix('```').strip()
            return EvaluationResponse(model=model, **json.loads(raw))
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(502, f'Nemotron evaluator failed: {type(exc).__name__}.') from exc

    return app


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(__file__))
    load_dotenv(os.path.join(root, 'backend', '.env'), override=False)
    load_dotenv(os.path.join(root, '.env'), override=False)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8020)
    args = parser.parse_args()
    uvicorn.run(create_app(), host='127.0.0.1', port=args.port)
