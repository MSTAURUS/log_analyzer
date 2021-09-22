# Log Analyzer


Запуск:
---------------

* конфигурация по умолчанию
~~~
    python log_analyzer.py
~~~
* внешняя конфигурация
~~~
    python log_analyzer.py --config config.cfg
~~~

Конфигурация:
-------------------------
~~~
{
    "REPORT_SIZE": 1000,            #Количество записей в отчёте
    "REPORT_DIR": "./reports",      #Каталог для сохранения отчётов
    "LOG_DIR": "./log",             #Каталог для поиска логов
    'REP_NAME': 'report-{}.html',   #шаблон отчёта
    'ERROR_PERC': 80,               #сколько процентов ошибко обработки разрешено
    'MON_PATH': './mon'             #каталог для логов анализатора
}
~~~

Тестирование:
------------
~~~
    python test_log_analyzer.py -v
~~~

### bookmark **Домашнее задание/проектная работа выполнено (-на) для курса "[Python Developer. Professional](https://otus.ru/lessons/python-professional/)"**
