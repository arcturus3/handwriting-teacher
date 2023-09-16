import os
import openai

openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_prompt():
    return 'What is 3 + 4?'

def generate_sample(word_count: int, weights: list[chr]):
    messages = [{'role': 'user', 'content': generate_prompt()}]
    completion = openai.ChatCompletion.create(
        model='gpt-4',
        messages=messages,
        temperature=1,
        n=1,
    )
    samples = [choice['message']['content'] for choice in completion['choices']]
    return samples

print(generate_sample(0, []))
