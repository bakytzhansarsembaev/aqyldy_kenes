"""
Metrics Collector для Task Helper.

Собирает и хранит метрики производительности Task Helper:
- Количество запросов
- Автономные решения vs эскалации
- Среднее количество подсказок
- Ошибки API
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import threading


# Директория для метрик
METRICS_DIR = Path(__file__).parent.parent.parent.parent / "logs"
METRICS_DIR.mkdir(exist_ok=True)


@dataclass
class TaskHelperMetrics:
    """Метрики Task Helper за период"""

    # Общие метрики
    total_requests: int = 0
    autonomous_resolutions: int = 0  # Решено без ментора
    escalations: int = 0  # Передано ментору

    # Детальные метрики
    avg_hints_per_task: float = 0.0
    tasks_completed: int = 0  # Ученик решил задачу

    # По уровням подсказок
    hints_level_distribution: Dict[int, int] = field(default_factory=dict)

    # Ошибки
    api_errors: int = 0
    validation_errors: int = 0

    # Производительность
    avg_response_time_ms: float = 0.0
    total_response_time_ms: float = 0.0

    # Время сбора метрик
    started_at: Optional[str] = None
    updated_at: Optional[str] = None

    def autonomy_rate(self) -> float:
        """Процент автономных решений (без ментора)"""
        if self.total_requests == 0:
            return 0.0
        return (self.autonomous_resolutions / self.total_requests) * 100

    def success_rate(self) -> float:
        """Процент успешно решённых задач"""
        if self.total_requests == 0:
            return 0.0
        return (self.tasks_completed / self.total_requests) * 100

    def escalation_rate(self) -> float:
        """Процент эскалаций к ментору"""
        if self.total_requests == 0:
            return 0.0
        return (self.escalations / self.total_requests) * 100

    def error_rate(self) -> float:
        """Процент ошибок"""
        if self.total_requests == 0:
            return 0.0
        total_errors = self.api_errors + self.validation_errors
        return (total_errors / self.total_requests) * 100

    def to_dict(self) -> dict:
        """Экспорт метрик в dict"""
        return {
            "total_requests": self.total_requests,
            "autonomous_resolutions": self.autonomous_resolutions,
            "escalations": self.escalations,
            "avg_hints_per_task": round(self.avg_hints_per_task, 2),
            "tasks_completed": self.tasks_completed,
            "hints_level_distribution": self.hints_level_distribution,
            "api_errors": self.api_errors,
            "validation_errors": self.validation_errors,
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "kpi": {
                "autonomy_rate": round(self.autonomy_rate(), 2),
                "success_rate": round(self.success_rate(), 2),
                "escalation_rate": round(self.escalation_rate(), 2),
                "error_rate": round(self.error_rate(), 2)
            }
        }


class MetricsCollector:
    """Сборщик метрик Task Helper (thread-safe)"""

    def __init__(self):
        self.metrics = TaskHelperMetrics()
        self.metrics.started_at = datetime.now().isoformat()
        self._hints_distribution: Dict[int, int] = {}
        self._total_hints: int = 0
        self._lock = threading.Lock()

    def record_request(self):
        """Записать новый запрос"""
        with self._lock:
            self.metrics.total_requests += 1
            self.metrics.updated_at = datetime.now().isoformat()

    def record_hint(self, level: int):
        """Записать выданную подсказку"""
        with self._lock:
            self._hints_distribution[level] = self._hints_distribution.get(level, 0) + 1
            self._total_hints += 1
            self.metrics.updated_at = datetime.now().isoformat()

    def record_escalation(self):
        """Записать эскалацию к ментору"""
        with self._lock:
            self.metrics.escalations += 1
            self.metrics.updated_at = datetime.now().isoformat()

    def record_completion(self, hints_used: int = 0):
        """Записать успешное завершение задачи"""
        with self._lock:
            self.metrics.tasks_completed += 1
            self.metrics.autonomous_resolutions += 1
            self.metrics.updated_at = datetime.now().isoformat()

    def record_api_error(self):
        """Записать ошибку API"""
        with self._lock:
            self.metrics.api_errors += 1
            self.metrics.updated_at = datetime.now().isoformat()

    def record_validation_error(self):
        """Записать ошибку валидации"""
        with self._lock:
            self.metrics.validation_errors += 1
            self.metrics.updated_at = datetime.now().isoformat()

    def record_response_time(self, time_ms: float):
        """Записать время ответа"""
        with self._lock:
            self.metrics.total_response_time_ms += time_ms
            if self.metrics.total_requests > 0:
                self.metrics.avg_response_time_ms = (
                    self.metrics.total_response_time_ms / self.metrics.total_requests
                )
            self.metrics.updated_at = datetime.now().isoformat()

    def calculate_averages(self):
        """Вычислить средние значения"""
        with self._lock:
            if self.metrics.total_requests > 0:
                total_hints = sum(
                    level * count
                    for level, count in self._hints_distribution.items()
                )
                self.metrics.avg_hints_per_task = total_hints / self.metrics.total_requests

            self.metrics.hints_level_distribution = self._hints_distribution.copy()

    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """
        Экспортировать метрики в файл.

        Args:
            filepath: Путь к файлу (по умолчанию logs/metrics.json)

        Returns:
            Путь к файлу с метриками
        """
        self.calculate_averages()

        if filepath is None:
            filepath = str(METRICS_DIR / "metrics.json")

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metrics.to_dict(), f, indent=2, ensure_ascii=False)

        return filepath

    def print_summary(self):
        """Вывести summary метрик в консоль"""
        self.calculate_averages()

        print("\n" + "=" * 60)
        print("TASK HELPER METRICS SUMMARY")
        print("=" * 60)
        print(f"Total Requests: {self.metrics.total_requests}")
        print(f"Autonomy Rate: {self.metrics.autonomy_rate():.1f}%")
        print(f"Success Rate: {self.metrics.success_rate():.1f}%")
        print(f"Escalation Rate: {self.metrics.escalation_rate():.1f}%")
        print(f"Error Rate: {self.metrics.error_rate():.1f}%")
        print(f"Avg Hints: {self.metrics.avg_hints_per_task:.2f}")
        print(f"Avg Response Time: {self.metrics.avg_response_time_ms:.0f}ms")
        print(f"API Errors: {self.metrics.api_errors}")
        print(f"Validation Errors: {self.metrics.validation_errors}")
        print("-" * 60)
        print("Hints Distribution:")
        for level, count in sorted(self._hints_distribution.items()):
            print(f"  Level {level}: {count}")
        print("=" * 60 + "\n")

    def get_metrics(self) -> dict:
        """Получить текущие метрики как dict"""
        self.calculate_averages()
        return self.metrics.to_dict()

    def reset(self):
        """Сбросить метрики"""
        with self._lock:
            self.metrics = TaskHelperMetrics()
            self.metrics.started_at = datetime.now().isoformat()
            self._hints_distribution = {}
            self._total_hints = 0


# Глобальный коллектор метрик (синглтон)
metrics_collector = MetricsCollector()


# ============================================
# Утилиты для интеграции
# ============================================

def auto_export_metrics(every_n_requests: int = 100):
    """
    Автоматический экспорт метрик каждые N запросов.

    Использование:
        metrics_collector.record_request()
        auto_export_metrics(100)
    """
    if metrics_collector.metrics.total_requests % every_n_requests == 0:
        metrics_collector.export_metrics()
        print(f"[Metrics] Exported after {metrics_collector.metrics.total_requests} requests")


def get_health_status() -> dict:
    """
    Получить статус здоровья Task Helper на основе метрик.

    Returns:
        Dict с статусом и деталями
    """
    metrics = metrics_collector.get_metrics()

    # Определяем статус на основе KPI
    autonomy = metrics["kpi"]["autonomy_rate"]
    error_rate = metrics["kpi"]["error_rate"]

    if error_rate > 5 or autonomy < 50:
        status = "unhealthy"
    elif error_rate > 2 or autonomy < 70:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "metrics": metrics,
        "thresholds": {
            "autonomy_target": 70,
            "error_threshold": 2,
            "escalation_threshold": 30
        }
    }
