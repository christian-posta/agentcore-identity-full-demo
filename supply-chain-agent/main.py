"""
AgentCore Runtime entrypoint.
Exposes `app` at module level for `uvicorn main:app` (agentcore dev / agentcore deploy).
Sets PORT=9000 per AgentCore A2A contract when not already set.
"""
import importlib.util
import os
import sys

from dotenv import load_dotenv
load_dotenv()

# Ensure PORT=9000 when not set (AgentCore A2A contract)
if "PORT" not in os.environ:
    os.environ["PORT"] = "9000"

# Load __main__ module to access create_app()
_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "sca_main", os.path.join(_dir, "__main__.py")
)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["sca_main"] = _mod
_spec.loader.exec_module(_mod)

# Expose app at module level for uvicorn main:app
app = _mod.create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("SUPPLY_CHAIN_AGENT_PORT", "9999")))
    print(f"🚀 Starting Supply Chain Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
