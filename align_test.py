from align import align


def marked(sample: str, reading: str) -> str:
    """The sample with each letter the reading doesn't match replaced by an underscore."""
    return ''.join(ch if ok else '_' for ch, ok in zip(sample, align(sample, reading)))


def test_a_perfect_reading_matches_every_letter() -> None:
    assert marked('Zombiescanmovecars.', 'Zombiescanmovecars.') == 'Zombiescanmovecars.'


def test_a_reading_of_the_first_word_matches_only_that_word() -> None:
    assert marked('Zombiescanmovecars.', 'Zombies') == 'Zombies____________'


def test_a_reading_of_the_last_word_matches_only_that_word() -> None:
    assert marked('Zombiescanmovecars.', 'cars.') == '______________cars.'


def test_a_misread_letter_doesnt_scatter_the_rest_of_the_word() -> None:
    assert marked('Fredjumpsforjoy.', 'Frcd') == 'Fr_d____________'


def test_a_missed_first_letter_leaves_the_rest_in_place() -> None:
    assert marked('Stevekeepspigssafe.', 'tevekee') == '_tevekee___________'


def test_a_stray_speck_in_the_reading_costs_nothing() -> None:
    assert marked('Acatcanrelax.', 'A1catcanrelax.') == 'Acatcanrelax.'


def test_case_counts() -> None:
    assert marked('Zombiescanmovecars.', 'zombiescanmovecars.') == '_ombiescanmovecars.'
