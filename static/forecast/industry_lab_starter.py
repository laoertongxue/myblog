"""Six-industry teaching fixtures. Python 3.10+, standard library only.
Run: python industry_lab_starter.py --output ./industry_lab_output
All records are simulated; no external connections or operational execution.
This is a starter, not six completed forecasting projects.
"""
import argparse
import csv
import json
import math
import random
from pathlib import Path


def save(folder, name, rows):
    rows = list(rows)
    if not rows:
        raise ValueError('Empty table: ' + name)
    with (folder / name).open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def tsb_update(p, z, observed, alpha=.2, beta=.2):
    if observed is None:
        return p, z
    if observed < 0 or not (0 < alpha <= 1 and 0 < beta <= 1):
        raise ValueError('Invalid demand or smoothing parameter')
    p = (1-beta)*p + beta*int(observed > 0)
    if observed > 0:
        z = (1-alpha)*z + alpha*observed
    return p, z


def integer_allocation(total, proportions):
    if total < 0 or not isinstance(total, int):
        raise ValueError('Total must be a nonnegative integer')
    if any(p < 0 for p in proportions) or not math.isclose(sum(proportions), 1):
        raise ValueError('Proportions must sum to 1')
    raw = [total*p for p in proportions]
    result = [math.floor(x) for x in raw]
    order = sorted(range(len(raw)), key=lambda i: (-(raw[i]-result[i]), i))
    for i in order[:total-sum(result)]:
        result[i] += 1
    return result


def fefo_demo(demands):
    # Expiry_day is inclusive: a batch is usable through that day's end.
    batches = [{'qty': 6, 'expiry': 3}, {'qty': 10, 'expiry': 30}]
    shortage, expired = 0, 0
    for day, demand in enumerate(demands, 1):
        for batch in batches:
            if batch['expiry'] < day:
                expired += batch['qty']
                batch['qty'] = 0
            take = min(batch['qty'], demand)
            batch['qty'] -= take
            demand -= take
        shortage += demand
    return shortage, expired


def self_test():
    assert math.isclose(100*.3/.75, 40)
    assert math.isclose(6/(6+2), .75)
    assert (80+2*100+140)/4 == 105
    assert integer_allocation(105, [.2, .5, .3]) == [21, 53, 31]
    assert math.isclose(100*(1+.4)-10, 130)
    net = 80*.12+50*.08
    assert math.isclose(net, 13.6)
    gross = net/.85
    assert math.isclose(gross, 16)
    assert math.ceil(max(0, gross+2-5-3)/4) == 3
    assert min(90//1, 160//2) == 80
    p, z = tsb_update(.2, 3, 0)
    assert math.isclose(p*z, .48)
    p, z = tsb_update(p, z, 4)
    assert math.isclose(p*z, 1.0496)
    assert tsb_update(p, z, None) == (p, z)
    assert fefo_demo([2, 2, 2, 3, 2, 2, 2]) == (0, 0)
    assert fefo_demo([0, 0, 0, 6, 3, 3, 3]) == (5, 6)
    return 'All formula/state assertions passed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='industry_lab_output')
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20261106)
    counts = {}
    # Each family has its own synthetic process; not an empirical industry claim.
    for family, locations, skus in [
        ('fresh', 3, 6), ('apparel', 1, 72), ('fmcg', 3, 12),
        ('hewei_dishes', 2, 4), ('spares', 3, 20), ('pharma', 4, 10)
    ]:
        folder = out / family
        folder.mkdir(exist_ok=True)
        rows, truths = [], []
        for day in range(1, 181):
            for location in range(1, locations+1):
                for sku in range(1, skus+1):
                    promo = int(day % 35 in (0, 1))
                    base = 10 + sku % 7 + location
                    expected = base + (4 if day % 7 in (0, 6) else 0)
                    if family == 'fmcg':
                        expected *= 1+.4*promo
                    latent = max(0, round(expected + rng.gauss(0, 3)))
                    if family == 'spares':
                        latent = rng.randint(1, 5) if rng.random() < .18 else 0
                    if family == 'pharma':
                        latent = rng.randint(0, 3)
                    opening = max(0, round(base*1.7))
                    if family == 'fresh' and rng.random() < .15:
                        opening = round(base*.6)
                    observed = min(latent, opening) if family == 'fresh' else latent
                    row = dict(day=day, location_id=location, sku_id=sku,
                               sales=observed, active_flag=1,
                               observation_complete=1,
                               stockout_flag=int(family == 'fresh' and latent >= opening),
                               opening_stock=opening)
                    if family == 'fmcg':
                        row.update(promo_flag=promo, announced_discount=.1*promo,
                                   announced_day=day-14)
                    if family == 'spares':
                        row['demand'] = row.pop('sales')
                    rows.append(row)
                    if family == 'fresh':
                        truths.append(dict(day=day, location_id=location,
                                           sku_id=sku, latent_demand=latent))
        expected_count = 180*locations*skus
        assert len(rows) == expected_count
        assert len({(r['day'],r['location_id'],r['sku_id']) for r in rows}) == expected_count
        counts[family] = save(folder, 'daily.csv', rows)
        if truths:
            save(folder, 'truth_scoring_only.csv', truths)
        if family == 'fresh':
            save(folder, 'sku.csv', [dict(sku_id=k, net_kg=.3,
                 yield_rate=.75, shelf_life_days=2) for k in range(1,7)])
        if family == 'apparel':
            save(folder, 'sku_style_map.csv', [dict(sku_id=k,
                 style_id=(k-1)//6+1, color=(k-1)%6//3+1,
                 size=['S','M','L'][(k-1)%3]) for k in range(1,73)])
        if family == 'hewei_dishes':
            save(folder, 'first14days.csv', [r for r in rows if r['day'] <= 14])
            save(folder, 'recipe.csv', [dict(dish_id=d, ingredient_id=j,
                 net_kg_per_serving=.1 if j%2 else .05,
                 valid_from=1, valid_to=180)
                 for d in range(1,5) for j in (2*d-1,2*d)])
        if family == 'pharma':
            save(folder, 'batches.csv', [dict(location_id=l, sku_id=k,
                 batch_id=f'{l}-{k}-{b}', qty=6 if b==1 else 10,
                 expiry_day=3 if b==1 else 30, quality_status='released')
                 for l in range(1,5) for k in range(1,11) for b in (1,2)])
    manifest = dict(simulated=True, seed=20261106,
        split=dict(train=[1,112], validation=[113,140], test=[141,180]),
        test_note='The full starter is visible; seal test data before model selection. Do not claim blind evaluation after viewing it.',
        limits='Starter fixtures only. Add launches, recipes, inventory events and time-aware backtesting as specified in the lessons.',
        row_counts=counts, verification=self_test())
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
