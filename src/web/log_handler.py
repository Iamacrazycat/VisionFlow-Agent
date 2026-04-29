import logging
import multiprocessing

# 使用 multiprocessing.Queue 确保跨进程日志传输
log_queue = multiprocessing.Queue()

class WebLogHandler(logging.Handler):
    """ 自定义日志处理器，将日志推送到 multiprocessing.Queue """
    
    def emit(self, record):
        try:
            msg = self.format(record)
            # 使用 non-blocking put 防止队列满时阻塞主流程
            log_queue.put_nowait(msg)
        except:
            pass

def setup_web_logging():
    """ 为全局日志添加 WebLogHandler """
    handler = WebLogHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
    logging.getLogger().addHandler(handler)
