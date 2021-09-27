#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pathlib
import unittest

import log_analyzer


class Test_Alanyzer(unittest.TestCase):
    def test_get_last_log(self):
        pass

    def test_read_config(self):
        config = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
            "REP_NAME": "report-{}.html",
            "ERROR_PERC": 81,
            "MONITOR_PATH": "./mon",
        }

        test = {}

        self.assertEqual(log_analyzer.read_config("./config.cfg", test), config)
        self.assertRaises(TypeError, log_analyzer.read_config, ("./test_log.log", test))

    def test_parse_log(self):
        test_log = pathlib.Path("./test_log.log")

        config = {"ERROR_PERC": 80}

        result = [
            {
                "url": "/api/v2/banner/25019354",
                "time_sum": 0.393,
                "time_max": 0.393,
                "count": 1,
                "count_perc": 33.33333333,
                "time_perc": 33.44680851,
                "time_avg": 0.393,
                "time_med": 0,
            },
            {
                "url": "/api/v2/banner/25019353",
                "time_sum": 0.392,
                "time_max": 0.392,
                "count": 1,
                "count_perc": 33.33333333,
                "time_perc": 33.36170213,
                "time_avg": 0.392,
                "time_med": 0,
            },
            {
                "url": "/api/v2/banner/25019352",
                "time_sum": 0.39,
                "time_max": 0.39,
                "count": 1,
                "count_perc": 33.33333333,
                "time_perc": 33.19148936,
                "time_avg": 0.39,
                "time_med": 0,
            },
        ]

        self.assertEqual(log_analyzer.parse_log(test_log, config), result)


if __name__ == "__main__":
    unittest.main()
