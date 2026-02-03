from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, QByteArray
import os

class TaskListModel(QAbstractListModel):
    def __init__(self, tasks=None):
        super().__init__()
        self.tasks = tasks or []

    def rowCount(self, parent=QModelIndex()):
        return len(self.tasks)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.tasks)):
            return None
        
        task = self.tasks[index.row()]
        if role == Qt.UserRole:
            return task
        if role == Qt.DisplayRole:
            return task.title if task.title else task.url
        return None

    def refresh(self, new_tasks):
        self.beginResetModel()
        self.tasks = new_tasks
        self.endResetModel()
