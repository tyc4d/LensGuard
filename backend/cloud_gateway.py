"""CPU-only entry point for the Nebius-backed Prototype runtime."""
import argparse
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from app.request_limits import RequestBodyLimitMiddleware

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'prototype'))

from prototype_demo_server.app import create_app
from prototype_demo_server.nebius import NebiusRuntime


def create_cloud_app(runtime=None):
    app = create_app(runtime if runtime is not None else NebiusRuntime())
    app.add_middleware(RequestBodyLimitMiddleware, paths=('/v1/analyze',))
    return app


if __name__ == '__main__':
    load_dotenv(ROOT / 'backend' / '.env', override=False)
    load_dotenv(ROOT / '.env', override=False)
    parser = argparse.ArgumentParser(description='LensGuard Nebius cloud inference; no local GPU required.')
    parser.add_argument('--port', type=int, default=8010)
    args = parser.parse_args()
    uvicorn.run(create_cloud_app(), host='127.0.0.1', port=args.port, workers=1)
