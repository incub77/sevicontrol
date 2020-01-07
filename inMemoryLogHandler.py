from logging import Handler
from collections import deque


class InMemoryLogHandler(Handler):
    def __init__(self, level):
        super().__init__(level=level)
        self.logs = deque([])
        self.log_limit = 50

    def emit(self, record):
        if len(self.logs) >= self.log_limit:
            self.logs.popleft()
        self.logs.append(record)

    def get_logs(self):
        logs = list(self.logs)
        return [self.format(msg) for msg in logs]
