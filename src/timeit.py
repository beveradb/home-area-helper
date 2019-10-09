import datetime
import sys
import time

methods_cumulative = {}
time_trace_logfile = 'timings.log'


def clear_logfile():
    open(time_trace_logfile, 'w').close()


def timeit(method):
    global methods_cumulative

    def timed(*args, **kw):
        # Comment out this line to record timings into the log file
        # return method(*args, **kw)

        global methods_cumulative

        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        milliseconds = (te - ts) * 1000

        caller = sys._getframe().f_back.f_code.co_name
        name_with_caller = '%s -> %s' % (caller, method.__name__)

        if name_with_caller not in methods_cumulative:
            methods_cumulative[name_with_caller] = {
                'calls': 0,
                'time': 0
            }

        methods_cumulative[name_with_caller]['calls'] += 1
        methods_cumulative[name_with_caller]['time'] += milliseconds

        return result

    return timed


def log_cumulatives():
    for key in sorted(methods_cumulative.keys()):
        if methods_cumulative[key]['time'] > 200:
            print('[%s] SLOW: %s - calls: %1.0f - time: %1.0f ms' % (
                datetime.datetime.utcnow().strftime("%d/%b/%Y %H:%I:%S"),
                key,
                methods_cumulative[key]['calls'],
                methods_cumulative[key]['time']
            ))
