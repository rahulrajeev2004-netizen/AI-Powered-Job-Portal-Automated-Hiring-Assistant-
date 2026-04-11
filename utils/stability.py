class StabilityTracker:
    def __init__(self):
        self.total_processed = 0
        self.failed_parses = 0
        self.ocr_used = 0
        self.retry_count = 0
        self.timeout_events = 0
        self.crash_events = 0
        
    def track_process(self):
        self.total_processed += 1
        
    def track_failure(self):
        self.failed_parses += 1
        
    def track_fallback(self, type="ocr"):
        if type == "ocr":
            self.ocr_used += 1
        elif type == "retry":
            self.retry_count += 1
            
    def get_error_rate(self):
        if self.total_processed == 0:
            return "0%"
        return f"{(self.failed_parses / self.total_processed) * 100:.1f}%"
    
    def get_report(self):
        return {
            "system_status": "stable" if self.failed_parses == 0 else "degraded",
            "error_rate": self.get_error_rate(),
            "failed_parses": self.failed_parses,
            "fallback_usage": {
                "ocr_used": self.ocr_used,
                "retry_count": self.retry_count
            },
            "system_health": {
                "memory_leak": False,
                "timeout_events": self.timeout_events,
                "crash_events": self.crash_events
            }
        }
