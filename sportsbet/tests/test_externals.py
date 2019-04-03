"""
Test the externals module.
"""

import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils import shuffle
from sklearn.base import clone
import pytest

from sportsbet.externals import TimeSeriesSplit, MultiOutputClassifiers

@pytest.mark.parametrize('n_splits, min_train_size', [
    (1, 0.4),
    (1, 0.9),
    (1, 1.5),
    (2, 1.4),
    (3, 0.00)
])
def test_time_series_split_errors(n_splits, min_train_size):
    """Test time series cross validator errors."""
    with pytest.raises(ValueError):
        TimeSeriesSplit(n_splits, min_train_size)


@pytest.mark.parametrize('n_splits, min_train_size', [
    (2, 0.4),
    (3, 0.4),
    (4, 0.4),
    (2, 0.9),
    (3, 0.95),
    (5, 0.9),
    (10, 0.1)
])
def test_time_series_split(n_splits, min_train_size):
    """Test time series cross validator."""
    X, _ = make_classification(random_state=0)
    tscv = TimeSeriesSplit(n_splits, min_train_size)
    indices = list(tscv.split(X))
    assert len(indices) == n_splits == tscv.get_n_splits(X)
    for train_indices, test_indices in indices:
        assert train_indices[0] == 0
        assert len(train_indices) >= int(min_train_size * len(X))
        assert not set(train_indices).intersection(test_indices)
        assert max(train_indices) + 1 == min(test_indices)
    assert test_indices[-1] == len(X) - 1


def test_multi_output_classification():
    """Test if multi-output classifiers initialize correctly with base classifiers 
    and fit. Assert predictions work as expected for predict, prodict_proba and score."""
    
    # Create multi-output data
    X, y1 = make_classification(n_classes=3, random_state=0, n_informative=5)
    y2 = shuffle(y1, random_state=1)
    y3 = shuffle(y1, random_state=2)
    y = np.column_stack((y1, y2, y3))
    n_samples, n_outputs = y.shape
    n_classes = len(np.unique(y1))

    # Create multi-output classifiers
    classifiers = [
        ('rf', RandomForestClassifier(n_estimators=10, random_state=0)),
        ('lr', LogisticRegression(solver='lbfgs', multi_class='auto', random_state=1)),
        ('dt', DecisionTreeClassifier(random_state=2))
    ] 
    multi_output_clfs = MultiOutputClassifiers(classifiers)

    # Fit and get predictions
    multi_output_clfs.fit(X, y)
    y_pred = multi_output_clfs.predict(X)
    y_pred_proba = multi_output_clfs.predict_proba(X)
    
    # Assert correct prediction shapes
    assert y_pred.shape == (n_samples, n_outputs) 
    assert len(y_pred_proba) == n_outputs
    for proba in y_pred_proba:
        (n_samples, n_classes) == proba.shape

    # Assert class and probability predictions are consistent
    np.testing.assert_array_equal(np.column_stack([np.argmax(proba, axis=1) for proba in y_pred_proba]), y_pred)
    
    # Assert class and probability predictions are correct
    for ind, (_, clf) in enumerate(classifiers):
        cloned_clf = clone(clf).fit(X, y[:, ind])
        np.testing.assert_array_equal(cloned_clf.predict(X), y_pred[:, ind])
        np.testing.assert_array_equal(cloned_clf.predict_proba(X), y_pred_proba[ind])
