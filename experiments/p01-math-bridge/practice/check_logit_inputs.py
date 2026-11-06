"""Show why finite logit rejects endpoints and invalid probabilities."""
from run import logit

for value in (0, 1, 1.2):
    try:
        logit(value)
    except ValueError as exc:
        print(f"拒绝 p={value}: {exc}")
    else:
        raise AssertionError(f"invalid input accepted: {value}")
