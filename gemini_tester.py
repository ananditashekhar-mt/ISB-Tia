"""Standalone Gemini tester for Threadly. Does not modify agent.py, app.py or evaluate.py.

Gemini exposes an OpenAI-compatible endpoint that supports chat.completions with a
json_schema response_format, which matches the existing "Ollama" code path in agent.py
(Model.understand/compose branch on self.mode == 'Ollama' to use chat.completions
instead of the Responses API used for 'OpenAI'). This script reuses that code path by
passing mode='Ollama' into Agent/Model together with a client that is actually pointed
at Gemini. The business logic (eligibility, policy retrieval, tools) in agent.py is
untouched and fully reused; only the HTTP client and model name are swapped here.

Important: this script uses its own isolated SQLite file (gemini_eval.sqlite), never the
shared runtime.sqlite, so any "mode=Ollama" label stored for these test conversations
never appears in the real app's history.

Setup:
  1. Open gemini.local.env (already gitignored) and paste your Gemini API key after
     GEMINI_API_KEY=. Do not paste it into chat or commit this file.
  2. Run: python gemini_tester.py --smoke-test
  3. Or:  python gemini_tester.py --benchmark --split test
"""
import argparse
import json
import os
import tempfile
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / 'gemini.local.env')

from agent import Agent, load  # noqa: E402  (import after load_dotenv on purpose)


def build_agent(db_path=None):
    api_key = os.getenv('GEMINI_API_KEY', '')
    if not api_key:
        raise SystemExit(
            'GEMINI_API_KEY is empty. Open gemini.local.env and paste your key there, '
            'then re-run this script.'
        )
    model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    base_url = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai/')
    from openai import OpenAI
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=60, max_retries=0)
    return Agent(db_path or ROOT / 'gemini_eval.sqlite', mode='Ollama', model=model, client=client)


def smoke_test():
    agent = build_agent()
    for message, order_id in [
        ('Where is my order?', 'ORD-10156'),
        ('My order is late, what happened?', 'ORD-10156'),
    ]:
        result = agent.chat(message, {'order_id': order_id}, today=date(2026, 9, 17), session='gemini-smoke-test')
        print('MESSAGE:', message)
        print('INTENT:', result['intent'], '| STATUS:', result['status'])
        print('RESPONSE:', result['response'])
        print('-' * 60)
    agent.db.close()


def run_benchmark(split='test', sim_date='2026-09-17'):
    rows = [r for r in load('support_conversations') if split == 'all' or r['Split'] == split]
    results = []
    with tempfile.TemporaryDirectory() as temp:
        agent = build_agent(Path(temp) / 'gemini_eval_bench.sqlite')
        for row in rows:
            result = agent.chat(
                row['Customer_Message'], {'order_id': row['Order_ID']},
                today=date.fromisoformat(sim_date), session=row['Conversation_ID'])
            results.append({
                'conversation_id': row['Conversation_ID'], 'expected_intent': row['Intent'],
                'expected_action': row['Expected_Action'], 'expected_escalation': row['Escalate'],
                'intent_correct': result['intent'] == row['Intent'], 'actual': result})
        agent.db.close()
    summary = {
        'mode': 'Gemini', 'split': split, 'count': len(results),
        'intent_accuracy': sum(r['intent_correct'] for r in results) / len(results) if results else None,
        'note': ('Only intent accuracy is automated. "mode" is labelled Gemini here for clarity; '
                 'internally this reuses the Ollama chat.completions code path with a Gemini client.')}
    out = ROOT / f'evaluation_gemini_{split}.json'
    out.write_text(json.dumps({'summary': summary, 'results': results}, indent=2))
    print(json.dumps(summary, indent=2))
    print('Results:', out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true', help='Send two sample messages and print the replies.')
    parser.add_argument('--benchmark', action='store_true', help='Run the held-out evaluation split through Gemini.')
    parser.add_argument('--split', choices=['train', 'validation', 'test', 'all'], default='test')
    args = parser.parse_args()
    if args.benchmark:
        run_benchmark(args.split)
    else:
        smoke_test()
