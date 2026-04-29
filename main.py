import multiprocessing
import logging
import time
import sys
import os

# 必须在最开始设置，尤其是在 Windows 上
if sys.platform == 'win32':
    # 确保子进程能正确初始化
    multiprocessing.freeze_support()

from src.utils import setup_logging
from src.bot import AutoRocoBot
from src.web.log_handler import setup_web_logging
from src.web.server import run_server
from config import CONFIG

def bot_process_loop(status_dict):
    """ 机器人的独立进程函数 """
    # 在子进程中重新设置日志，使其输出到共享队列
    setup_logging()
    setup_web_logging()
    
    logging.info("Bot worker process started (Independent GIL).")
    
    bot = AutoRocoBot()
    last_run_time = 0
    
    while True:
        # 即使在子进程，也保持短休眠
        time.sleep(0.1)
        
        # 从共享字典读取运行状态
        is_running = status_dict.get("is_running", False)
        running_mode = status_dict.get("running_mode", "smart")
        
        if not is_running:
            continue
            
        current_time = time.time()
        if current_time - last_run_time < CONFIG.poll_interval_sec:
            continue
            
        try:
            # 同步模式
            if bot.state.selected_mode != running_mode:
                logging.info(f"Bot Process: Switching Mode to {running_mode}")
                bot.set_mode(running_mode)
            
            # 执行步骤
            bot.step()
            last_run_time = time.time()
        except Exception as e:
            logging.exception(f"Error in bot process: {e}")
            time.sleep(1.0)

def main() -> None:
    """ 程序主入口 (管理进程) """
    # 1. 启动主进程日志
    setup_logging()
    setup_web_logging()

    logging.info("Launching RocoBot with Multiprocessing architecture...")

    # 2. 创建进程间共享数据
    manager = multiprocessing.Manager()
    status_dict = manager.dict()
    status_dict["is_running"] = False
    status_dict["running_mode"] = CONFIG.running_mode

    # 3. 启动机器人子进程
    # 注意：在 Windows 上，必须在 if __name__ == "__main__" 下启动
    bot_p = multiprocessing.Process(target=bot_process_loop, args=(status_dict,), daemon=True)
    bot_p.start()
    
    logging.info(f"Bot process PID: {bot_p.pid}")
    logging.info(f"Starting Web Server on port {CONFIG.web_port}...")

    # 4. 在主进程运行 Web 服务器
    try:
        run_server(status_dict=status_dict)
    except KeyboardInterrupt:
        logging.info("Main: Shutdown requested.")
    finally:
        bot_p.terminate()
        logging.info("Processes terminated. Cleanup complete.")

if __name__ == "__main__":
    main()
