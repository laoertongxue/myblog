#!/usr/bin/env python3
"""Offline SQLite teaching slice. Never opens a database file or a network."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parent
TABLES = {
    'candidate_orders': 'candidate-orders.csv',
    'expected_slots': 'expected-slots.csv',
    'original_lines': 'fashion-original-lines.csv',
    'anomaly_lines': 'fashion-anomaly-lines.csv',
    'original_receipts': 'fashion-original-receipts.csv',
    'anomaly_receipts': 'fashion-anomaly-receipts.csv',
    'original_snapshots': 'hewei-original-snapshots.csv',
    'anomaly_snapshots': 'hewei-anomaly-snapshots.csv',
}


def source_hashes():
    files = sorted((ROOT / 'data').glob('*.csv')) + [ROOT / 'manifest.json']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files}


def connect():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['fashion_receipts_complete_in_this_simulation'] is True
    assert manifest['fashion_candidate_orders_frozen_before_injection'] is True
    assert manifest['hewei_full_14_day_dataset_generated'] is False
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.executescript((ROOT / 'schema.sql').read_text(encoding='utf-8'))
    for table, filename in TABLES.items():
        with (ROOT / 'data' / filename).open(newline='', encoding='utf-8') as source:
            reader = csv.reader(source)
            columns = next(reader)
            values = [tuple(None if value in ('', 'NULL') else value for value in row)
                      for row in reader]
        placeholders = ','.join('?' for _ in columns)
        # The table names and CSV schemas are package constants, not user SQL.
        db.executemany(f'INSERT INTO {table} VALUES ({placeholders})', values)
    ensure_inventory_identity(db)
    db.executescript((ROOT / 'analysis.sql').read_text(encoding='utf-8'))
    return db


def rows(db, sql, parameters=()):
    return [dict(row) for row in db.execute(sql, parameters)]


def ensure_inventory_identity(db):
    """Reject ambiguous identities before joins; do not choose a snapshot."""
    for table in ('expected_slots', 'original_snapshots', 'anomaly_snapshots'):
        bad_keys = rows(db, f'''SELECT snapshot_date, store_id, sku FROM {table}
            WHERE snapshot_date IS NULL OR TRIM(snapshot_date) = ''
               OR store_id IS NULL OR TRIM(store_id) = ''
               OR sku IS NULL OR TRIM(sku) = '' ''')
        if bad_keys:
            raise ValueError(f'{table}: missing observation key: {bad_keys}')
        duplicates = rows(db, f'''SELECT snapshot_date, store_id, sku, COUNT(*) AS rows
            FROM {table} GROUP BY snapshot_date, store_id, sku HAVING COUNT(*) > 1''')
        if duplicates:
            raise ValueError(f'{table}: duplicate observation key: {duplicates}')
        if table == 'expected_slots':
            continue
        bad_ids = rows(db, f'''SELECT snapshot_date, store_id, sku, source_row_id
            FROM {table} WHERE source_row_id IS NULL OR TRIM(source_row_id) = '' ''')
        if bad_ids:
            raise ValueError(f'{table}: missing source_row_id: {bad_ids}')
        duplicate_ids = rows(db, f'''SELECT source_row_id, COUNT(*) AS rows
            FROM {table} GROUP BY source_row_id HAVING COUNT(*) > 1''')
        if duplicate_ids:
            raise ValueError(f'{table}: duplicate source_row_id: {duplicate_ids}')


def original_quantity(db, exclude=None, matched=False):
    # Always run against the preserved original inputs; never "repair" the copy.
    return rows(db, '''
        WITH per_line AS (
          SELECT l.order_id, l.line_id, l.ordered_qty,
            MIN(l.ordered_qty, COALESCE(SUM(CASE
              WHEN r.qualified = 1 AND r.accepted_qty >= 0
               AND julianday(r.accepted_at) <= julianday(l.promise_at)
              THEN r.accepted_qty ELSE 0 END), 0)) AS credited_qty
          FROM original_lines l LEFT JOIN original_receipts r USING(line_id)
          WHERE l.ordered_qty > 0 AND julianday(l.promise_at) <=
                julianday((SELECT as_of FROM config))
            AND (? IS NULL OR l.order_id <> ?)
            AND (? = 0 OR l.order_id IN (SELECT order_id FROM diagnostic_lines))
          GROUP BY l.order_id, l.line_id, l.ordered_qty
        )
        SELECT COUNT(*) AS lines, COUNT(DISTINCT order_id) AS orders,
          SUM(credited_qty) AS credited_qty, SUM(ordered_qty) AS planned_qty,
          1.0 * SUM(credited_qty) / NULLIF(SUM(ordered_qty), 0) AS fill_rate
        FROM per_line
    ''', (exclude, exclude, int(matched)))[0]


def build_report(db):
    ensure_inventory_identity(db)
    fashion = rows(db, (ROOT / 'article-fashion.sql').read_text(encoding='utf-8'))[0]
    inventory = rows(db, (ROOT / 'article-inventory.sql').read_text(encoding='utf-8'))[0]
    quality = rows(db, '''
      SELECT
        (SELECT COUNT(*) FROM anomaly_lines) AS physical_order_line_rows,
        (SELECT COUNT(DISTINCT event_id) FROM anomaly_lines) AS order_line_events,
        (SELECT COUNT(*) FROM anomaly_lines WHERE event_id IN
          (SELECT event_id FROM anomaly_lines
           WHERE event_id NOT IN (SELECT event_id FROM event_conflicts)
           GROUP BY event_id HAVING COUNT(*) > 1))
          AS replay_group_physical_rows,
        (SELECT COUNT(*) FROM confirmed_replay_rows) AS confirmed_extra_replay_rows,
        (SELECT COUNT(*) FROM event_conflicts) AS conflicting_event_groups,
        (SELECT COUNT(*) FROM canonical_lines WHERE ordered_qty < 0) AS negative_order_rows,
        (SELECT COUNT(*) FROM canonical_lines WHERE promise_at IS NULL) AS missing_promise_rows,
        (SELECT COUNT(*) FROM orphan_receipts) AS orphan_receipt_rows,
        (SELECT COUNT(*) FROM blocked_orders) AS blocked_orders,
        (SELECT COUNT(*) FROM anomaly_receipts WHERE line_id = 'L1') AS l1_receipt_events,
        (SELECT SUM(accepted_qty) FROM anomaly_receipts WHERE line_id = 'L1') AS l1_receipt_qty
    ''')[0]
    baseline_inventory = rows(db, '''
      SELECT COUNT(*) AS expected_slots, COUNT(inventory) AS valid_rows,
        SUM(CASE WHEN inventory = 0 THEN 1 ELSE 0 END) AS zero_rows,
        SUM(CASE WHEN inventory > 0 THEN 1 ELSE 0 END) AS positive_rows,
        1.0 * SUM(CASE WHEN inventory = 0 THEN 1 ELSE 0 END) / COUNT(*) AS zero_rate
      FROM original_snapshots
    ''')[0]
    unknown = inventory['missing_rows'] + inventory['null_values']
    return {
        'fashion_original_teaching_truth': original_quantity(db),
        'fashion_diagnostic_subset_not_full_kpi': fashion,
        'fashion_candidate_order_evaluation_coverage': {
            'evaluated': fashion['evaluated_orders'], 'frozen_candidates': fashion['candidate_orders'],
            'ratio': fashion['evaluated_orders'] / fashion['candidate_orders']},
        'fashion_same_cohort_original_control': original_quantity(db, matched=True),
        'fashion_selection_bias_independent_control_mask_A3': original_quantity(db, exclude='A3'),
        'fashion_quality': quality,
        'inventory_original_teaching_truth': baseline_inventory,
        'inventory_anomaly_observations': inventory,
        'inventory_unknown_state_bounds_not_point_estimate': {
            'unknown_slots': unknown, 'denominator': inventory['expected_slots'],
            'lower_zero_slots': inventory['zero_rows'],
            'upper_zero_slots': inventory['zero_rows'] + unknown,
            'lower_ratio': inventory['zero_rows'] / inventory['expected_slots'],
            'upper_ratio': (inventory['zero_rows'] + unknown) / inventory['expected_slots']},
        'inventory_wrong_zero_fill_for_comparison_only': {
            'zero_slots': inventory['zero_rows'] + unknown,
            'denominator': inventory['expected_slots'],
            'ratio': (inventory['zero_rows'] + unknown) / inventory['expected_slots']},
    }


def check_boundaries(db, report):
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append(name)

    original = report['fashion_original_teaching_truth']
    diagnostic = report['fashion_diagnostic_subset_not_full_kpi']
    control = report['fashion_selection_bias_independent_control_mask_A3']
    same = report['fashion_same_cohort_original_control']
    inventory = report['inventory_anomaly_observations']
    check('baseline_280_over_400', original['credited_qty'] == 280 and original['planned_qty'] == 400)
    check('diagnostic_180_over_200_is_blocked', diagnostic['credited_qty'] == 180
          and diagnostic['planned_qty'] == 200 and diagnostic['formal_status'] == 'BLOCKED')
    check('same_cohort_unchanged', same['credited_qty'] == 180 and same['planned_qty'] == 200)
    check('selection_bias_same_numerator', original['credited_qty'] == control['credited_qty'] == 280
          and control['planned_qty'] == 300 and control['fill_rate'] > original['fill_rate'])
    check('replay_not_split_receipts', report['fashion_quality']['confirmed_extra_replay_rows'] == 1
          and report['fashion_quality']['l1_receipt_events'] == 2
          and report['fashion_quality']['l1_receipt_qty'] == 100)
    check('inventory_32_expected_15_valid', inventory['expected_slots'] == 32
          and inventory['reported_rows'] == 16 and inventory['missing_rows'] == 16
          and inventory['null_values'] == 1 and inventory['zero_rows'] == 2
          and inventory['valid_rows'] == 15)
    check('inventory_zero_is_valid', db.execute("SELECT COUNT(*) FROM inventory_audit WHERE state='ZERO_OBSERVED' AND inventory>=0").fetchone()[0] == 2)
    for name, mutation, assertion in [
        ('conflicting_replay_is_blocked',
         "INSERT INTO anomaly_lines SELECT 'CONFLICT', origin_row_id, event_id, order_id, line_id, sku, unit, 99, promise_at FROM anomaly_lines WHERE source_row_id='AF01'",
         "SELECT COUNT(*)=1 FROM blocked_orders WHERE order_id='A1'"),
        ('conflicted_event_not_arbitrarily_chosen',
         "INSERT INTO anomaly_lines SELECT 'CONFLICT', origin_row_id, event_id, order_id, line_id, sku, unit, 99, promise_at FROM anomaly_lines WHERE source_row_id='AF01'",
         "SELECT COUNT(*)=0 FROM canonical_lines WHERE event_id='FE1'"),
        ('whole_order_block_not_just_bad_line',
         "INSERT INTO anomaly_lines VALUES ('EXTRA','', 'EXTRA_EVENT','A4','L4-extra','TEE-M','件',100,'2026-10-21T12:00:00+07:00')",
         "SELECT COUNT(*)=0 FROM diagnostic_lines WHERE order_id='A4'"),
        ('independent_events_same_key_are_not_auto_deduped',
         "INSERT INTO anomaly_lines SELECT 'NEW_EVENT','', 'FE_NEW',order_id,line_id,sku,unit,ordered_qty,promise_at FROM anomaly_lines WHERE source_row_id='AF01'",
         "SELECT COUNT(*)=1 FROM line_key_conflicts WHERE line_id='L1'"),
        ('empty_inventory_denominator_is_null',
         "UPDATE anomaly_snapshots SET inventory=NULL",
         "SELECT (1.0*SUM(CASE WHEN inventory=0 THEN 1 ELSE 0 END)/NULLIF(SUM(CASE WHEN inventory>=0 THEN 1 ELSE 0 END),0)) IS NULL FROM inventory_audit"),
        ('empty_order_denominator_is_null',
         "UPDATE anomaly_lines SET ordered_qty=-1",
         "SELECT (1.0*SUM(credited_qty)/NULLIF(SUM(ordered_qty),0)) IS NULL FROM diagnostic_line_result"),
    ]:
        db.execute('SAVEPOINT boundary_case')
        db.execute(mutation)
        check(name, db.execute(assertion).fetchone()[0] == 1)
        db.execute('ROLLBACK TO boundary_case')
        db.execute('RELEASE boundary_case')
    db.execute('SAVEPOINT conflict_scope')
    db.execute("INSERT INTO anomaly_lines SELECT 'CONFLICT',origin_row_id,event_id,order_id,line_id,sku,unit,99,promise_at FROM anomaly_lines WHERE source_row_id='AF01'")
    db.execute("INSERT INTO anomaly_lines VALUES ('SIBLING','','SIBLING_EVENT','A1','L1-SIBLING','TEE-M','件',50,'2026-10-21T12:00:00+07:00')")
    check('conflict_blocks_normal_sibling_line', db.execute("SELECT COUNT(*) FROM diagnostic_lines WHERE order_id='A1'").fetchone()[0] == 0)
    check('conflict_not_counted_as_confirmed_replay', db.execute('SELECT COUNT(*) FROM confirmed_replay_rows').fetchone()[0] == 0)
    _, conflict_audit, conflict_log = audits(db)
    conflicting = [row for row in conflict_audit if row['event_id'] == 'FE1']
    check('conflict_audit_labels_are_not_replay', len(conflicting) == 3
          and all(row['disposition'] == 'EVENT_PAYLOAD_CONFLICT' for row in conflicting)
          and any(row['issue'] == 'EVENT_PAYLOAD_CONFLICT' for row in conflict_log)
          and not any(row['issue'] == 'REPLAY_CONFIRMED' and row['key'] == 'FE1' for row in conflict_log))
    db.execute('ROLLBACK TO conflict_scope')
    db.execute('RELEASE conflict_scope')
    for name, mutation, error_text in [
        ('duplicate_snapshot_key_refuses_calculation',
         "INSERT INTO anomaly_snapshots SELECT 'DUPLICATE','',snapshot_date,store_id,sku,inventory FROM anomaly_snapshots WHERE source_row_id='AI001'",
         'duplicate observation key'),
        ('missing_snapshot_source_id_refuses_calculation',
         "UPDATE anomaly_snapshots SET source_row_id=NULL WHERE source_row_id='AI001'",
         'missing source_row_id'),
        ('duplicate_snapshot_source_id_refuses_calculation',
         "UPDATE anomaly_snapshots SET source_row_id='AI001' WHERE source_row_id='AI002'",
         'duplicate source_row_id'),
        ('empty_expected_key_refuses_calculation',
         "UPDATE expected_slots SET store_id='' WHERE snapshot_date='2026-10-10' AND store_id='S01' AND sku='K01'",
         'missing observation key'),
    ]:
        db.execute('SAVEPOINT identity_gate')
        db.execute(mutation)
        rejected = False
        try:
            build_report(db)
        except ValueError as error:
            rejected = error_text in str(error)
        check(name, rejected)
        db.execute('ROLLBACK TO identity_gate')
        db.execute('RELEASE identity_gate')
    return checks


def audits(db):
    ensure_inventory_identity(db)
    inventory = rows(db, '''
      SELECT a.*, o.source_row_id AS teaching_original_source,
        o.inventory AS teaching_original_inventory
      FROM inventory_audit a JOIN original_snapshots o
        USING(snapshot_date, store_id, sku)
      ORDER BY a.snapshot_date, a.store_id, a.sku
    ''')
    fashion = rows(db, '''
      SELECT a.*, CASE
        WHEN a.event_id IN (SELECT event_id FROM event_conflicts)
          THEN 'EVENT_PAYLOAD_CONFLICT'
        WHEN a.line_id IN (SELECT line_id FROM line_key_conflicts)
          THEN 'LINE_KEY_CONFLICT'
        WHEN a.source_row_id IN (SELECT source_row_id FROM confirmed_replay_rows)
          THEN 'CONFIRMED_REPLAY_FOLDED'
        WHEN a.order_id IN (SELECT order_id FROM blocked_orders) THEN 'ORDER_BLOCKED'
        ELSE 'DIAGNOSTIC_SUBSET_ONLY' END AS disposition,
        CASE WHEN a.order_id IN (SELECT order_id FROM blocked_orders)
          THEN 1 ELSE 0 END AS order_blocked
      FROM anomaly_lines a ORDER BY a.source_row_id
    ''')
    log = []
    for event in rows(db, '''SELECT event_id, GROUP_CONCAT(source_row_id,'|') AS sources,
                            COUNT(*) AS hit_rows, MIN(source_row_id) AS representative
                            FROM anomaly_lines GROUP BY event_id'''):
        conflict = db.execute('SELECT 1 FROM event_conflicts WHERE event_id=?', (event['event_id'],)).fetchone()
        if conflict:
            log.append(dict(issue='EVENT_PAYLOAD_CONFLICT', key=event['event_id'], source_row_ids=event['sources'],
                            hit_rows=event['hit_rows'], extra_rows=0, action='BLOCK_ALL_AFFECTED_ORDERS',
                            scope='all orders mentioned by the conflicting raw event'))
        elif event['hit_rows'] > 1:
            log.append(dict(issue='REPLAY_CONFIRMED', key=event['event_id'], source_row_ids=event['sources'],
                            hit_rows=event['hit_rows'], extra_rows=event['hit_rows']-1,
                            action='KEEP_'+event['representative']+'_FOLD_REPLAYS',
                            scope='same event identity and identical full payload only'))
    for receipt in rows(db, 'SELECT * FROM orphan_receipts ORDER BY source_row_id'):
        log.append(dict(issue='ORPHAN_RECEIPT', key=receipt['line_id'], source_row_ids=receipt['source_row_id'],
                        hit_rows=1, extra_rows=0, action='PENDING_LINK_BLOCK_FORMAL_SCOPE',
                        scope='TEE-M / 2026-10-21 full KPI pending reconciliation'))
    for conflict in rows(db, '''SELECT line_id, GROUP_CONCAT(source_row_id,'|') AS sources,
                              COUNT(*) AS hit_rows FROM canonical_lines
                              WHERE line_id IN (SELECT line_id FROM line_key_conflicts)
                              GROUP BY line_id'''):
        log.append(dict(issue='LINE_KEY_CONFLICT', key=conflict['line_id'], source_row_ids=conflict['sources'],
                        hit_rows=conflict['hit_rows'], extra_rows=0, action='BLOCK_ALL_AFFECTED_ORDERS',
                        scope='all orders mentioned by the conflicting business line key'))
    for line in rows(db, 'SELECT * FROM canonical_lines ORDER BY source_row_id'):
        for issue, hit in [('NEGATIVE_ORDER_QTY', line['ordered_qty'] is not None and line['ordered_qty'] < 0),
                           ('MISSING_PROMISE', line['promise_at'] is None)]:
            if hit:
                log.append(dict(issue=issue, key=line['order_id'], source_row_ids=line['source_row_id'],
                                hit_rows=1, extra_rows=0, action='BLOCK_WHOLE_ORDER',
                                scope=line['order_id']+' and full KPI'))
    for item in inventory:
        if item['state'] in ('MISSING_ROW', 'NULL_VALUE', 'ZERO_OBSERVED'):
            action = {'MISSING_ROW':'PENDING_KEEP_EXPECTED_SLOT',
                      'NULL_VALUE':'PENDING_EXCLUDE_FROM_OBSERVED_RATE',
                      'ZERO_OBSERVED':'KEEP_VALID_OBSERVATION'}[item['state']]
            log.append(dict(issue=item['state'], key='|'.join([item['snapshot_date'],item['store_id'],item['sku']]),
                            source_row_ids=item['source_row_id'] or '', hit_rows=0 if item['state']=='MISSING_ROW' else 1,
                            extra_rows=0, action=action, scope='snapshot slot; full-slice point estimate unavailable'))
    return inventory, fashion, log


def write_csv(path, records):
    with path.open('x', newline='', encoding='utf-8') as target:
        writer = csv.DictWriter(target, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='new directory only; an existing path is refused')
    args = parser.parse_args()
    before = source_hashes()
    db = connect()
    report = build_report(db)
    checks = check_boundaries(db, report)
    expected = json.loads((ROOT / 'expected' / 'report.json').read_text(encoding='utf-8'))
    assert report == expected, 'actual report differs from expected/report.json'
    checks.append('actual_report_equals_expected_snapshot')
    assert source_hashes() == before, 'source CSV or manifest was changed'
    checks.append('source_csv_and_manifest_hashes_unchanged')
    inventory, fashion, log = audits(db)
    # Never overwrite input, expected results, or an existing output directory.
    if args.output is None:
        output = Path(tempfile.mkdtemp(prefix='d5-results-', dir=Path.cwd()))
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (output / 'checks.json').write_text(json.dumps({'passed': checks, 'source_sha256': before}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    write_csv(output / 'inventory-audit.csv', inventory)
    write_csv(output / 'fashion-line-audit.csv', fashion)
    write_csv(output / 'issue-log.csv', log)
    write_csv(output / 'diagnostic-lines.csv', rows(db, 'SELECT * FROM diagnostic_line_result ORDER BY line_id'))
    db.close()
    print(f'PASS {len(checks)} checks; output: {output}')
    print('Fashion: original 280/400=70%; diagnostic 180/200=90%, full KPI BLOCKED.')
    print('Hewei: observed zero 2/15; valid coverage 15/32; 17 unknown slots.')


if __name__ == '__main__':
    main()
