import time
from enum import Enum

class State(Enum):
    CLOSED = "CLOSED"     # Normal operation
    OPEN = "OPEN"         # Failing, reject requests immediately
    HALF_OPEN = "HALF_OPEN" # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = State.CLOSED
        self.failures = 0
        self.last_failure_time = 0

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = State.OPEN
            print(f"Circuit Breaker OPENED (Failures: {self.failures})")

    def record_success(self):
        if self.state == State.HALF_OPEN:
            self.state = State.CLOSED
            self.failures = 0
            print("Circuit Breaker CLOSED (Recovered)")
        elif self.state == State.CLOSED:
            self.failures = 0

    def allow_request(self) -> bool:
        if self.state == State.CLOSED:
            return True
        
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = State.HALF_OPEN
                print("Circuit Breaker HALF_OPEN (Probing)")
                return True
            return False
            
        if self.state == State.HALF_OPEN:
            # Allow one request to probe (simplified: allow all in half-open until success/fail)
            return True
            
        return False
