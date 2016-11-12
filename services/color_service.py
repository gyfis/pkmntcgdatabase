import colorsys
import itertools
from fractions import Fraction


def _zenos_dichotomy():
    for k in itertools.count():
        yield Fraction(1, 2**k)


def _getfracs():
    yield 0
    for k in _zenos_dichotomy():
        i = k.denominator
        for j in range(1, i, 2):
            yield Fraction(j, i)


def _genhsv(h):
    yield h, 0.9, 0.7
    yield h, 0.1, 0.9


def get_colors(number):
    gethsvs = lambda: itertools.chain.from_iterable(map(_genhsv, _getfracs()))

    return list(map(lambda x: '%02x%02x%02x' % tuple(map(lambda y: round(255 * y), colorsys.hsv_to_rgb(*x))), itertools.islice(gethsvs(), number)))
