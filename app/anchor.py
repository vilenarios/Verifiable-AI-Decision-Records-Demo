import json
import logging
import os

import requests

from app.decision_record import canonical_json

logger = logging.getLogger(__name__)


class ArweaveAnchor:
    """Upload proof payloads to Arweave via Turbo SDK."""

    def __init__(self, wallet_path: str, gateway_host: str = "arweave.net"):
        self.gateway_host = gateway_host
        self.enabled = False
        self._turbo = None

        if not os.path.exists(wallet_path):
            logger.warning(f"Arweave wallet not found at {wallet_path}. Anchoring disabled.")
            return

        try:
            from turbo_sdk import ArweaveSigner, Turbo

            with open(wallet_path) as f:
                jwk = json.load(f)
            signer = ArweaveSigner(jwk)
            self._turbo = Turbo(signer)
            self.enabled = True
            logger.info("Arweave anchoring enabled.")
        except Exception as e:
            logger.warning(f"Failed to initialize Arweave anchor: {e}")

    def upload_proof(self, envelope: dict) -> tuple[str, str] | None:
        """Upload proof envelope to Arweave. Returns (tx_id, url) or None."""
        if not self.enabled or not self._turbo:
            return None

        try:
            data_bytes = canonical_json(envelope)
            decision_id = envelope.get("record", {}).get("decision_id", "unknown")
            record_hash = envelope.get("record_hash", "unknown")

            result = self._turbo.upload(
                data=data_bytes,
                tags=[
                    {"name": "Content-Type", "value": "application/json"},
                    {"name": "App-Name", "value": "Verifiable-AI-Demo"},
                    {"name": "Record-Type", "value": "DecisionProof"},
                    {"name": "Decision-ID", "value": decision_id},
                    {"name": "Record-Hash", "value": record_hash},
                ],
            )

            tx_id = result.id
            url = f"https://{self.gateway_host}/{tx_id}"
            logger.info(f"Uploaded to Arweave: tx_id={tx_id}")
            return tx_id, url

        except Exception as e:
            logger.error(f"Arweave upload failed: {e}")
            return None

    def fetch_proof(self, tx_id: str) -> dict | None:
        """Fetch proof envelope from Arweave gateway."""
        try:
            url = f"https://{self.gateway_host}/raw/{tx_id}"
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch from Arweave: {e}")
            return None
