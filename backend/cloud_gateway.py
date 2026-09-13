"""CPU-only entry point for the Nebius-backed Prototype runtime."""
import argparse
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'prototype'))

from prototype_demo_server.app import create_app
from prototype_demo_server.nebius import NebiusRuntime


if __name__ == '__main__':
    load_dotenv(ROOT / 'backend' / '.env', override=False)
    load_dotenv(ROOT / '.env', override=False)
    parser = argparse.ArgumentParser(description='LensGuard Nebius cloud inference; no local GPU required.')
    parser.add_argument('--port', type=int, default=8010)
    args = parser.parse_args()
    uvicorn.run(create_app(NebiusRuntime()), host='127.0.0.1', port=args.port, workers=1)
