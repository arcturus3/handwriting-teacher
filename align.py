from Bio import Align


def align(sample: str, pred: str) -> list[bool]:
    success = [False] * len(sample)
    if not pred or not sample:
        return success
    aligner = Align.PairwiseAligner()
    aligner.open_gap_score = -0.5  # prefer mismatches to gaps
    alignments = aligner.align(sample, pred)
    alignment = alignments[0]
    sample_groups, pred_groups = alignment.aligned
    for group_idx in range(len(sample_groups)):
        sample_group = sample_groups[group_idx]
        pred_group = pred_groups[group_idx]
        group_size = sample_group[1] - sample_group[0]
        for i in range(group_size):
            sample_idx = sample_group[0] + i
            pred_idx = pred_group[0] + i
            if sample[sample_idx] == pred[pred_idx]:
                success[sample_idx] = True
    return success
