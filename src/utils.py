import logging
import os
import sys
import time
import zipfile

methods_timings_cumulative = {}


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

        # noinspection PyProtectedMember
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


def download_file(url, target_dir, local_filename):
    command = "mkdir -p " + target_dir
    logging.debug("Executing command: " + command)
    logging.debug("Execution response: " + str(os.system(command)))

    command = "curl -s -L -o " + local_filename + " " + url
    logging.debug("Executing command: " + command)
    logging.debug("Execution response: " + str(os.system(command)))


def preload_files(url_root, files_to_check):
    for single_check in files_to_check:
        fetch_filepath = single_check['dir'] + single_check['file']
        fetch_url = url_root + single_check['file']

        if not os.path.isfile(fetch_filepath):
            logging.info("Preload file not found: " + fetch_filepath + " - downloading from: " + fetch_url)
            download_file(fetch_url, single_check['dir'], fetch_filepath)

            if not os.path.isfile(fetch_filepath):
                raise Exception("Preload file download failed")

            if fetch_filepath.endswith('.zip'):
                logging.info("Preload file ends with .zip, unzipping")
                with zipfile.ZipFile(fetch_filepath, "r") as zip_ref:
                    zip_ref.extractall(single_check['dir'])
        else:
            logging.info("Preload file already exists: " + fetch_filepath)
