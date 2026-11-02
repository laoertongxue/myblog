"""D9-v1 deterministic generator. LCG constants define every bit, no packages."""
from datetime import date, timedelta
from baseline import validate

VERSION = 'D9-v1'
SEED = 20261102
START = date(2026, 4, 6)  # Monday; all 180 days predate this article.
SPLITS = {'train': [1, 112], 'validation': [113, 140], 'test': [141, 180]}


def generate(case='hewei'):
    if case not in ('hewei', 'apparel'):
        raise ValueError('unknown simulation case')
    state = SEED + (case == 'apparel')
    week = [20, 22, 21, 24, 28, 36, 32] if case == 'hewei' else [80, 84, 86, 88, 110, 140, 126]
    rows = []
    for day in range(1, 181):
        state = (1664525 * state + 1013904223) % (2 ** 32)
        noise = state % 7 - 3
        trend = (day - 1) // 14 if case == 'apparel' else 0
        promotion = 90 if case == 'apparel' and 118 <= day <= 120 else 0
        rows.append({'date': (START + timedelta(days=day-1)).isoformat(),
                     'demand': max(0, week[(day-1) % 7] + noise + trend + promotion)})
    validate(rows)
    return rows
