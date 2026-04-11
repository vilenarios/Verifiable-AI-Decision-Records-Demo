import hashlib
import json
import uuid
from datetime import datetime, timezone


def normalize_floats(obj, precision=6):
    """Recursively round floats for deterministic hashing."""
    if isinstance(obj, float):
        return round(obj, precision)
    if isinstance(obj, dict):
        return {k: normalize_floats(v, precision) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [normalize_floats(v, precision) for v in obj]
    return obj


def canonical_json(obj: dict) -> bytes:
    """Deterministic JSON serialization: sorted keys, compact, UTF-8."""
    normalized = normalize_floats(obj)
    return json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def hash_data(data: bytes) -> str:
    """SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def build_decision_record(
    input_data: dict,
    prediction: dict,
    model_name: str,
    model_version: str,
    mlflow_run_id: str,
    artifact_uri: str,
    trace_id: str,
    span_id: str,
    latency_ms: float,
    service_name: str = "verifiable-ai-demo",
) -> dict:
    """Build a canonical decision record dict."""
    return {
        "decision_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "span_id": span_id,
        "service_name": service_name,
        "mlflow_run_id": mlflow_run_id,
        "model_name": model_name,
        "model_version": model_version,
        "artifact_uri": artifact_uri,
        "input_hash": hash_data(canonical_json(input_data)),
        "output_hash": hash_data(canonical_json(prediction)),
        "prediction": prediction,
        "latency_ms": round(latency_ms, 2),
        "human_override": False,
    }
