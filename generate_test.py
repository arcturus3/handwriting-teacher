from types import SimpleNamespace
from unittest.mock import patch

import generate


def completion(*sentences: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=s)) for s in sentences]
    )


def test_asks_luna_with_a_little_reasoning() -> None:
    with patch.object(generate.client.chat.completions, 'create') as create:
        create.return_value = completion('Jazz quiz vexes Jake.')
        assert generate.generate_samples(1, 4, ['q', 'z'], 'en') == ['Jazz quiz vexes Jake.']
    kwargs = create.call_args.kwargs
    assert kwargs['model'] == 'gpt-6-luna'
    assert kwargs['reasoning_effort'] == 'low'
    assert kwargs['n'] == 1
    assert 'q, z' in kwargs['messages'][0]['content']


def test_an_empty_reply_is_an_error_not_a_blank_sentence() -> None:
    with patch.object(generate.client.chat.completions, 'create') as create:
        create.return_value = completion(None)
        try:
            generate.generate_samples(1, 4, ['q'], 'en')
        except RuntimeError as error:
            assert 'no sentence' in str(error)
        else:
            raise AssertionError('expected a RuntimeError')
