"""Langfuse 初始化与 OTLP 导出兜底（本地未起 Langfuse 时不拖垮主流程）。"""

from __future__ import annotations

import base64
import logging
import os
import socket
from typing import Any, Optional, Sequence, Tuple
from urllib.parse import urlparse

from yard.observability.logging import LogModule, get_logger

_log = get_logger(LogModule.SYSTEM)

# 降低 OTEL HTTP 导出器在不可达时的刷屏（仍优先用 no-op 导出器避免重试）
_OTEL_OTLP_LOGGER = "opentelemetry.exporter.otlp.proto.http.trace_exporter"
_OTEL_BSP_LOGGER = "opentelemetry.sdk.trace.export"


def _langfuse_configured() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def _resolve_base_url() -> str:
    return (
        os.getenv("LANGFUSE_BASE_URL")
        or os.getenv("LANGFUSE_HOST")
        or "https://cloud.langfuse.com"
    ).rstrip("/")


def _probe_tcp_reachable(base_url: str, timeout_sec: float) -> bool:
    parsed = urlparse(base_url if "://" in base_url else f"http://{base_url}")
    host = parsed.hostname
    if not host:
        return False
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            return True
    except OSError:
        return False


def _should_probe() -> bool:
    raw = os.getenv("LANGFUSE_PROBE_REACHABILITY", "true").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _suppress_noisy_otel_loggers() -> None:
    for name in (_OTEL_OTLP_LOGGER, _OTEL_BSP_LOGGER):
        logging.getLogger(name).setLevel(logging.CRITICAL)


class _NoOpSpanExporter:
    """不发起网络请求的 Span 导出器。"""

    def export(self, spans: Sequence[Any]) -> Any:
        from opentelemetry.sdk.trace.export import SpanExportResult

        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


class _ResilientSpanExporter:
    """包装真实导出器：失败时记一次日志并返回 SUCCESS，避免 BatchProcessor 反复报错。"""

    def __init__(self, delegate: Any, *, label: str) -> None:
        self._delegate = delegate
        self._label = label
        self._warned = False

    def _warn_once(self, exc: BaseException) -> None:
        if self._warned:
            return
        self._warned = True
        _log.warning(
            f"Langfuse OTLP 导出失败（{self._label}），已静默跳过，主流程不受影响: {exc!r}",
        )

    def export(self, spans: Sequence[Any]) -> Any:
        from opentelemetry.sdk.trace.export import SpanExportResult

        try:
            result = self._delegate.export(spans)
            if result is SpanExportResult.FAILURE:
                self._warn_once(RuntimeError("OTLP export returned FAILURE"))
                return SpanExportResult.SUCCESS
            return result
        except Exception as exc:
            self._warn_once(exc)
            return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        try:
            self._delegate.shutdown()
        except Exception as exc:
            self._warn_once(exc)

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        try:
            return bool(self._delegate.force_flush(timeout_millis))
        except Exception as exc:
            self._warn_once(exc)
            return True


def _build_otlp_exporter(
    *,
    base_url: str,
    public_key: str,
    secret_key: str,
    timeout: int,
) -> Any:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    from langfuse._version import __version__ as langfuse_version

    basic_auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode("ascii")
    headers = {
        "Authorization": f"Basic {basic_auth}",
        "x-langfuse-sdk-name": "python",
        "x-langfuse-sdk-version": langfuse_version,
        "x-langfuse-public-key": public_key,
    }
    traces_path = os.getenv("LANGFUSE_OTEL_TRACES_EXPORT_PATH")
    endpoint = (
        f"{base_url}/{traces_path.lstrip('/')}"
        if traces_path
        else f"{base_url}/api/public/otel/v1/traces"
    )
    return OTLPSpanExporter(endpoint=endpoint, headers=headers, timeout=timeout)


def _pick_span_exporter(
    *,
    base_url: str,
    public_key: str,
    secret_key: str,
    timeout: int,
    probe_timeout: float,
) -> Tuple[Any, str]:
    if _should_probe() and not _probe_tcp_reachable(base_url, probe_timeout):
        _log.warning(
            f"Langfuse 服务不可达（{base_url}），追踪导出已降级为 no-op；"
            "启动 Langfuse 后重启本进程可恢复上报",
        )
        return _NoOpSpanExporter(), "no-op"

    otlp = _build_otlp_exporter(
        base_url=base_url,
        public_key=public_key,
        secret_key=secret_key,
        timeout=timeout,
    )
    return _ResilientSpanExporter(otlp, label=base_url), "otlp"


def init_langfuse() -> Tuple[Optional[Any], Optional[Any]]:
    """初始化 Langfuse client + LangChain CallbackHandler；失败时返回 (None, None)。"""
    if not _langfuse_configured():
        return None, None

    _suppress_noisy_otel_loggers()

    base_url = _resolve_base_url()
    public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    timeout = int(os.getenv("LANGFUSE_TIMEOUT", "5"))
    probe_timeout = float(os.getenv("LANGFUSE_PROBE_TIMEOUT_SEC", "2"))

    try:
        from langfuse import Langfuse
        from langfuse.langchain import CallbackHandler

        span_exporter, mode = _pick_span_exporter(
            base_url=base_url,
            public_key=public_key,
            secret_key=secret_key,
            timeout=timeout,
            probe_timeout=probe_timeout,
        )
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            base_url=base_url,
            timeout=timeout,
            span_exporter=span_exporter,
        )
        handler = CallbackHandler()
        _log.debug(f"Langfuse 已初始化（导出模式: {mode}）")
        return client, handler
    except Exception as exc:
        _log.warning(f"Langfuse 初始化失败，已禁用追踪: {exc!r}")
        return None, None


def safe_flush(client: Any | None) -> None:
    if client is None:
        return
    try:
        client.flush()
    except Exception as exc:
        _log.debug(f"Langfuse flush 失败（已忽略）: {exc!r}")
