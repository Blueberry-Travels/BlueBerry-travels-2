"""
Random Forest regressor — pure Python, no numpy, no sklearn.
100 trees, bootstrap sampling, random feature subsets per split.
Serialisation: JSON.
"""

import json
import math
import random

from engine_meta.ml.decision_tree import DecisionTree
from engine_meta.ml.feature_extractor import VECTOR_SIZE


class RandomForest:
    """
    Ensemble of DecisionTree regressors.
    Prediction = mean of all tree predictions.
    """

    def __init__(self,
                 n_trees=100,
                 max_depth=10,
                 min_samples_leaf=5,
                 feature_subset_size=None,
                 seed=42):
        self.n_trees           = n_trees
        self.max_depth         = max_depth
        self.min_samples_leaf  = min_samples_leaf
        # int(sqrt(VECTOR_SIZE)) = 6 — matches spec
        self.feature_subset_size = feature_subset_size or int(math.sqrt(VECTOR_SIZE))
        self.seed              = seed
        self.trees             = []
        self.is_trained        = False

    # ── Training ──────────────────────────────────────────────────────────

    def fit(self, X: list, y: list) -> None:
        """
        X — list of 48-dim vectors
        y — list of float targets (reward)
        Trains n_trees on bootstrap samples with random feature subsets.
        """
        if not X or not y:
            raise ValueError('Empty training data.')
        if len(X) != len(y):
            raise ValueError('X and y length mismatch.')

        n          = len(X)
        all_feats  = list(range(len(X[0])))
        rng        = random.Random(self.seed)
        self.trees = []

        for t in range(self.n_trees):
            # Bootstrap: sample n rows with replacement
            bootstrap_idx = [rng.randint(0, n - 1) for _ in range(n)]
            X_boot = [X[i] for i in bootstrap_idx]
            y_boot = [y[i] for i in bootstrap_idx]

            # Random feature subset for this tree
            feat_idx = rng.sample(all_feats, self.feature_subset_size)

            tree = DecisionTree(
                max_depth=self.max_depth,
                min_samples_leaf=self.min_samples_leaf,
                feature_indices=feat_idx,
            )
            tree.fit(X_boot, y_boot)
            self.trees.append(tree)

        self.is_trained = True

    # ── Prediction ────────────────────────────────────────────────────────

    def predict(self, vector: list) -> float:
        """Returns mean prediction across all trees. Range: 0.0–1.0."""
        if not self.is_trained or not self.trees:
            raise RuntimeError('Forest not trained. Call fit() first.')
        preds = [tree.predict(vector) for tree in self.trees]
        return sum(preds) / len(preds)

    def predict_batch(self, vectors: list) -> list:
        """Predict a list of vectors. Returns a list of floats."""
        return [self.predict(v) for v in vectors]

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_json(self) -> str:
        """Serialise the full forest to a JSON string."""
        return json.dumps({
            'n_trees':            self.n_trees,
            'max_depth':          self.max_depth,
            'min_samples_leaf':   self.min_samples_leaf,
            'feature_subset_size':self.feature_subset_size,
            'seed':               self.seed,
            'is_trained':         self.is_trained,
            'trees':              [t.to_dict() for t in self.trees],
        }, separators=(',', ':'))

    @classmethod
    def from_json(cls, json_str: str) -> 'RandomForest':
        """Deserialise a forest from a JSON string."""
        d  = json.loads(json_str)
        rf = cls(
            n_trees=d['n_trees'],
            max_depth=d['max_depth'],
            min_samples_leaf=d['min_samples_leaf'],
            feature_subset_size=d['feature_subset_size'],
            seed=d['seed'],
        )
        rf.is_trained = d['is_trained']
        rf.trees      = [DecisionTree.from_dict(t) for t in d['trees']]
        return rf

    def save(self, path: str) -> None:
        """Write forest JSON to disk."""
        with open(path, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> 'RandomForest':
        """Load forest from a JSON file on disk."""
        with open(path) as f:
            return cls.from_json(f.read())

    # ── Diagnostics ───────────────────────────────────────────────────────

    def feature_importances(self) -> dict:
        """
        Returns a dict of {feature_index: importance_score}.
        Importance = mean variance reduction contributed by that feature
        across all splits in all trees. Useful for debugging.
        """
        counts = {}
        totals = {}
        for tree in self.trees:
            _collect_importances(tree.root, counts, totals)
        result = {}
        for feat, total in totals.items():
            result[feat] = round(total / counts[feat], 6)
        return dict(sorted(result.items(), key=lambda x: -x[1]))


def _collect_importances(node, counts, totals):
    if node is None or node.get('leaf'):
        return
    feat = node['feat']
    counts[feat] = counts.get(feat, 0) + 1
    # Use node size as a proxy weight for importance
    totals[feat] = totals.get(feat, 0.0) + node.get('n', 1)
    _collect_importances(node.get('left'),  counts, totals)
    _collect_importances(node.get('right'), counts, totals)