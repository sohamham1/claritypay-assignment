"""Run the full merchant underwriting pipeline from one submission entrypoint."""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load local API keys and model settings from solution/.env.
# The .env file is ignored by Git so secrets stay on your machine.
load_dotenv(PROJECT_ROOT / ".env")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline import run_pipeline


if __name__ == "__main__":
    result = asyncio.run(run_pipeline())
    print(json.dumps(result["portfolio"], indent=2))
    print(json.dumps(result["report_result"], indent=2))
