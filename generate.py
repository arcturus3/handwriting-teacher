import os
import openai

openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_prompt(word_count: int, targets: list[str]) -> str:
    targets = ', '.join(targets)
    return f'Write a {word_count} word sentence with a high proportion of the characters: {targets}.'

def generate_samples(sample_count: int, word_count: int, targets: list[str]) -> list[str]:
    prompt = generate_prompt(word_count, targets)
    messages = [{'role': 'user', 'content': prompt}]
    completion = openai.ChatCompletion.create(
        model='gpt-4',
        messages=messages,
        temperature=1,
        n=sample_count,
    )
    return [choice['message']['content'] for choice in completion['choices']]
