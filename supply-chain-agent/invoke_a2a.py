#!/usr/bin/env python3
"""
Invoke the deployed A2A supply chain agent via message/send (SigV4).
Reads agent ARN (and region) from .bedrock_agentcore.yaml in this directory when run
from supply-chain-agent; override with AGENT_ARN / AWS_REGION env vars if needed.
"""
import argparse
import json
import os
import uuid
from pathlib import Path

import boto3
import requests
import yaml
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib.parse

_CONFIG_PATH = Path(__file__).resolve().parent / ".bedrock_agentcore.yaml"


def _load_agent_arn_and_region() -> tuple[str | None, str | None]:
    """Load agent_arn and region from .bedrock_agentcore.yaml if present."""
    if not _CONFIG_PATH.is_file():
        return None, None
    try:
        with open(_CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)
        default = cfg.get("default_agent")
        if not default or default not in cfg.get("agents", {}):
            return None, None
        agent = cfg["agents"][default]
        arn = (agent.get("bedrock_agentcore") or {}).get("agent_arn")
        region = (agent.get("aws") or {}).get("region")
        return arn, region
    except Exception:
        return None, None


def _get_agent_arn() -> str:
    arn, _ = _load_agent_arn_and_region()
    if arn:
        return arn
    env_arn = os.environ.get("AGENT_ARN")
    if env_arn:
        return env_arn
    return "arn:aws:bedrock-agentcore:us-west-2:<account>:runtime/a2a_supply_chain_agent-<id>"


def _get_region() -> str:
    _, region = _load_agent_arn_and_region()
    if region:
        return region
    return os.environ.get("AWS_REGION", "us-west-2")


def invoke(message: str) -> None:
    agent_arn = _get_agent_arn()
    region = _get_region()
    session = boto3.Session()
    creds = session.get_credentials().get_frozen_credentials()
    encoded_arn = urllib.parse.quote(agent_arn, safe="")
    runtime_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": str(uuid.uuid4()),
            }
        },
    }
    body = json.dumps(payload)

    req = AWSRequest(
        method="POST",
        url=runtime_url + "/",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": str(uuid.uuid4()),
        },
    )
    SigV4Auth(creds, "bedrock-agentcore", region).add_auth(req)
    resp = requests.post(req.url, data=body, headers=dict(req.headers))
    print(resp.status_code)
    result = resp.json()
    for part in result.get("result", {}).get("parts", []):
        if part.get("kind") == "text":
            print(part["text"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoke A2A supply chain agent (message/send, SigV4)")
    parser.add_argument(
        "message",
        nargs="?",
        default="optimize laptop supply chain for Q2 hiring",
        help="User message to send (default: optimize laptop supply chain for Q2 hiring)",
    )
    args = parser.parse_args()
    invoke(args.message)


if __name__ == "__main__":
    main()
