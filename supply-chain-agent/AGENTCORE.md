# Deploy supply-chain-agent to AgentCore Runtime (A2A)

Guide for deploying and testing the Supply Chain Optimizer Agent on Amazon Bedrock AgentCore Runtime using the AgentCore CLI. The agent uses the **A2A protocol** (agent card + `message/send`). Note: `agentcore dev` uses `uvicorn main:app`, so `main.py` must expose `app` at module level — this is already handled in the current code.

---

## Prerequisites

- Python 3.11+ (3.10 minimum; 3.11 recommended — matches AgentCore runtime)
- [AgentCore CLI](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/) installed and configured
- AWS credentials configured (e.g. `aws configure` or `AWS_PROFILE`)

> **Note:** This agent is rule-based and does not call an LLM directly. No `GOOGLE_API_KEY` is required to run the supply-chain-agent itself. A key is only needed if you also run the `market-analysis-agent`.

Install dependencies from this directory:

```bash
pip install -r requirements.txt
```

Or with uv:

```bash
uv sync
```

---

## 1. Agentcore Configure the agent (one-time)

Run from the `supply-chain-agent/` directory. This creates or updates `.bedrock_agentcore.yaml`.

```bash
agentcore configure --entrypoint main.py --name a2a_supply_chain_agent --protocol A2A \
  --disable-memory --non-interactive \
  --request-header-allowlist "X-Amzn-Bedrock-AgentCore-Runtime-Custom-User-Id"
```

To allow multiple headers: `--request-header-allowlist "Header1,Header2"`.

---

## 2. Run locally

### Option A: AgentCore dev server (recommended)

Starts the agent with the same behavior as the deployed runtime.

```bash
agentcore dev
```

Server auto-selects a free port starting at 8080 — check the output for the actual port, e.g.:

```
✓ Using port 8082 instead
Server will be available at: http://localhost:8082/invocations
```

Use that port in all the commands below (replace `PORT` with it).

### Option B: Python directly

To simulate the AgentCore A2A contract (port 9000):

```bash
PORT=9000 python main.py
```

For standard local dev (port 9999):

```bash
python main.py
```

Or with uv: `uv run python main.py`.

---

## 3. Call the agent (local)

With the server running (Option A or B above), use any of these from another terminal.

> **A2A agents do not expose `/invocations`** — `agentcore invoke --dev` will return 404. Use the A2A endpoints below directly.

### A2A: agent card

Replace `PORT` with the port shown in the `agentcore dev` output (or 9000/9999 for Option B):

```bash
curl http://localhost:PORT/.well-known/agent-card.json
```

Use the base URL `http://localhost:PORT/` in your A2A client.

### A2A: message/send (curl)

```bash
curl -X POST http://localhost:PORT/ \
  -H "Content-Type: application/json" \
  -d ‘{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "optimize laptop supply chain for Q2 hiring"}],
        "messageId": "00000000-0000-0000-0000-000000000001"
      }
    }
  }’
```

### A2A client (local)

Point your A2A client at **base URL** `http://localhost:PORT/` (or `http://localhost:9000/` when using `python main.py`). The client will:

1. GET `/.well-known/agent-card.json` for the agent card.
2. POST `/` for `message/send` (JSON-RPC).

---

## 4. Deploy to AgentCore Runtime

From the `supply-chain-agent/` directory (requires `main.py` and `.bedrock_agentcore.yaml`):

```bash
agentcore deploy
```

If the agent already exists from a previous deploy, add `--auto-update-on-conflict`:

```bash
agentcore deploy --auto-update-on-conflict
```

The output will include the **agent ARN**, e.g.:

```
✅ Agent created/updated: arn:aws:bedrock-agentcore:us-west-2:<account>:runtime/a2a_supply_chain_agent-<id>
```

Record this ARN — you need it to construct the runtime URL for all A2A calls.

The **runtime URL** for all deployed calls is:

```
https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<url-encoded-agent-arn>/invocations
```

The agent ARN must be URL-encoded in the path (replace `:` with `%3A` and `/` with `%2F`).

---

## 5. Call the deployed agent (A2A over IAM/SigV4)

The default authorization is **IAM (SigV4)**. All requests to the deployed runtime must be signed with `bedrock-agentcore` as the service name.

> **A2A agents do not use the `/invocations` path for JSON-RPC.** The A2A endpoints are:
> - Agent card: `GET {RUNTIME_URL}/.well-known/agent-card.json`
> - Message send: `POST {RUNTIME_URL}/`

### Build the runtime URL

```bash
AGENT_ARN="arn:aws:bedrock-agentcore:us-west-2:<account>:runtime/a2a_supply_chain_agent-<id>"
REGION="us-west-2"
ENCODED_ARN=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$AGENT_ARN")
RUNTIME_URL="https://bedrock-agentcore.${REGION}.amazonaws.com/runtimes/${ENCODED_ARN}/invocations"
```

### A2A: agent card (deployed, SigV4)

Use Python with boto3 to sign the request (works with any AWS credential type including SSO):

```python
import boto3, requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib.parse

AGENT_ARN = "arn:aws:bedrock-agentcore:us-west-2:<account>:runtime/a2a_supply_chain_agent-<id>"
REGION = "us-west-2"

session = boto3.Session()
creds = session.get_credentials().get_frozen_credentials()
encoded_arn = urllib.parse.quote(AGENT_ARN, safe='')
runtime_url = f"https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{encoded_arn}/invocations"

req = AWSRequest(method="GET", url=runtime_url + "/.well-known/agent-card.json")
SigV4Auth(creds, "bedrock-agentcore", REGION).add_auth(req)
resp = requests.get(req.url, headers=dict(req.headers))
print(resp.status_code, resp.json())
```

### A2A: message/send (deployed, SigV4)

From the `supply-chain-agent` directory, run the script. It reads the agent ARN and region from `.bedrock_agentcore.yaml` (written by deploy), so no env vars are needed after a deploy:

```bash
cd supply-chain-agent
python invoke_a2a.py
```

Optional: pass a custom message as the first argument (default is "optimize laptop supply chain for Q2 hiring"):

```bash
python invoke_a2a.py "your message here"
```

You can override with `AGENT_ARN` and `AWS_REGION` if needed. The script uses `boto3.Session().get_credentials()` for SigV4, so it works with SSO and assumed-role sessions.

> **Note:** `aws configure get aws_access_key_id/aws_secret_access_key` does **not** work for SSO/assumed-role sessions — always use `boto3.Session().get_credentials()` which resolves the full credential chain including session tokens.

### Calling with JWT (Bearer token, after configuring custom authorizer)

After re-configuring with `--authorizer-config` (see "Configure inbound auth" below):

```bash
export TOKEN=your-jwt-token-here

curl -X POST \
  "${RUNTIME_URL}/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: $(uuidgen)" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "optimize laptop supply chain"}],
        "messageId": "00000000-0000-0000-0000-000000000001"
      }
    }
  }'
```

---

## Quick reference: local vs deployed

| Action | Local (`agentcore dev`) | Local (`python main.py`) | Deployed (IAM/SigV4) |
|--------|------------------------|--------------------------|----------------------|
| **Base URL** | `http://localhost:PORT/` (port shown in output) | `http://localhost:9000/` or `http://localhost:9999/` | `https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<url-encoded-arn>/invocations` |
| **AgentCore invoke** | N/A — A2A agents don't expose `/invocations` locally | N/A | N/A — use A2A JSON-RPC directly |
| **A2A agent card** | `GET http://localhost:PORT/.well-known/agent-card.json` | `GET http://localhost:9000/.well-known/agent-card.json` | `GET {RUNTIME_URL}/.well-known/agent-card.json` + SigV4 |
| **A2A message/send** | `POST http://localhost:PORT/` (JSON-RPC body) | `POST http://localhost:9000/` (JSON-RPC body) | `POST {RUNTIME_URL}/` (JSON-RPC body) + SigV4 |
| **Auth** | None | None | SigV4 (`bedrock-agentcore` service) via `boto3.Session()` |

---

## Configure inbound auth (optional)

To require JWT (e.g. Keycloak or Auth0) for the **deployed** agent, re-run `agentcore configure` with `--authorizer-config` and `--request-header-allowlist "Authorization"`, then **redeploy**.

### Auth0 JWT

```bash
agentcore configure --entrypoint main.py --name a2a_supply_chain_agent --protocol A2A \
  --disable-memory --non-interactive \
  --authorizer-config '{"customJWTAuthorizer":{"discoveryUrl":"https://ceposta-solo.auth0.com/.well-known/openid-configuration","allowedAudience":["https://api.supply-chain-ui.local"]}}' \
  --request-header-allowlist "Authorization"
agentcore deploy
```

Invoke with: `agentcore invoke '{"prompt": "hi"}' --bearer-token "$TOKEN"`. A2A clients use the same token for the runtime URL.

---

## Environment variables

The agent reads configuration from `.env` (see `env.example`). For AgentCore deployment, ensure:

- **`GOOGLE_API_KEY`**: Not needed by this agent (rule-based, no LLM). Only required if you run `market-analysis-agent`.
- **`PORT`**: AgentCore sets this to 9000 for A2A; do not override in production
- **`MARKET_ANALYSIS_AGENT_URL`**: If the agent delegates to the market-analysis agent, set this to the deployed or accessible URL of that agent
