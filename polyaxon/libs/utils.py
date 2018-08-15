from distutils.util import strtobool  # pylint:disable=import-error

from schemas.utils import to_list


def to_bool(value, handle_none=False, exception=TypeError):
    if isinstance(value, str):
        value = strtobool(value)

    if value in (False, 0):
        return False

    if value in (True, 1):
        return True

    if handle_none and value is None:
        return False

    raise exception('The value `{}` cannot be interpreted as boolean'.format(value))


def get_list(values):
    return to_list(values) if values is not None else []


def to_unit_memory(number):
    """Creates a string representation of memory size given `number`."""
    kb = 1024

    number /= kb

    if number < 100:
        return '{} Kb'.format(round(number, 2))

    number /= kb
    if number < 300:
        return '{} Mb'.format(round(number, 2))

    number /= kb

    return '{} Gb'.format(round(number, 2))
