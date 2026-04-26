from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("bridge_requests_total", "Total bridge requests", ["action", "status"])

TX_DURATION = Histogram("transaction_duration_seconds", "Transaction processing time")

ERROR_COUNT = Counter("bridge_errors_total", "Total errors", ["code", "type"])
