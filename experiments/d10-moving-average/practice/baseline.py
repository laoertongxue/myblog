"""D10-v1: causal moving-average and weekly seasonal-naive baselines.

Only complete, observed, daily demand is accepted. An origin is the one-based
last known day, not the target day. Fixed-origin forecasts never update their
history with either future actuals or their own predictions.
"""
from datetime import date, timedelta
import csv
import math
from pathlib import Path


def _positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f'{name} must be a positive integer')


def validate(rows):
    """Validate one series of consecutive dates; zero demand is legitimate."""
    if not rows:
        raise ValueError('empty history')
    previous_date = None
    previous_day = None
    series = None
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('each row must be a mapping')
        try:
            current_date = date.fromisoformat(row['date'])
            day = row['day']
            value = row['demand']
            current_series = row['series']
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('missing or invalid row field') from exc
        if row['date'] != current_date.isoformat():
            raise ValueError('date must use canonical YYYY-MM-DD format')
        _positive_integer(day, 'day')
        if not isinstance(current_series, str) or not current_series.strip():
            raise ValueError('series must be a nonempty string')
        if series is None:
            series = current_series
        elif current_series != series:
            raise ValueError('cannot mix entities or measurement units')
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('demand must be finite, numeric and nonnegative')
        try:
            finite = math.isfinite(value)
        except OverflowError as exc:
            raise ValueError('demand exceeds supported finite numeric range') from exc
        if not finite or value < 0:
            raise ValueError('demand must be finite, numeric and nonnegative')
        if previous_date is not None:
            if current_date != previous_date + timedelta(days=1) or day != previous_day + 1:
                raise ValueError('days and dates must be ordered, unique and continuous')
        previous_date, previous_day = current_date, day


def load_csv(path, series):
    """Read a single explicitly identified series without imputing bad data.

    D9 CSVs have no entity column: the caller supplies the series identity.
    A separate metadata contract fixes case/unit; these files are not a
    multi-entity format and must never be concatenated.
    """
    rows = []
    try:
        with Path(path).open(encoding='utf-8', newline='') as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames != ['day', 'date', 'demand', 'split']:
                raise ValueError('CSV header must be day,date,demand,split')
            for raw in reader:
                if set(raw) != {'day', 'date', 'demand', 'split'} or any(v is None for v in raw.values()):
                    raise ValueError('missing or surplus CSV field')
                try:
                    # int("True"), float("True"), empty and NULL all fail.
                    row = {'day': int(raw['day']), 'date': raw['date'],
                           'demand': float(raw['demand']), 'split': raw['split'],
                           'series': series}
                except (TypeError, ValueError) as exc:
                    raise ValueError('invalid numeric CSV value') from exc
                if raw['day'] != str(row['day']):
                    raise ValueError('day must be a canonical positive integer')
                if row['split'] not in {'train', 'validation'}:
                    raise ValueError('only train and validation rows are allowed')
                rows.append(row)
    except csv.Error as exc:
        raise ValueError(f'malformed CSV syntax: {exc}') from exc
    validate(rows)
    return rows


def validate_development(rows):
    """D9-v1 source contract; intentionally excludes all 40 test labels."""
    validate(rows)
    if len(rows) != 140 or rows[0]['day'] != 1 or rows[0]['date'] != '2026-04-06':
        raise ValueError('development data must be original days 1..140')
    for row in rows:
        expected = 'train' if row['day'] <= 112 else 'validation'
        if row.get('split') != expected:
            raise ValueError('112/28 development split mismatch')


def moving_average(history, horizon, k):
    _positive_integer(horizon, 'horizon')
    _positive_integer(k, 'k')
    validate(history)
    if len(history) < k:
        raise ValueError('insufficient history for full moving-average window')
    # Divide before summing to avoid overflow from finite, very large inputs.
    mean = math.fsum(row['demand'] / k for row in history[-k:])
    if not math.isfinite(mean):
        raise ValueError('nonfinite forecast')
    return [mean] * horizon


def seasonal_naive(history, horizon, period=7):
    _positive_integer(horizon, 'horizon')
    _positive_integer(period, 'period')
    validate(history)
    if len(history) < period:
        raise ValueError('insufficient history for full seasonal cycle')
    return [history[-period + h % period]['demand'] for h in range(horizon)]


def forecast_at(rows, origin, horizon, method='moving_average', k=7):
    """Slice at the information boundary BEFORE validation or forecasting.

    origin is the number of observations known, which equals day for the
    development data (starts at day 1). No row after origin is inspected here.
    """
    _positive_integer(origin, 'origin')
    if origin > len(rows):
        raise ValueError('origin beyond available data')
    history = rows[:origin]
    if method == 'moving_average':
        return moving_average(history, horizon, k)
    if method == 'seasonal_naive_7':
        return seasonal_naive(history, horizon, period=7)
    raise ValueError('unknown forecast method')


def windows(start, end, horizon):
    """Return (origin, first target, last target); never cross block edges."""
    for value, name in ((start, 'start'), (end, 'end'), (horizon, 'horizon')):
        _positive_integer(value, name)
    if end < start:
        raise ValueError('evaluation end precedes start')
    return [(first - 1, first, first + horizon - 1)
            for first in range(start, end - horizon + 2)]
