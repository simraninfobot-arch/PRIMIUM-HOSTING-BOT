import asyncio
import logging
import time
import sys
import os
import subprocess

logger = logging.getLogger(__name__)


class BotRecovery:
    """Auto Recovery System - Monitors and restarts crashed projects"""

    def __init__(self):
        self.running = True
        self.restart_count = 0
        self.max_restarts = 100
        self.crash_log = []

    async def start_recovery_monitor(self, application):
        """Main recovery loop"""
        import main as _m
        while self.running and _m.recovery_enabled:
            try:
                await self.check_bot_health(application)
                await self.recover_projects()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Recovery error: {e}")
                self.crash_log.append({"time": time.time(), "error": str(e)})
                await asyncio.sleep(5)

    async def check_bot_health(self, application):
        """Check if bot is running correctly"""
        try:
            await application.bot.get_me()
        except Exception as e:
            logger.critical(f"Bot health check failed: {e}")
            await self.emergency_restart(application)

    async def recover_projects(self):
        """Auto-restart crashed projects"""
        import main as _m
        for p_name, proc in list(_m.running_processes.items()):
            if proc.poll() is not None:
                if _m.recovery_enabled and p_name in _m.project_owners:
                    logger.info(f"Recovering crashed project: {p_name}")
                    folder = _m.project_owners[p_name]["path"]
                    main_file = os.path.join(folder, "main.py")
                    if os.path.exists(main_file):
                        try:
                            _m.log_streamer.stop_stream(p_name)
                            new_proc = subprocess.Popen(
                                [sys.executable, "-u", main_file],
                                cwd=folder,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                bufsize=1
                            )
                            _m.running_processes[p_name] = new_proc
                            if _m.live_logs_enabled:
                                _m.log_streamer.start_stream(p_name, new_proc)
                            logger.info(f"Project {p_name} recovered")
                        except Exception as e:
                            logger.error(f"Failed to recover {p_name}: {e}")

    async def emergency_restart(self, application):
        """Emergency restart when bot crashes"""
        if self.restart_count < self.max_restarts:
            self.restart_count += 1
            logger.critical(f"Emergency restart #{self.restart_count}")
            await asyncio.sleep(5)
            try:
                await application.stop()
                await asyncio.sleep(2)
                await application.start()
                await application.updater.start_polling(drop_pending_updates=True)
                logger.info("Emergency restart successful")
            except Exception as e:
                logger.critical(f"Emergency restart failed: {e}")

    def stop(self):
        self.running = False
