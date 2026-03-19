PAST_INCIDENTS = [
    {
        "alarm": "CPU at 95% on EC2 instance",
        "root_cause": "JVM heap exhaustion causing GC thrash. Java process consuming 94% CPU.",
        "fix": "Restart the service and increase JVM heap size. Add CloudWatch alarm at 80% CPU."
    },
    {
        "alarm": "RDS connection pool exhausted",
        "root_cause": "Connection leak in application code. New deployment introduced unclosed DB connections.",
        "fix": "Rollback the deployment. Fix connection handling in code. Set pool max size limit."
    },
    {
        "alarm": "Memory usage above 90% on EKS pod",
        "root_cause": "Memory leak in Node.js service. Heap growing steadily every 6 hours.",
        "fix": "Increase memory limit temporarily. Profile heap dump. Fix leak in event listener code."
    },
    {
        "alarm": "5xx error rate above 10%",
        "root_cause": "Downstream service timeout. Payment API responding in 30s instead of 3s.",
        "fix": "Set circuit breaker on payment service calls. Alert payment team. Scale payment service."
    },
    {
        "alarm": "Disk usage above 85% on EC2",
        "root_cause": "Application logs not rotating. Log files consuming 40GB over 30 days.",
        "fix": "Clear old logs immediately. Set up logrotate. Add disk usage alarm at 70%."
    }
]