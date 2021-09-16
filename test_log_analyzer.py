import unittest
import log_analyzer

class Test_Alanyzer(unittest.TestCase):
    def test_get_last_log(self):
        pass

    def test_median(self):
        self.assertEqual(log_analyzer.median([1, 2, 3, 4, 5]), 3)
        self.assertEqual(log_analyzer.median([1, 2, 4, 5]), 3)
        self.assertEqual(log_analyzer.median([2]), 2)

    def test_read_config(self):
        config = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
            'REP_NAME': 'report-{}.html',
            'ERROR_PERC': 81,
            'MON_PATH': './mon'
        }

        test = {}

        self.assertEqual(log_analyzer.read_config(test, './config.cfg'), config)

    def test_parse_log(self):
        test_line = ['''1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "" "-" "" "dc7161be3" 0.393
                     1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019353 HTTP/1.1" 200 927 "-" "" "-" "" "dc7161be3" 0.392
                     1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019352 HTTP/1.1" 200 927 "-" "" "-" "" "dc7161be3" 0.390
                     ''']

        config = {'ERROR_PERC':80}

        result = [{'url': '/api/v2/banner/25019354', 'time_sum': 0.393, 'time_max': 0.393, 'count': 1, 'count_perc': 100.0, 'time_perc': 100.0, 'time_avg': 0.393, 'time_med': 0}]

        self.assertEqual(log_analyzer.parse_log(test_line, config), result)

if __name__ == "__main__":
    unittest.main()