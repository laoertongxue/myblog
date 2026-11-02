"""Independent review oracle; reads no sealed labels and writes no experiment files."""
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/d9-seasonal-naive'))
from baseline import forecast_at

rows = [{'date': (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
         'demand': i + 1} for i in range(180)]
records = []
for origin in (7, 8, 11, 14, 15, 105, 112, 113, 139, 140):
    for horizon in (1, 5, 7, 8, 14, 15, 40):
        # Distinct one-based values make the returned value its source day.
        expected = [origin + h - 7 * ((h - 1) // 7 + 1)
                    for h in range(1, horizon + 1)]
        actual = forecast_at(rows, origin, horizon)
        assert actual == expected, (origin, horizon, actual, expected)
        records.append({'origin': origin, 'horizon': horizon,
                        'expected': expected, 'actual': actual})
    poisoned = deepcopy(rows)
    for row in poisoned[origin:]:
        row.update(date='poison', demand=None)
    assert forecast_at(poisoned, origin, 40) == forecast_at(rows, origin, 40)

print(json.dumps({'oracle_cases': records, 'future_poison_origins': 10,
                  'sealed_labels_read': False}, indent=2))
