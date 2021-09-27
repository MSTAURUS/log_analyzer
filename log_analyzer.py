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
from typing import Dict, Tuple, Union, List

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "REP_NAME": "report-{}.html",
    "ERROR_PERC": 80,
    "MONITOR_PATH": "./monitoring",
}


def read_config(path: str, default_config: Dict[str, Union[int, str]]) -> Dict[str, Union[int, str]]:
    """
    read config from file
    """
    try:
        with open(path, "r") as config_file:
            cfg = json.load(config_file)
            default_config.update(cfg)
            return default_config
    except IOError as e:
        logging.exception("I/O error({0}): {1}. The default config is used ".format(e.errno, e.strerror))
        return default_config
    except Exception as e:
        logging.exception("Cannot read CONFIG file.")
        raise ValueError("Cannot read CONFIG file.")


def parse_log(path: str, config: Dict[str, Union[int, str]]) -> List[Dict[str, Union[float, Tuple[float], int]]]:
    """
    read log file or gz
    main parcer log
    """

    path = Path(path)

    if not path.exists():
        raise ValueError("Dir log is not exists")

    try:
        if path.suffix == ".gz":
            file_log = gzip.open(path, "rb")
        else:
            file_log = open(path, "r")
    except:
        logging.exception("Error open log flie for read")

    line_count = 0
    error_count = 0
    res = {}
    time_all = 0

    for line_count, line in enumerate(file_log, start=1):
        try:
            link = re.findall("\B(?:/(?:[\w?=_&-]+))+", str(line))
            # if not url - go next
            if not link:
                continue

            link = link[0]
            line = str(line)

            timeout = re.findall(" \d+\.\d+", line)[0]

            time_all += float(timeout)

            if res.get(link):
                res[link]["time_sum"] += float(timeout)
                res[link]["count"] += 1

                if res[link]["time_max"] < float(timeout):
                    res[link]["time_max"] = float(timeout)

                res[link]["list"].append(float(timeout))
            else:
                res[link] = {
                    "url": link,
                    "time_sum": float(timeout),
                    "time_max": float(timeout),
                    "list": [float(timeout)],
                    "count": 1,
                }
        except Exception as e:
            error_count += 1
            logging.exception("Error parsing line: " + str(line))
            err_perc = error_count * 100 / line_count
            if err_perc >= config["ERROR_PERC"]:
                logging.error("The percentage of errors is greater {}".format(config["ERROR_PERC"]))
                file_log.close()
                raise e

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
            "url": item["url"],
            "time_sum": round(float(item["time_sum"]), 8),
            "time_max": round(float(item["time_max"]), 8),
            "count": item["count"],
            "count_perc": round(float(item["count"]) * 100 / line_count, 8),
            "time_perc": round(float(item["time_sum"]) * 100 / time_all, 8),
            "time_avg": round(float(item["time_sum"]) / float(item["count"]), 8),
            "time_med": round(median(item["list"])),
        }
        for item in res.values()
    ]

    return result


def create_report(config: Dict[str, Union[int, str]], result_parsing: List[Dict[str, Union[float, Tuple[float], int]]]):
    size = config["REPORT_SIZE"]
    result_parsing.sort(key=lambda x: x["time_sum"], reverse=True)
    # result_parsing.sort(key=operator.itemgetter('time_sum'))
    j = json.dumps(result_parsing[:size])

    tmpl_report_path = Path(config["REPORT_DIR"])
    if not tmpl_report_path.exists():
        tmpl_report_path.mkdir(exist_ok=True, parents=True)

    path = tmpl_report_path / config["REP_NAME"]

    try:
        with open("./tmpl_report.html", "r") as tmpl:
            try:
                with open(path, "w") as report:
                    for line in tmpl:
                        report.write(line.replace("$table_json", j))
            except Exception as e:
                logging.exception("Error write report")
                raise e
    except Exception as e:
        logging.exception("Error read report tmpl")
        raise e


def get_last_log(config: Dict[str, Union[int, str]]) -> str:
    log_file_datetime_mapping = {}
    log_dir = Path(config["LOG_DIR"])

    if log_dir.is_dir():
        for file in log_dir.iterdir():
            file_name = str(file.name)
            result = re.search("^nginx-access-ui.log-[0-9]{8}", file_name)
            if result:
                date_str = re.search("[0-9]{8}", file_name).group(0)
                datetime_object = datetime.strptime(date_str, "%Y%m%d")
                log_file_datetime_mapping[datetime_object] = file_name
    else:
        logging.error("Error open log dir: {}".format(config["LOG_DIR"]))

    if log_file_datetime_mapping:
        max_date_in_files = max(date_time for date_time in log_file_datetime_mapping)
        config["REP_NAME"] = config["REP_NAME"].format(
            max_date_in_files.strftime("%Y.%m.%d")
        )
        return log_file_datetime_mapping[max_date_in_files]
    else:
        return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="set config file", type=str, metavar="config file")
    args = parser.parse_args()

    default_config = dict(CONFIG.items())

    if args.config:
        cfg = read_config(args.config, default_config)
        if not cfg:
            logging.error("Config is empty")
            sys.exit(0)

    log_path = Path(default_config["MONITOR_PATH"])
    log_path.mkdir(exist_ok=True, parents=True)
    log_path = log_path / "log_analyzer.log"
    logging.basicConfig(
        filename=log_path,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        level=logging.INFO,
    )

    logging.info("Start Analyzer")

    # get last log
    try:
        last_log = get_last_log(default_config)
    except:
        logging.exception("Error get last log file")
        sys.exit(0)

    if not last_log:
        logging.exception("Error get last log file")
        sys.exit(0)

    if Path(default_config["REPORT_DIR"]).joinpath(default_config["REP_NAME"]).exists():
        logging.info("Nothing!")
        sys.exit(0)

    # read last and analyze log
    path_log = Path(default_config["LOG_DIR"]).joinpath(last_log)

    r = parse_log(path_log, default_config)

    # create report
    create_report(default_config, r)

    logging.info("Done!")


if __name__ == "__main__":
    main()
