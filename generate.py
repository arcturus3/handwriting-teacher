import os
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

MODEL = 'gpt-6-luna'
# One step above none: enough thought to fit the target letters into a short sentence, while
# keeping each sentence to a few seconds (medium sometimes takes ten).
REASONING_EFFORT = 'low'

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
    messages: list[ChatCompletionMessageParam] = [{'role': 'user', 'content': prompt}]
    completion = client.chat.completions.create(
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        messages=messages,
        temperature=1,
        n=sample_count,
    )
    sentences: list[str] = []
    for choice in completion.choices:
        # A reasoning model can spend its whole budget thinking and return no text.
        if not choice.message.content:
            raise RuntimeError(f'{MODEL} returned no sentence')
        sentences.append(choice.message.content.strip())
    return sentences
