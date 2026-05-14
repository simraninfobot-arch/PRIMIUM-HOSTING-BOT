import platform
import time
import logging

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, system health will use basic info")


async def get_system_health():
    """Collects system health data"""
    try:
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            ram = psutil.virtual_memory()
            ram_used_gb = ram.used / (1024**3)
            ram_total_gb = ram.total / (1024**3)
            ram_percent = ram.percent

            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            disk_percent = disk.percent

            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time

            return {
                "status": "ok",
                "cpu": f"{cpu_percent}%",
                "cpu_cores": cpu_count,
                "ram": f"{ram_percent}%",
                "ram_used": f"{ram_used_gb:.1f}GB",
                "ram_total": f"{ram_total_gb:.1f}GB",
                "disk": f"{disk_percent}%",
                "disk_used": f"{disk_used_gb:.1f}GB",
                "disk_total": f"{disk_total_gb:.1f}GB",
                "uptime": f"{int(uptime//3600)}h {int((uptime%3600)//60)}m"
            }
        else:
            return {
                "status": "basic",
                "platform": platform.system(),
                "machine": platform.machine(),
                "processor": platform.processor() or "Unknown",
                "python_version": platform.python_version()
            }
    except Exception as e:
        logger.error(f"System health error: {e}")
        return {"status": "error", "error": str(e)}
