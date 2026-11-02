"""D9-v1: fully observed, daily nonnegative demand; Python standard library."""
from datetime import date, timedelta
import math


def validate(rows):
    if not rows:
        raise ValueError('empty history')
    previous = None
    for row in rows:
        day = date.fromisoformat(row['date'])
        value = row['demand']
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('demand must be finite and nonnegative')
        if previous is not None and day != previous + timedelta(days=1):
            raise ValueError('dates must be ordered, unique and continuous')
        previous = day


def seasonal_naive(history, horizon, period=7):
    if type(horizon) is not int or horizon < 1:
        raise ValueError('horizon must be a positive integer')
    if type(period) is not int or period < 1:
        raise ValueError('period must be a positive integer')
    validate(history)
    if len(history) < period:
        raise ValueError('insufficient history for one complete season')
    return [history[-period + (h % period)]['demand'] for h in range(horizon)]


def forecast_at(rows, origin, horizon):
    """origin is a one-based last known day; slice BEFORE validation/prediction."""
    if type(origin) is not int or not 1 <= origin <= len(rows):
        raise ValueError('invalid origin')
    return seasonal_naive(rows[:origin], horizon)


def windows(start, end, horizon):
    if any(type(x) is not int for x in (start, end, horizon)) or start < 1 or end < start or horizon < 1:
        raise ValueError('invalid evaluation block')
    return [(first - 1, first, first + horizon - 1)
            for first in range(start, end - horizon + 2)]
