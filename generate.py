import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

LANGUAGE_PROMPTS = {
    'en': 'Write a {word_count} word grammatically correct, meaningful English sentence using common words. Include as many of these letters as possible: {targets}. The sentence must make sense and be something a native speaker would say. Keep it under 25 characters. Output only the sentence.',
    'ru': 'Write a {word_count} word grammatically correct, meaningful Russian sentence using Cyrillic script and common words. Include as many of these letters as possible: {targets}. The sentence must make sense. Keep it under 25 characters. Output only the sentence.',
    'ar': 'Write a {word_count} word grammatically correct, meaningful Arabic sentence using common words. Include as many of these letters as possible: {targets}. The sentence must make sense. Keep it under 25 characters. Output only the sentence.',
}


def generate_prompt(word_count: int, targets: list[str], lang: str = 'en') -> str:
    targets_str = ', '.join(targets)
    template = LANGUAGE_PROMPTS.get(lang, LANGUAGE_PROMPTS['en'])
    return template.format(word_count=word_count, targets=targets_str)


def generate_samples(sample_count: int, word_count: int, targets: list[str], lang: str = 'en') -> list[str]:
    prompt = generate_prompt(word_count, targets, lang)
    messages = [{'role': 'user', 'content': prompt}]
    completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        temperature=1,
        n=sample_count,
    )
    return [choice.message.content for choice in completion.choices]
