import psutil


def get_system_metrics() -> dict:
    """Returns a snapshot of system CPU, Memory, and Disk usage."""
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": vm.percent,
        "memory_used_gb": round(vm.used / (1024 ** 3), 2),
        "memory_total_gb": round(vm.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
    }
