#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
from datetime import datetime
import gzip
import json
import logging
from pathlib import Path
import re
from statistics import median
import sys
from typing import Dict, Tuple, Union

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

CONFIG = {
    'REPORT_SIZE': 1000,
    'REPORT_DIR': './reports',
    'LOG_DIR': './log',
    'REP_NAME': 'report-{}.html',
    'ERROR_PERC': 80,
    'MONITOR_PATH': './monitoring'
}


def read_config(in_config: Dict[str, Union[int, str]], path: str) -> Dict[str, Union[int, str]]:
    '''
        read config from file
    '''
    try:
        with open(path, 'r') as config_file:
            cfg = json.load(config_file)
            in_config.update(cfg)
            return in_config
    except IOError as e:
        return in_config
        logging.exception('I/O error({0}): {1}. The default config is used '.format(e.errno, e.strerror))
    except Exception as e:
        logging.exception('Cannot read CONFIG file.')


def parse_log(path: str, config: Dict[str, Union[int, str]]) -> Tuple[Dict[str, Union[float, Tuple[float], int]]]:
    '''
        read log file or gz
        main parcer log
    '''

    f = Path(path).exists()

    try:
        if Path(path).suffix =='.gz':
            file_log = gzip.open(path, 'rb')
        else:
            file_log = open(path, 'r')
    except:
        logging.exception('Error open log flie for read')

    line_count = 0
    error_count = 0
    res = {}
    time_all = 0

    for line_count, line in enumerate(file_log, start=1):
        try:
            link = re.findall('\B(?:/(?:[\w?=_&-]+))+', str(line))
            # if not url - go next
            if not link:
                continue

            link = link[0]
            line = str(line)

            timeout = re.findall(' \d+\.\d+', line)[0]

            time_all += float(timeout)

            if res.get(link):
                res[link]['time_sum'] += float(timeout)
                res[link]['count'] += 1

                if res[link]['time_max'] < float(timeout):
                    res[link]['time_max'] = float(timeout)

                res[link]['list'].append(float(timeout))
            else:
                res[link] = {
                    'url': link,
                    'time_sum': float(timeout),
                    'time_max': float(timeout),
                    'list': [float(timeout)],
                    'count': 1
                }
        except Exception as e:
            error_count += 1
            logging.exception("Error parsing line: " + str(line))
            err_perc = error_count * 100 / line_count
            if err_perc >= config['ERROR_PERC']:
                logging.error('The percentage of errors is greater {}'.format(config['ERROR_PERC']))
                file_log.close()
                raise e
        if line_count == 10:
            break

    file_log.close()

    # build result

    # count - сколько раз встречается URL, абсолютное значение
    # count_perc - сколько раз встречается URL, в процентнах относительно общего числа запросов
    # time_sum - суммарный $request_time для данного URL'а, абсолютное значение
    # time_perc - суммарный $request_time для данного URL'а, в процентах относительно общего $request_time всех запросов
    # time_avg - средний $request_time для данного URL'а
    # time_max - максимальный $request_time для данного URL'а
    # time_med - медиана $request_time для данного URL'а

    result = [
        {
            'url': item['url'],
            'time_sum': round(float(item['time_sum']), 8),
            'time_max': round(float(item['time_max']), 8),
            'count': item['count'],
            'count_perc': round(float(item['count']) * 100 / line_count, 8),
            'time_perc': round(float(item['time_sum']) * 100 / time_all, 8),
            'time_avg': round(float(item['time_sum']) / float(item['count']), 8),
            'time_med': round(median(item['list']))
        }
        for item in res.values()
    ]

    return result


def create_report(config: Dict[str, Union[int, str]], result_parsing: Tuple[Dict[str, Union[float, Tuple[float], int]]]):
    size = config['REPORT_SIZE']
    result_parsing.sort(key=lambda x: x['time_sum'], reverse=True)
    # result_parsing.sort(key=operator.itemgetter('time_sum'))
    j = json.dumps(result_parsing[:size])

    path = Path(config['REPORT_DIR']).joinpath(config['REP_NAME'])

    if Path(config['REPORT_DIR']).exists():
        try:
            with open('./report.html', 'r') as tmpl:
                try:
                    with open(path, 'w') as report:
                        for line in tmpl:
                            report.write(line.replace('$table_json', j))
                except Exception as e:
                    logging.exception('Error write report')
                    raise e
        except Exception as e:
            logging.exception('Error read report tmpl')
            raise e


def get_last_log(config: Dict[str, Union[int, str]]) -> str:
    log_files = {}

    if Path(config['LOG_DIR']).is_dir():
        for files in Path(config['LOG_DIR']).iterdir():
            f = str(files.name)
            result = re.search('^nginx-access-ui.log-[0-9]{8}', f)
            if result:
                date_str = re.search('[0-9]{8}', f).group(0)
                datetime_object = datetime.strptime(date_str, '%Y%m%d')
                log_files[datetime_object] = f
    else:
        logging.error('Error open log dir: {}'.format(config['LOG_DIR']))

    if log_files:
        max_date_in_files = max(dt for dt in log_files.keys())
        config['REP_NAME'] = config['REP_NAME'].format(max_date_in_files.strftime('%Y.%m.%d'))
        return log_files[max_date_in_files]
    else:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='set config file', type=str, metavar='config file')
    args = parser.parse_args()

    cfg = dict(CONFIG.items())

    if args.config:
        cfg = read_config(cfg, args.config)
        if cfg is None or cfg == []:
            logging.error('Config is empty')
            sys.exit(0)

    log_path = Path(cfg['MONITOR_PATH'])
    log_path.mkdir(exist_ok=True, parents=True)
    log_path = log_path / 'log_analyzer.log'
    logging.basicConfig(filename=log_path, format='[%(asctime)s] %(levelname).1s %(message)s', level=logging.INFO)

    logging.info("Start Analyzer")

    # get last log
    try:
        last_log = get_last_log(cfg)
    except:
        logging.exception('Error get last log file')
        sys.exit(0)

    if last_log is None:
        logging.exception('Error get last log file')
        sys.exit(0)

    if Path(cfg['REPORT_DIR']).joinpath(cfg['REP_NAME']).exists():
        logging.info("Nothing!")
        sys.exit(0)

    # read last and analyze log
    path_log = Path(cfg['LOG_DIR']).joinpath(last_log)

    r = parse_log(path_log, cfg)

    # create report
    create_report(cfg, r)

    logging.info("Done!")


if __name__ == "__main__":
    main()
