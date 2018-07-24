import os
import sys
import asyncio
import logging
import argparse
import calendar
import select
import subprocess
import time
from datetime import datetime
from collections import deque
from glob import glob
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

VERSION = '0.1.0'


def config_logging(level):
    fmt = logging.Formatter(
        '[%(asctime)-10s][%(levelname)-4s:%(funcName)-10s] %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(level)
    logger.addHandler(ch)


class GatlingExporter(object):
    """Custom Prometheus collector class"""

    def __init__(self, simulation_log_path, log_buffer):
        self.log_buffer = log_buffer
        self.operations_summary = dict()
        self.aggregated_errors = dict()
        logger.debug(
            'init gatling exporter for simulation=%s',
            simulation_log_path)

    def collect(self):
        yield from self.collect_buffered_entries(self.log_buffer)

    def collect_buffered_entries(self, log_buffer):
        max_collect_count = log_buffer.maxlen

        try:
            # don't want to send more than the length of the buffer in one response
            while max_collect_count > 0:
                max_collect_count -= 1
                log_entry = log_buffer.popleft()
                # entry parts structure is as follows
                # index 0 - the type of metric - we're interested in REQUEST
                # index 1 - type of operation (eg. select, insert etc) as
                #           indicated by the scenario_id
                # index 2 - count of operation execution
                # index 4 - start timestamp
                # index 5 - end timestamp
                # index 6 - status of the request OK (it can also be KO for
                #           failures in which case we'll have index 7 to
                #           process)
                # index 7 - exception in case the request failed
                entry_parts = log_entry.split()
                if entry_parts[0] == 'REQUEST':
                    request_status = entry_parts[6]
                    operation_response_time = int(entry_parts[5]) - int(entry_parts[4])
                    sim_id = entry_parts[1]

                    logger.debug("exporting entry with status=%s and type=%s",
                                 request_status, sim_id)

                    success_count_key = (sim_id, 'Success')
                    if success_count_key not in self.operations_summary:
                        self.operations_summary[success_count_key] = 0

                    failure_count_key = (sim_id, 'Failure')
                    if failure_count_key not in self.operations_summary:
                        self.operations_summary[failure_count_key] = 0

                    labels = ['sim_id', 'status']
                    custom_metrics = []
                    if request_status == 'OK':
                        self.operations_summary[success_count_key] = self.operations_summary.get(success_count_key) + 1
                        metrics = [sim_id, 'Success']
                        c = GaugeMetricFamily('loadgenerator',
                                              'loadgenerator statements response time',
                                              labels=labels)
                        c.add_metric(metrics, operation_response_time)
                        yield c
                    else:
                        self.operations_summary[failure_count_key] = self.operations_summary.get(failure_count_key) + 1
                        error = ' '.join(x.strip() for x in entry_parts[8:])
                        self.aggregated_errors[(error, sim_id)] = self.aggregated_errors.get((error, sim_id), 0) + 1

                else:
                    continue

        except IndexError:
            logger.debug('drained log buffer. yield metrics')

        for key, value in self.aggregated_errors.items():
            labels = ['error', 'sim_id', 'status']
            c = GaugeMetricFamily('loadgenerator',
                                  'loadgenerator aggregated errors count',
                                  labels=labels)
            metrics = [key[0], key[1], 'Failure']
            c.add_metric(metrics, value)
            yield c

        summary_labels = ['sim_id', 'status']
        for key, value in self.operations_summary.items():
            c = GaugeMetricFamily('loadgenerator_summary', '', labels=summary_labels)
            c.add_metric([key[0], key[1]], value)
            yield c


class EnvDefault(argparse.Action):
    """Idea taken from https://stackoverflow.com/a/10551190/1143231"""

    def __init__(self,
                 envvar,
                 type=str,
                 required=True,
                 default=None,
                 **kwargs):

        if envvar in os.environ:
            default = type(os.environ[envvar])
        if default is not None:
            required = False
        super(EnvDefault, self).__init__(default=default,
                                         required=required,
                                         type=type,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


def parse_args():
    parser = argparse.ArgumentParser('Gatling Exporter for Prometheus')
    parser.add_argument('--port', '-p', type=int, action=EnvDefault,
                        envvar='GATLING_EXPORTER_PORT', default=9102)
    parser.add_argument('--simulation_log_path', '-s', type=str, action=EnvDefault,
                        envvar='GATLING_EXPORTER_SIMULATION_LOG_PATH', required=True)
    parser.add_argument('--buffer_len', type=int, default=30000)
    parser.add_argument('--log-level', '-l', type=int, action=EnvDefault,
                        envvar='GATLING_EXPORTER_LOG_LEVEL', default=logging.INFO)
    parser.add_argument('--version', '-v', action='version', version=VERSION)
    return parser.parse_args()


def main():
    """
    Prometheus Agent for monitoring gatling simulation logs.

    Usage:
      python gatling_exporter.py [ARGS]

    Arguments can be provided as command line arguments or as environment
    variables with ``GATLING_EXPORTER_`` prefix, e.g. for ``--port`` the
    environment variable equivalent would be ``GATLING_EXPORTER_PORT``.
    """
    args = parse_args()
    config_logging(args.log_level)
    logger.info(args)

    log_buffer = deque(maxlen=args.buffer_len)

    paths = glob(args.simulation_log_path)
    if len(paths) is not 1:
        raise SystemExit('Please specify only one path to a simulation. Got %s' % paths)
    expanded_sim_log_path = paths[0]

    REGISTRY.register(GatlingExporter(expanded_sim_log_path, log_buffer))
    start_http_server(args.port)

    f = subprocess.Popen(['tail', '-n0', '-f', expanded_sim_log_path],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        line = f.stdout.readline().decode('UTF-8').strip()
        log_buffer.append(line)


if __name__ == '__main__':
    main()
