# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from agents.graph import chat

print("Starting...")
result = chat('Why is f(x)=x^2 even?', 'even_function')

print(f"Response length: {len(result['response'])} characters")
print(f"\nAI Response:\n{result['response']}")
print(f"\nNode history: {result['state'].get('node_history', [])}")
