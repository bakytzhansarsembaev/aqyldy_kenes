"""
Тесты для Metrics Collector.

Запуск: pytest src/tests/test_metrics.py -v
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.tools.monitoring.metrics import (
    TaskHelperMetrics,
    MetricsCollector,
    get_health_status
)


class TestTaskHelperMetrics:
    """Тесты для dataclass TaskHelperMetrics"""

    def test_default_values(self):
        """Тест значений по умолчанию"""
        metrics = TaskHelperMetrics()

        assert metrics.total_requests == 0
        assert metrics.autonomous_resolutions == 0
        assert metrics.escalations == 0
        assert metrics.tasks_completed == 0
        assert metrics.api_errors == 0

    def test_autonomy_rate_zero_requests(self):
        """Тест autonomy_rate при нуле запросов"""
        metrics = TaskHelperMetrics()
        assert metrics.autonomy_rate() == 0.0

    def test_autonomy_rate_calculation(self):
        """Тест расчёта autonomy_rate"""
        metrics = TaskHelperMetrics()
        metrics.total_requests = 100
        metrics.autonomous_resolutions = 70

        assert metrics.autonomy_rate() == 70.0

    def test_success_rate_calculation(self):
        """Тест расчёта success_rate"""
        metrics = TaskHelperMetrics()
        metrics.total_requests = 100
        metrics.tasks_completed = 60

        assert metrics.success_rate() == 60.0

    def test_escalation_rate_calculation(self):
        """Тест расчёта escalation_rate"""
        metrics = TaskHelperMetrics()
        metrics.total_requests = 100
        metrics.escalations = 25

        assert metrics.escalation_rate() == 25.0

    def test_error_rate_calculation(self):
        """Тест расчёта error_rate"""
        metrics = TaskHelperMetrics()
        metrics.total_requests = 100
        metrics.api_errors = 3
        metrics.validation_errors = 2

        assert metrics.error_rate() == 5.0

    def test_to_dict(self):
        """Тест экспорта в dict"""
        metrics = TaskHelperMetrics()
        metrics.total_requests = 50
        metrics.autonomous_resolutions = 40
        metrics.escalations = 10

        result = metrics.to_dict()

        assert "total_requests" in result
        assert "kpi" in result
        assert "autonomy_rate" in result["kpi"]
        assert result["total_requests"] == 50


class TestMetricsCollector:
    """Тесты для MetricsCollector"""

    def test_record_request(self):
        """Тест записи запроса"""
        collector = MetricsCollector()

        collector.record_request()
        collector.record_request()

        assert collector.metrics.total_requests == 2

    def test_record_hint(self):
        """Тест записи подсказки"""
        collector = MetricsCollector()

        collector.record_hint(1)
        collector.record_hint(2)
        collector.record_hint(1)

        collector.calculate_averages()

        assert collector._hints_distribution[1] == 2
        assert collector._hints_distribution[2] == 1

    def test_record_escalation(self):
        """Тест записи эскалации"""
        collector = MetricsCollector()

        collector.record_escalation()
        collector.record_escalation()

        assert collector.metrics.escalations == 2

    def test_record_completion(self):
        """Тест записи завершения"""
        collector = MetricsCollector()

        collector.record_completion()

        assert collector.metrics.tasks_completed == 1
        assert collector.metrics.autonomous_resolutions == 1

    def test_record_api_error(self):
        """Тест записи ошибки API"""
        collector = MetricsCollector()

        collector.record_api_error()
        collector.record_api_error()

        assert collector.metrics.api_errors == 2

    def test_record_validation_error(self):
        """Тест записи ошибки валидации"""
        collector = MetricsCollector()

        collector.record_validation_error()

        assert collector.metrics.validation_errors == 1

    def test_record_response_time(self):
        """Тест записи времени ответа"""
        collector = MetricsCollector()
        collector.metrics.total_requests = 2

        collector.record_response_time(100)
        collector.record_response_time(200)

        assert collector.metrics.total_response_time_ms == 300
        assert collector.metrics.avg_response_time_ms == 150

    def test_calculate_averages(self):
        """Тест расчёта средних"""
        collector = MetricsCollector()
        collector.metrics.total_requests = 4

        collector.record_hint(1)
        collector.record_hint(1)
        collector.record_hint(2)
        collector.record_hint(3)

        collector.calculate_averages()

        # (1+1+2+3) / 4 = 1.75
        assert collector.metrics.avg_hints_per_task == 1.75

    def test_export_metrics(self):
        """Тест экспорта метрик в файл"""
        collector = MetricsCollector()
        collector.record_request()
        collector.record_hint(1)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_metrics.json"
            result_path = collector.export_metrics(str(filepath))

            assert Path(result_path).exists()

            with open(result_path, 'r') as f:
                data = json.load(f)

            assert data["total_requests"] == 1

    def test_get_metrics(self):
        """Тест получения метрик"""
        collector = MetricsCollector()
        collector.record_request()
        collector.record_request()
        collector.record_escalation()

        metrics = collector.get_metrics()

        assert metrics["total_requests"] == 2
        assert metrics["escalations"] == 1

    def test_reset(self):
        """Тест сброса метрик"""
        collector = MetricsCollector()
        collector.record_request()
        collector.record_hint(1)
        collector.record_escalation()

        collector.reset()

        assert collector.metrics.total_requests == 0
        assert collector.metrics.escalations == 0
        assert collector._hints_distribution == {}

    def test_thread_safety(self):
        """Тест потокобезопасности"""
        import threading

        collector = MetricsCollector()
        threads = []

        def worker():
            for _ in range(100):
                collector.record_request()
                collector.record_hint(1)

        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert collector.metrics.total_requests == 1000


class TestHealthStatus:
    """Тесты для функции get_health_status"""

    def test_healthy_status(self):
        """Тест здорового статуса"""
        from src.tools.monitoring.metrics import metrics_collector

        metrics_collector.reset()
        metrics_collector.metrics.total_requests = 100
        metrics_collector.metrics.autonomous_resolutions = 80
        metrics_collector.metrics.api_errors = 1

        status = get_health_status()

        assert status["status"] == "healthy"

    def test_degraded_status(self):
        """Тест деградированного статуса"""
        from src.tools.monitoring.metrics import metrics_collector

        metrics_collector.reset()
        metrics_collector.metrics.total_requests = 100
        metrics_collector.metrics.autonomous_resolutions = 65
        metrics_collector.metrics.api_errors = 3

        status = get_health_status()

        assert status["status"] == "degraded"

    def test_unhealthy_status(self):
        """Тест нездорового статуса"""
        from src.tools.monitoring.metrics import metrics_collector

        metrics_collector.reset()
        metrics_collector.metrics.total_requests = 100
        metrics_collector.metrics.autonomous_resolutions = 40
        metrics_collector.metrics.api_errors = 6

        status = get_health_status()

        assert status["status"] == "unhealthy"

    def test_status_includes_thresholds(self):
        """Тест что статус включает пороговые значения"""
        status = get_health_status()

        assert "thresholds" in status
        assert "autonomy_target" in status["thresholds"]
        assert "error_threshold" in status["thresholds"]
