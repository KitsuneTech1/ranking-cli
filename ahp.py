"""Small pairwise AHP helper built on ranking-cli's weighted sum."""

import math
from typing import List, Sequence, Tuple

from ranking_cli import rank_options


_SAATY_RI = {
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
    11: 1.51,
    12: 1.48,
    13: 1.56,
    14: 1.57,
    15: 1.59,
}


def pairwise_weights(matrix: Sequence[Sequence[float]]) -> Tuple[List[float], float]:
    """Return normalized criterion weights and the AHP consistency ratio.

    ``matrix[i][j]`` means criterion ``i`` is preferred over criterion ``j``.
    Values must be positive, diagonal entries must be 1, and off-diagonal
    entries must be reciprocal.
    """
    try:
        rows = [list(row) for row in matrix]
    except TypeError:
        raise ValueError("AHP matrix must be a non-empty square matrix")
    size = len(rows)
    if not size or any(len(row) != size for row in rows):
        raise ValueError("AHP matrix must be a non-empty square matrix")
    if size > max(_SAATY_RI):
        raise ValueError("AHP consistency ratios are supported for matrices up to 15x15")

    numeric_rows = []
    for row in rows:
        numeric_row = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("AHP matrix values must be finite positive numbers")
            numeric_value = float(value)
            if not math.isfinite(numeric_value) or numeric_value <= 0:
                raise ValueError("AHP matrix values must be finite positive numbers")
            numeric_row.append(numeric_value)
        numeric_rows.append(numeric_row)

    for row_index, row in enumerate(numeric_rows):
        for column_index, value in enumerate(row):
            if row_index == column_index and not math.isclose(value, 1.0):
                raise ValueError("AHP matrix diagonal entries must be 1")
            if row_index < column_index and not math.isclose(value * numeric_rows[column_index][row_index], 1.0):
                raise ValueError("AHP matrix entries must be reciprocal")

    geometric_means = [math.exp(sum(math.log(value) for value in row) / size) for row in numeric_rows]
    total = sum(geometric_means)
    weights = [value / total for value in geometric_means]
    if size < 3:
        return weights, 0.0

    weighted_totals = [sum(value * weight for value, weight in zip(row, weights)) for row in numeric_rows]
    lambda_max = sum(total_value / weight for total_value, weight in zip(weighted_totals, weights)) / size
    consistency_index = max(0.0, (lambda_max - size) / (size - 1))
    consistency_ratio = consistency_index / _SAATY_RI[size]
    return weights, consistency_ratio


def rank_with_ahp(options, criteria: Sequence[str], matrix, reverse: bool = True):
    """Rank options using AHP-derived criterion weights and weighted sums.

    Returns ``(ranked_options, consistency_ratio)``. A consistency ratio near
    zero is ideal. The function does not reject an inconsistent matrix because
    the ratio is useful evidence for the caller to review.
    """
    if isinstance(criteria, str):
        raise ValueError("AHP criteria must be unique non-empty names")
    try:
        criteria = list(criteria)
        matrix_size = len(matrix)
    except TypeError:
        raise ValueError("AHP criteria must be unique non-empty names")
    if len(criteria) != matrix_size:
        raise ValueError("The number of criteria must match the AHP matrix size")
    if any(not isinstance(criterion, str) or not criterion for criterion in criteria):
        raise ValueError("AHP criteria must be unique non-empty names")
    criteria = [criterion.strip() for criterion in criteria]
    if any(not criterion for criterion in criteria):
        raise ValueError("AHP criteria must be unique non-empty names")
    if len(set(criteria)) != len(criteria):
        raise ValueError("AHP criteria must be unique non-empty names")
    weights, consistency_ratio = pairwise_weights(matrix)
    ranked = rank_options(options, dict(zip(criteria, weights)), reverse=reverse)
    return ranked, consistency_ratio
