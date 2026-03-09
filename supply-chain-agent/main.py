"""
AgentCore Runtime entrypoint.
Invokes the same startup as __main__.py (sets PORT=9000 in AgentCore config).
"""
import importlib.util
import os
import sys

if __name__ == "__main__":
    # Ensure PORT=9000 when not set (AgentCore A2A contract)
    if "PORT" not in os.environ:
        os.environ["PORT"] = "9000"

    _dir = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "sca_main", os.path.join(_dir, "__main__.py")
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sca_main"] = mod
    spec.loader.exec_module(mod)
    mod.run()
