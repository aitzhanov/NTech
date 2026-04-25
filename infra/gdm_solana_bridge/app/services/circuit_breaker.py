import time


class CircuitBreaker:

    def __init__(self, failure_threshold=5, recovery_time=30):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "open"

    def allow_request(self):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "half_open"
                return True
            return False
        return True
