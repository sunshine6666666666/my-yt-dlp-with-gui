import threading
import os
from uuid import uuid4
from copy import copy
from .task import Task, TaskStatus
from .downloader import Downloader
from .logger import setup_logger

logger = setup_logger("QueueManager")

class QueueManager:
    def __init__(self, max_concurrent=5, config=None, yt_dlp_path="./yt-dlp"):
        self.max_concurrent = max_concurrent
        self.config = config
        self.yt_dlp_path = yt_dlp_path
        self.tasks = []
        self.active_downloads = {} # task_id -> Downloader
        self.lock = threading.Lock()
        self.on_update = None # callback(task_id)

    def add_task(self, url):
        logger.info(f"New task added: {url}")
        with self.lock:
            task = Task(id=str(uuid4()), url=url)
            self.tasks.append(task)
        self._schedule()
        return task.id

    def _schedule(self):
        with self.lock:
            pending = [t for t in self.tasks if t.status == TaskStatus.PENDING]
            active_count = len(self.active_downloads)
            slots = max(0, self.max_concurrent - active_count)
            to_start = pending[:slots]
            
            logger.debug(f"Scheduling check. Active: {active_count}, Max: {self.max_concurrent}, Pending slots: {slots}")

            # Mark them as starting so we don't start them again if schedule is called quickly
            for task in to_start:
                task.status = TaskStatus.DOWNLOADING

        # Start downloads outside lock to avoid deadlocks in callbacks if they call back into manager
        for task in to_start:
            logger.info(f"Starting downloader for task: {task.id}")
            output_path = self.config.get("download_path") if self.config else "."
            
            # Get download path from config
            output_path = output_path
            
            downloader = Downloader(
                task, 
                output_path, 
                self.yt_dlp_path,
                on_progress=lambda p, s, e, t=task: self._on_progress(t.id, p, s, e),
                on_complete=lambda t=task: self._on_complete(t.id),
                on_error=lambda err, t=task: self._on_error(t.id, err),
                config=self.config
            )
            
            with self.lock:
                self.active_downloads[task.id] = downloader
            
            threading.Thread(target=downloader.start, daemon=True).start()
            
            if self.on_update:
                self.on_update(task.id)

    def _on_progress(self, task_id, progress, speed, eta):
        task = self.get_task(task_id)
        if task:
            task.progress = progress
            task.speed = speed
            task.eta = eta
            if self.on_update:
                self.on_update(task_id)

    def _on_complete(self, task_id):
        with self.lock:
            if task_id in self.active_downloads:
                del self.active_downloads[task_id]
        
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.progress = 100.0
            if self.on_update:
                self.on_update(task_id)
        
        self._schedule()

    def _on_error(self, task_id, error):
        with self.lock:
            if task_id in self.active_downloads:
                del self.active_downloads[task_id]
        
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
            if self.on_update:
                self.on_update(task_id)
        
        self._schedule()

    def pause_task(self, task_id):
        downloader = None
        with self.lock:
            downloader = self.active_downloads.get(task_id)
        
        if downloader:
            downloader.pause()
            
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.PAUSED
            if self.on_update:
                self.on_update(task_id)

    def resume_task(self, task_id):
        downloader = None
        with self.lock:
            downloader = self.active_downloads.get(task_id)
        
        if downloader:
            downloader.resume()
            
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.DOWNLOADING
            if self.on_update:
                self.on_update(task_id)

    def cancel_task(self, task_id):
        downloader = None
        with self.lock:
            if task_id in self.active_downloads:
                downloader = self.active_downloads[task_id]
                del self.active_downloads[task_id]
        
        if downloader:
            downloader.cancel()
            
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            if self.on_update:
                self.on_update(task_id)
        
        self._schedule()

    def retry_task(self, task_id):
        task = self.get_task(task_id)
        if task:
            with self.lock:
                task.status = TaskStatus.PENDING
                task.progress = 0
                task.error = ""
            if self.on_update:
                self.on_update(task_id)
            self._schedule()

    def get_task(self, task_id):
        with self.lock:
            for t in self.tasks:
                if t.id == task_id:
                    return t
        return None

    def get_all_tasks(self):
        with self.lock:
            return copy(self.tasks)
