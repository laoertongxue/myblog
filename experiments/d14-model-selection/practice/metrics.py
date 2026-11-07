"""Forecast errors are actual minus prediction. WAPE is a ratio, not percent."""
import math


def evaluate(actual, prediction):
    """Use finite binary64 aggregates; reject overflow and nonzero-to-zero underflow.

    Inputs and results retain ordinary floating-point rounding. In particular,
    this is not arbitrary-precision arithmetic. Aggregate sums must be finite,
    even if a mean alone could otherwise be representable.
    """
    actual, prediction = list(actual), list(prediction)
    if not actual or len(actual) != len(prediction):
        raise ValueError('nonempty, equally sized aligned inputs required')
    try:
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in actual + prediction):
            raise ValueError('finite numeric inputs required')
        if any(v < 0 for v in actual):
            raise ValueError('actual demand must be nonnegative')
        errors = [a - p for a, p in zip(actual, prediction)]
        if not all(math.isfinite(e) for e in errors):
            raise ValueError('error exceeds finite numeric range')
        n = len(errors)
        scale = max(abs(e) for e in errors)
        error_sum = math.fsum(errors)
        absolute_error_sum = math.fsum(abs(e) for e in errors)
        result = {'n': n, 'actual_sum': math.fsum(actual),
                  'absolute_error_sum': absolute_error_sum,
                  # Sum before dividing: dividing subnormal errors first loses them.
                  'me': error_sum / n,
                  'mae': absolute_error_sum / n,
                  'rmse': scale * math.sqrt(math.fsum((e / scale) ** 2 for e in errors) / n) if scale else 0.0}
        result['wape'] = (result['absolute_error_sum'] / result['actual_sum']
                          if result['actual_sum'] else None)
        result['wape_status'] = 'defined' if result['actual_sum'] else 'undefined_zero_actual_sum'
        if not all(v is None or not isinstance(v, (float, int)) or math.isfinite(v) for v in result.values()):
            raise ValueError('metric exceeds finite numeric range')
        if ((error_sum != 0 and result['me'] == 0)
                or (absolute_error_sum != 0 and (result['mae'] == 0 or result['rmse'] == 0
                    or result['wape'] == 0))):
            raise ValueError('nonzero metric underflows supported numeric range')
        return result
    except OverflowError as exc:
        raise ValueError('metric exceeds finite numeric range') from exc
