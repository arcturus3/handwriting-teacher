from Bio import Align

# Every score is set here, so a Biopython upgrade can't change how letters are matched:
# 1.86 changed the default gap extension from 0 to -1, which made splitting a gap cheaper
# than extending it and scattered a partial reading's letters across the sentence.
MATCH = 2.0
MISMATCH = -1.0  # a misread letter costs less than a gap, so it stays in place
GAP_OPEN = -2.0
GAP_EXTEND = -0.5  # less than opening, so one long gap beats several short ones
# A reading often covers only part of the sentence: the writer stopped early, or the
# detector missed the first or last word. Gaps at either end cost nothing.
END_GAP = 0.0


def make_aligner() -> Align.PairwiseAligner:
    aligner = Align.PairwiseAligner()
    aligner.mode = 'global'
    aligner.match_score = MATCH
    aligner.mismatch_score = MISMATCH
    aligner.open_gap_score = GAP_OPEN
    aligner.extend_gap_score = GAP_EXTEND
    aligner.end_gap_score = END_GAP
    return aligner


ALIGNER = make_aligner()


def align(sample: str, pred: str) -> list[bool]:
    """For each letter of the sample, whether the reading has that letter in its place."""
    success = [False] * len(sample)
    if not pred or not sample:
        return success
    alignment = ALIGNER.align(sample, pred)[0]
    sample_groups, pred_groups = alignment.aligned
    for sample_group, pred_group in zip(sample_groups, pred_groups):
        for i in range(sample_group[1] - sample_group[0]):
            sample_idx = sample_group[0] + i
            if sample[sample_idx] == pred[pred_group[0] + i]:
                success[sample_idx] = True
    return success
