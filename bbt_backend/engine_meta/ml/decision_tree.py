"""
Decision tree for regression — pure Python, no numpy, no sklearn.
Split criterion: variance reduction.
Serialisation: JSON (human-readable, portable).
"""

import json
import random


class DecisionTree:
    """
    A single regression decision tree.
    Predicts a continuous target (reward, 0.0–1.0).
    """

    def __init__(self, max_depth=10, min_samples_leaf=5, feature_indices=None):
        """
        feature_indices — list of dim indices this tree is allowed to split on.
        If None, all dims are eligible (used in unit tests; RF always passes a subset).
        """
        self.max_depth        = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.feature_indices  = feature_indices
        self.root             = None

    # ── Training ─────────────────────────────────────────────────────────

    def fit(self, X: list, y: list) -> None:
        """
        X — list of vectors (each a list of floats, length VECTOR_SIZE)
        y — list of float targets
        """
        if not X or not y:
            raise ValueError('Empty training data.')
        if len(X) != len(y):
            raise ValueError('X and y length mismatch.')
        indices = list(range(len(X)))
        feat_idx = self.feature_indices or list(range(len(X[0])))
        self.root = self._build(X, y, indices, feat_idx, depth=0)

    def _build(self, X, y, indices, feat_idx, depth):
        values = [y[i] for i in indices]
        node_mean = _mean(values)

        # Leaf conditions
        if (depth >= self.max_depth
                or len(indices) < 2 * self.min_samples_leaf
                or _variance(values) < 1e-9):
            return {'leaf': True, 'value': node_mean, 'n': len(indices)}

        best = _best_split(X, y, indices, feat_idx, self.min_samples_leaf)

        if best is None:
            return {'leaf': True, 'value': node_mean, 'n': len(indices)}

        feat, threshold, left_idx, right_idx = best

        return {
            'leaf':      False,
            'feat':      feat,
            'threshold': threshold,
            'n':         len(indices),
            'left':      self._build(X, y, left_idx,  feat_idx, depth + 1),
            'right':     self._build(X, y, right_idx, feat_idx, depth + 1),
        }

    # ── Prediction ────────────────────────────────────────────────────────

    def predict(self, vector: list) -> float:
        if self.root is None:
            raise RuntimeError('Tree not trained. Call fit() first.')
        return _traverse(self.root, vector)

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'max_depth':        self.max_depth,
            'min_samples_leaf': self.min_samples_leaf,
            'feature_indices':  self.feature_indices,
            'root':             self.root,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'DecisionTree':
        tree = cls(
            max_depth=d['max_depth'],
            min_samples_leaf=d['min_samples_leaf'],
            feature_indices=d.get('feature_indices'),
        )
        tree.root = d['root']
        return tree


# ── Internal functions ────────────────────────────────────────────────────────

def _mean(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def _variance_reduction(parent: list, left: list, right: list) -> float:
    """
    Weighted variance reduction — the split criterion.
    Higher = better split.
    """
    n  = len(parent)
    nl = len(left)
    nr = len(right)
    if nl == 0 or nr == 0:
        return 0.0
    return (_variance(parent)
            - (nl / n) * _variance(left)
            - (nr / n) * _variance(right))


def _best_split(X, y, indices, feat_idx, min_samples_leaf):
    """
    Find the best (feature, threshold) split among feat_idx for the given indices.
    Returns (feat, threshold, left_indices, right_indices) or None.
    """
    parent_y = [y[i] for i in indices]
    best_score    = -1.0
    best_feat     = None
    best_threshold= None
    best_left     = None
    best_right    = None

    for feat in feat_idx:
        # Collect unique values for this feature
        values = sorted(set(X[i][feat] for i in indices))
        if len(values) < 2:
            continue

        # Candidate thresholds: midpoints between consecutive unique values
        thresholds = [
            (values[k] + values[k + 1]) / 2.0
            for k in range(len(values) - 1)
        ]

        for threshold in thresholds:
            left_idx  = [i for i in indices if X[i][feat] <= threshold]
            right_idx = [i for i in indices if X[i][feat] >  threshold]

            if (len(left_idx)  < min_samples_leaf
                    or len(right_idx) < min_samples_leaf):
                continue

            left_y  = [y[i] for i in left_idx]
            right_y = [y[i] for i in right_idx]
            score   = _variance_reduction(parent_y, left_y, right_y)

            if score > best_score:
                best_score     = score
                best_feat      = feat
                best_threshold = threshold
                best_left      = left_idx
                best_right     = right_idx

    if best_feat is None:
        return None
    return best_feat, best_threshold, best_left, best_right


def _traverse(node: dict, vector: list) -> float:
    """Walk the tree to a leaf and return its value."""
    if node['leaf']:
        return node['value']
    if vector[node['feat']] <= node['threshold']:
        return _traverse(node['left'], vector)
    return _traverse(node['right'], vector)