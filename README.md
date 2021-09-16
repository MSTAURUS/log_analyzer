#Log Analyzer


Запуск:
---------------

* конфигурация по умолчанию

    :code:`python log_analyzer.py`

* внешняя конфигурация

    :code:`python log_analyzer.py --config config.cfg`

Конфигурация:
-------------------------

.. code:: Python

{
    "REPORT_SIZE": 1000,            #Количество записей в отчёте
    "REPORT_DIR": "./reports",      #Каталог для сохранения отчётов
    "LOG_DIR": "./log",             #Каталог для поиска логов
    'REP_NAME': 'report-{}.html',   #шаблон отчёта
    'ERROR_PERC': 80,               #сколько процентов ошибко обработки разрешено
    'MON_PATH': './mon'             #каталог для логов анализатора
}


Тестирование:
------------

    :code:`python test_log_analyzer.py -v`
