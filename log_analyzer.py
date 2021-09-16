#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import logging
import argparse
import os
import re
from datetime import datetime
import gzip
import json
import operator

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    'REP_NAME': 'report-{}.html',
    'ERROR_PERC': 80,
    'MON_PATH': './mon'
}


def median(list):
    # calc median
    i = len(list)
    index = i // 2
    if i % 2:
        return sorted(list)[index]
    else:
        return sum(sorted(list)[index - 1:index + 1]) / 2


def read_config(config, path):
    # read config from file
    try:
        with open(path, 'r') as config_file:
            cfg = json.load(config_file)
            config.update(cfg)
            return config
    except:
        logging.exception('Cannot read CONFIG file.')


def readlog(path):
    # read log file or gz
    try:
        if path.endswith('.gz'):
            log = gzip.open(path, 'rb')
        else:
            log = open(path, 'r')

        return log
    except:
        logging.exception('Error open log flie for read')


def parse_log(file_log, config):
    #  main parcer
    line_count = 0
    error_count = 0
    res = {}
    time_all = 0
    for line in file_log:
        line_count += 1
        try:
            link = re.findall('\B(?:/(?:[\w?=_&-]+))+', str(line))
            # if not url - go next
            if link:
                timeout = re.findall(' \d+\.\d+', str(line))[0]

                time_all += float(timeout)

                if res.get(link[0]):
                    res[link[0]]['time_sum'] += float(timeout)
                    res[link[0]]['count'] += 1

                    if res[link[0]]['time_max'] < float(timeout):
                        res[link[0]]['time_max'] = float(timeout)

                    res[link[0]]['list'].append(float(timeout))
                else:
                    res[link[0]] = {
                        'url': link[0],
                        'time_sum': float(timeout),
                        'time_max': float(timeout),
                        'list': [float(timeout)],
                        'count': 1
                    }
        except:
            error_count += 1
            logging.exception("Error parsing line: " + str(line))
            err_perc = error_count * 100 / line_count
            if err_perc >= config['ERROR_PERC']:
                logging.error('The percentage of errors is greater {}'.format(config['ERROR_PERC']))
                sys.exit()

        # if line_count == 10:
        #     break

    # build result
    result = []
    for key in res.keys():
        step = {
            'url': res[key]['url'],
            'time_sum': round(float(res[key]['time_sum']), 8),
            'time_max': round(float(res[key]['time_max']), 8),
            'count': res[key]['count'],
            'count_perc': round(float(res[key]['count']) * 100 / line_count, 8),
            'time_perc': round(float(res[key]['time_sum']) * 100 / time_all, 8),
            'time_avg': round(float(res[key]['time_sum']) / float(res[key]['count']), 8),
            'time_med': round(median(res[key]['list']))}
        result.append(step)

    return result


# + count - сколько раз встречается URL, абсолютное значение
# + count_perc - сколько раз встречается URL, в процентнах относительно общего числа запросов
# + time_sum - суммарный $request_time для данного URL'а, абсолютное значение
# + time_perc - суммарный $request_time для данного URL'а, в процентах относительно общего $request_time всех запросов
# + time_avg - средний $request_time для данного URL'а
# + time_max - максимальный $request_time для данного URL'а
# time_med - медиана $request_time для данного URL'а

def create_report(config, result_parsing):
    size = config['REPORT_SIZE']
    result_parsing.sort(key=lambda x: x['time_sum'], reverse=True)
    # result_parsing.sort(key=operator.itemgetter('time_sum'))
    j = json.dumps(result_parsing[:size])

    path = os.path.join(config['REPORT_DIR'], config['REP_NAME'])
    try:
        with open('./report.html', "rt") as tmpl:
            try:
                with open(path, "wt") as report:
                    for line in tmpl:
                        report.write(line.replace('$table_json', j))
            except:
                logging.exception('Error write report')
    except:
        logging.exception('Error read report tmpl')


def get_last_log(config):
    try:
        log_files = {}
        if os.path.isdir(config['LOG_DIR']):
            for files in os.listdir(config['LOG_DIR']):
                result = re.search('^nginx-access-ui.log-[0-9]{8}', files)
                if result:
                    date_str = re.search('[0-9]{8}', files).group(0)
                    datetime_object = datetime.strptime(date_str, '%Y%m%d')
                    log_files[datetime_object] = files
        else:
            logging.error('Error open log dir: {}'.format(config['LOG_DIR']))

        if log_files:
            max_date_in_files = max(dt for dt in log_files.keys())
            config['REP_NAME'] = config['REP_NAME'].format(max_date_in_files.strftime('%Y.%m.%d'))
            return log_files[max_date_in_files]
        else:
            return None
    except:
        logging.exception('Error get last log file')


# def update_config(config, path):
#     if not os.path.exists(path):
#         logging.error('New file config not exists')
#         sys.exit(0)

def main():
    log_path = os.path.join(config['MON_PATH'], 'log_analyzer.log')
    logging.basicConfig(filename=log_path, format='[%(asctime)s] %(levelname).1s %(message)s', level=logging.INFO)

    logging.info("Start Analyzer")

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='set config file', type=str, metavar='config file')
    args = parser.parse_args()

    if args.config:
        read_config(config, args.config)

    # get last log
    last_log = get_last_log(config)
    if os.path.exists(os.path.join(config['REPORT_DIR'], config['REP_NAME'])):
        logging.info("Nothing!")
        sys.exit(0)

    # read last log
    log = readlog(os.path.join(config['LOG_DIR'], last_log))

    # analyze log
    r = parse_log(log, config)

    # create report
    create_report(config, r)

    logging.info("Done!")


if __name__ == "__main__":
    main()