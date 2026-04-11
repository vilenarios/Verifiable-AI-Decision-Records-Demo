# Verifiable AI Decision Records

Tamper-evident AI audit trail anchored to Arweave.

## What This Demonstrates

Every AI prediction creates a **decision record** that is:

1. **Traced** — OpenTelemetry captures runtime context (trace ID, span ID)
2. **Linked to model lineage** — MLflow records which model version produced the output
3. **Hashed & signed** — SHA-256 hash chain + Ed25519 digital signature
4. **Anchored to Arweave** — Immutable permanent storage via ArDrive Turbo SDK
5. **Independently verifiable** — AR.IO Gateway + AR.IO Verify produces attestations

If someone tampers with the local record, the **Arweave-anchored copy** remains intact and verifiable.

## Architecture

```
User Input
  |
  v
FastAPI /predict
  |---> MLflow (model lineage: run_id, version, artifact_uri)
  |---> OpenTelemetry (trace_id, span_id)
  |---> Inference (sklearn LogisticRegression)
  |
  v
Decision Record (canonical JSON)
  |---> SHA-256 hash + hash chain (previous_hash)
  |---> Ed25519 signature
  |
  v
Proof Envelope
  |---> Turbo SDK upload to Arweave
  |---> AR.IO Verify attestation
  |
  v
Append-only local storage + Arweave permanent record
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the Model (optional — auto-trains on first prediction)

```bash
python scripts/train_model.py
```

### 3. Start the App

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open the Dashboard

Navigate to [http://localhost:8000](http://localhost:8000)

## Arweave Setup (Optional)

To enable permanent anchoring:

1. Generate an Arweave wallet at [arweave.app](https://arweave.app)
2. Save the wallet JSON as `keys/arweave_wallet.json`
3. Fund with credits via [ardrive.io](https://ardrive.io)

Without a wallet, the app runs in **local proof mode** — hashing, signing, and verification all work locally.

## Demo Walkthrough

### 1. Make a Prediction

Submit the form with iris flower measurements. Default values are pre-filled.

### 2. View the Decision Record

Click a decision ID to see the full record:
- Model metadata (MLflow run ID, version)
- Trace context (OpenTelemetry trace/span IDs)
- Proof layer (record hash, chain link, signature)
- Arweave anchoring (transaction ID, gateway URL)
- AR.IO verification (level, attestation)

### 3. Tamper with a Record

Click **Tamper** to modify the local record's output hash.

### 4. Verify After Tampering

Click **Verify** — local verification now **FAILS** because:
- The record hash no longer matches the canonical JSON
- The Ed25519 signature is invalid for the modified content

If the record was anchored to Arweave, the external copy is **STILL VALID**.

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/predict` | POST | Run prediction, create decision record (JSON body) |
| `/predict-form` | POST | Same, from HTML form (redirects to detail) |
| `/decisions` | GET | List all decision records |
| `/decisions/{id}` | GET | Get a single decision record |
| `/verify/{id}` | POST | Verify a decision (local + external) |
| `/tamper/{id}` | POST | Tamper with a record (demo only) |

### Example: Make a Prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

### Example: Verify a Decision

```bash
curl -X POST http://localhost:8000/verify/<decision_id>
```

### Example: Tamper and Re-Verify

```bash
# Tamper
curl -X POST http://localhost:8000/tamper/<decision_id>

# Verify (will show hash_valid=false, signature_valid=false)
curl -X POST http://localhost:8000/verify/<decision_id>
```

## Configuration

Environment variables (prefix: `VAIDR_`):

| Variable | Default | Description |
|---|---|---|
| `VAIDR_ARWEAVE_WALLET_PATH` | `keys/arweave_wallet.json` | Arweave JWK wallet |
| `VAIDR_MLFLOW_TRACKING_URI` | `mlruns` | MLflow tracking directory |
| `VAIDR_MLFLOW_MODEL_NAME` | `iris-classifier` | Registered model name |
| `VAIDR_ARIO_GATEWAY_HOST` | `arweave.net` | AR.IO gateway hostname |
| `VAIDR_ARIO_VERIFY_URL` | `http://localhost:4001` | AR.IO Verify service URL |
| `VAIDR_RECORDS_FILE` | `data/records.json` | Local record storage path |

## How It Works

### MLflow — Model Lineage
Every prediction is tied to a specific model version. MLflow captures the run ID, model version, and artifact URI, creating an auditable link between the model and its decisions.

### OpenTelemetry — Runtime Trace
Each prediction creates a distributed trace. The trace ID and span ID are embedded in the decision record, allowing correlation with infrastructure monitoring.

### Proof Layer — Integrity
Decision records are serialized to deterministic canonical JSON, then:
- **SHA-256 hashed** — any change to the record changes the hash
- **Hash-chained** — each record links to the previous record's hash
- **Ed25519 signed** — cryptographic proof of record origin

### ArDrive Turbo SDK — Anchoring
The complete proof envelope is uploaded to Arweave permanent storage. Once confirmed, the data is immutable and publicly accessible.

### AR.IO Verify — Independent Validation
AR.IO Verify independently fetches the Arweave data, recomputes hashes, verifies signatures, and produces a signed attestation — proving the record exists and is authentic without trusting the original system.
