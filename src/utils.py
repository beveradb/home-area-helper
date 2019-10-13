import logging
import sys
import time

import requests_cache

methods_timings_cumulative = {}

cached_requests = requests_cache.core.CachedSession(
    cache_name='api_cache',
    backend="sqlite",
    allowable_methods=('GET', 'POST')
)


def timeit(method):
    global methods_timings_cumulative

    def timed(*args, **kw):
        # Comment out this line to record timings into the log file
        # return method(*args, **kw)

        global methods_timings_cumulative

        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        milliseconds = (te - ts) * 1000

        caller = sys._getframe().f_back.f_code.co_name
        name_with_caller = '%s -> %s' % (caller, method.__name__)

        if name_with_caller not in methods_timings_cumulative:
            methods_timings_cumulative[name_with_caller] = {
                'calls': 0,
                'time': 0
            }

        methods_timings_cumulative[name_with_caller]['calls'] += 1
        methods_timings_cumulative[name_with_caller]['time'] += milliseconds

        return result

    return timed


def log_method_timings():
    global methods_timings_cumulative
    for key in sorted(methods_timings_cumulative.keys()):
        if methods_timings_cumulative[key]['time'] > 200:
            logging.warning('SLOW: %s - calls: %1.0f - time: %1.0f ms' % (
                key,
                methods_timings_cumulative[key]['calls'],
                methods_timings_cumulative[key]['time']
            ))

    # Clear the cumulative counter now we've completed a request and logged the results
    methods_timings_cumulative = {}
