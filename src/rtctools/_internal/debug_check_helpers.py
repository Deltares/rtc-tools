import logging
from enum import IntEnum

logger = logging.getLogger("rtctools")


class DebugLevel(IntEnum):
    NONE = 0
    LOW = 10
    MEDIUM = 20
    HIGH = 30
    VERYHIGH = 40


def debug_check(level):
    def noop(*args, **kwargs):
        pass

    def wrap(func):
        def func_wrapper(*args, **kwargs):
            this = args[0]
            filter_ = this._debug_check_level
            do_check = False
            if callable(filter_):
                if filter_(level, func.__qualname__):
                    do_check = True
            elif filter_ >= level:
                do_check = True

            if do_check:
                logger.info(f"Starting debug check '{func.__qualname__}'")
                extra_options = this._debug_check_options.get(func.__qualname__, {})
                ret = func(*args, **kwargs, **extra_options)
                logger.info(f"Finished debug check '{func.__qualname__}'")
                return ret
            else:
                return noop(*args, **kwargs)

        return func_wrapper

    return wrap
