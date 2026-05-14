import queue
import threading
import time
import logging

logger = logging.getLogger(__name__)

user_log_sessions = {}


class LogStreamer:
    """Real-time Log Streaming System"""

    def __init__(self):
        self.active_streams = {}  # {project_name: {"queue": Queue(), "subscribers": set()}}
        self.monitor_threads = {}

    def start_stream(self, project_name, process):
        """Start log stream for new project"""
        if project_name in self.active_streams:
            return

        log_queue = queue.Queue()
        self.active_streams[project_name] = {
            "queue": log_queue,
            "subscribers": set(),
            "process": process,
            "last_lines": [],
            "running": True
        }

        stdout_thread = threading.Thread(
            target=self._read_output,
            args=(project_name, process.stdout, "stdout"),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=self._read_output,
            args=(project_name, process.stderr, "stderr"),
            daemon=True
        )

        stdout_thread.start()
        stderr_thread.start()

        self.monitor_threads[project_name] = (stdout_thread, stderr_thread)
        logger.info(f"📝 Log stream started for {project_name}")

    def _read_output(self, project_name, pipe, pipe_type):
        """Read logs from pipe and put in queue"""
        stream_data = self.active_streams.get(project_name)
        if not stream_data:
            return

        try:
            for line in iter(pipe.readline, ''):
                if not stream_data["running"]:
                    break

                timestamp = time.strftime("%H:%M:%S")
                log_entry = f"[{timestamp}] [{pipe_type.upper()}] {line.rstrip()}"

                stream_data["queue"].put(log_entry)

                stream_data["last_lines"].append(log_entry)
                if len(stream_data["last_lines"]) > 50:
                    stream_data["last_lines"].pop(0)

                for user_id in list(stream_data["subscribers"]):
                    try:
                        if user_id in user_log_sessions and user_log_sessions[user_id]["active"]:
                            user_log_sessions[user_id]["buffer"].append(log_entry)
                    except:
                        pass

        except Exception as e:
            logger.error(f"Log read error for {project_name}: {e}")
        finally:
            pipe.close()

    def subscribe(self, project_name, user_id, chat_id, message_id):
        """Add user to log stream"""
        if project_name not in self.active_streams:
            return False

        stream_data = self.active_streams[project_name]
        stream_data["subscribers"].add(user_id)

        user_log_sessions[user_id] = {
            "project": project_name,
            "chat_id": chat_id,
            "message_id": message_id,
            "buffer": list(stream_data["last_lines"]),
            "active": True,
            "last_update": time.time()
        }
        return True

    def unsubscribe(self, user_id):
        """Remove user from log stream"""
        if user_id in user_log_sessions:
            project_name = user_log_sessions[user_id]["project"]
            if project_name in self.active_streams:
                self.active_streams[project_name]["subscribers"].discard(user_id)
            user_log_sessions[user_id]["active"] = False
            return True
        return False

    def stop_stream(self, project_name):
        """Stop log stream for project"""
        if project_name in self.active_streams:
            self.active_streams[project_name]["running"] = False
            if project_name in self.monitor_threads:
                for thread in self.monitor_threads[project_name]:
                    thread.join(timeout=2)
            del self.active_streams[project_name]
            if project_name in self.monitor_threads:
                del self.monitor_threads[project_name]

    def get_recent_logs(self, project_name, lines=20):
        """Get last few lines"""
        if project_name in self.active_streams:
            return self.active_streams[project_name]["last_lines"][-lines:]
        return []

    def is_streaming(self, project_name):
        """Check if stream is running"""
        return project_name in self.active_streams and self.active_streams[project_name]["running"]
