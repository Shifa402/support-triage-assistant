from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assistant import SupportTriageAssistant


def main() -> None:
    parser = argparse.ArgumentParser(description='AI-powered support triage assistant')
    parser.add_argument('query', help='Natural-language support question')
    parser.add_argument(
        '--data-dir',
        default=str(Path(__file__).resolve().parents[2] / 'data'),
        help='Directory containing .md knowledge docs and JSON files',
    )
    parser.add_argument('--pretty', action='store_true', help='Pretty-print the structured output')
    args = parser.parse_args()

    assistant = SupportTriageAssistant(args.data_dir)
    result = assistant.answer(args.query)
    print(json.dumps(result, indent=2 if args.pretty else None))


if __name__ == '__main__':
    main()
