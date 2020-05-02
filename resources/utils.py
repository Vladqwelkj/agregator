import threading
import datetime
from dateutil import tz


def in_new_thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs, daemon=True)
        my_thread.start()
    return wrapper


@in_new_thread
def write_log(*args):
    """Обший лог"""
    input_data = ' '.join([str(v) for v in args])
    print(input_data)
    with open('common_log.log', 'a') as f:
        f.write(datetime.datetime.strftime(
            datetime.datetime.now().astimezone(tz.gettz('Europe/Moscow')),
            '[%d/%m/%Y %H:%M:%S] ') 
            + input_data + '\n') #Текущая дата/время + текст