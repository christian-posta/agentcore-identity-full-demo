# Deploy supply-chain-agent to AgentCore Runtime (A2A)

Guide for deploying and testing the Supply Chain Optimizer Agent on Amazon Bedrock AgentCore Runtime using the AgentCore CLI. The agent supports both the AgentCore **invocations** API and the **A2A protocol** (agent card + `message/send`).

---

## Prerequisites

- Python 3.10+
- [AgentCore CLI](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/) installed and configured
- AWS credentials configured (e.g. `aws configure` or `AWS_PROFILE`)
- For LLM calls: `GOOGLE_API_KEY` (or your configured model provider) in `.env` or environment

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

Server listens on **http://localhost:8080** (or the port shown in the output).

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

### AgentCore invocations (CLI)

```bash
agentcore invoke --local '{"prompt": "optimize laptop supply chain"}'
```

### AgentCore invocations (curl)

Replace `PORT` with 8080 (agentcore dev) or 9000 (python main.py with PORT=9000):

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"optimize laptop supply chain"}'
```

### A2A: agent card

```bash
curl http://localhost:8080/.well-known/agent-card.json
```

Use this URL in your A2A client as the agent’s base URL when testing locally (e.g. `http://localhost:8080/` or `http://localhost:9000/`).

### A2A: message/send (curl)

```bash
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### A2A client (local)

Point your A2A client at **base URL** `http://localhost:8080/` (or `http://localhost:9000/` when using `python main.py`). The client will:

1. GET `/.well-known/agent-card.json` for the agent card.
2. POST `/` for `message/send` (JSON-RPC).

---

## 4. Deploy to AgentCore Runtime

From the same directory (with `main.py` and `.bedrock_agentcore.yaml`):

```bash
agentcore deploy
```

Note the deploy output: it will include the **agent ARN** and (depending on your setup) the **runtime URL** for the deployed agent. You need the runtime URL (or agent ARN + region) to call the agent and to configure an A2A client.

---

## 5. Call the deployed agent

### AgentCore invocations (CLI)

Do **not** use `--local`; the CLI uses the deployed runtime from your config.

```bash
agentcore invoke '{"prompt": "optimize laptop supply chain"}'
```

### AgentCore invocations (curl / API)

Use the runtime invocation URL from your deploy output or from the AgentCore console, with the same auth (e.g. SigV4 or JWT) that your runtime requires. For SigV4 the URL is typically:

`https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<agent-arn>/invocations/`

(Replace `<region>` and `<agent-arn>` with your values. The agent ARN must be URL-encoded when used in the path.)

### A2A: base URL when deployed

The A2A base URL for the deployed agent is the **runtime invocation URL** (same as above), for example:

- **Base URL:** `https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<agent-arn>/invocations/`

Replace `<region>` and `<agent-arn>` with your values from `agentcore deploy` or `.bedrock_agentcore.yaml`.

### A2A: agent card (deployed)

```bash
RUNTIME_URL="https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<agent-arn>/invocations"
curl "$RUNTIME_URL/.well-known/agent-card.json"
```

If your runtime uses IAM (SigV4), sign the request with the `bedrock-agentcore` service in the correct region.

### A2A: message/send (deployed)

POST the same JSON-RPC `message/send` body to the base URL:

- **URL:** `{RUNTIME_URL}/` (e.g. `https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<agent-arn>/invocations/`)
- **Method:** POST
- **Body:** JSON-RPC 2.0 with `method`: `"message/send"` and `params.message` as in section 3.

Authentication (SigV4, JWT, etc.) must match what the runtime is configured to accept.

### Calling directly with JWT (Bearer token)

```bash
export TOKEN=your-jwt-token-here

curl -X POST \
  "https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<url-encoded-agent-arn>/invocations?qualifier=DEFAULT" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: $(uuidgen)" \
  -d '{"prompt": "Hello!"}'
```

---

## Quick reference: local vs deployed

| Action | Local | Deployed |
|--------|-------|----------|
| **Base URL** | `http://localhost:8080/` or `http://localhost:9000/` | `https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<agent-arn>/invocations/` |
| **AgentCore invoke** | `agentcore invoke --local '{"prompt":"..."}'` | `agentcore invoke '{"prompt":"..."}'` |
| **Invocations (curl)** | `POST http://localhost:8080/invocations` | `POST {RUNTIME_URL}/invocations` (with auth) |
| **A2A agent card** | `GET http://localhost:8080/.well-known/agent-card.json` | `GET {RUNTIME_URL}/.well-known/agent-card.json` (with auth) |
| **A2A message/send** | `POST http://localhost:8080/` (JSON-RPC body) | `POST {RUNTIME_URL}/` (JSON-RPC body + auth) |

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

- **`GOOGLE_API_KEY`** (or your model provider key) is set in the runtime environment or `.env` if bundled
- **`PORT`**: AgentCore sets this to 9000 for A2A; do not override in production
- **`MARKET_ANALYSIS_AGENT_URL`**: If the agent delegates to the market-analysis agent, set this to the deployed or accessible URL of that agent
