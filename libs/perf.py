import logging
from datetime import datetime, timedelta
from functools import wraps

log: logging.Logger = logging.getLogger("timer")


def print_elapsed_time(func):
    """
    함수 실행 시간을 로그로 출력하는 데코레이터
    :param func:  함수
    :return:      함수 실행 시간을 로그로 출력
    """

    @wraps(func)
    def wrapper(**kwargs):
        start = datetime.now()
        log.info(f"start: {start}")

        # 함수 실행
        result = func(**kwargs)

        # 현재 Epoch time 얻기
        end = datetime.now()
        log.info(f"end: {end}")

        elapsed_time: timedelta = (end - start)
        formatted_elapsed_time = "{:.3f}".format(elapsed_time.total_seconds())
        log.info(
            f"Elapsed time for function: {formatted_elapsed_time} s")

        return result

    return wrapper
