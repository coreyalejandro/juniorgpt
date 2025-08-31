"""Launch a standalone HTTP service for a given agent.

This utility makes it easy to run any agent implementation as an
independent microservice. The script dynamically imports the specified
agent class, initialises its model service using the global configuration
and serves the `/process` and `/health` endpoints defined in
``agents.agent_server``.
"""
from __future__ import annotations

import argparse
import importlib
import json
from typing import Optional

from config import get_config
from services.model_service import ModelService
from agents.base_agent import AgentConfig
from agents.agent_server import create_agent_app


def load_agent(agent_path: str, model_service: ModelService, config: Optional[AgentConfig] = None):
    """Dynamically load and instantiate an agent class."""
    module_name, class_name = agent_path.split(":")
    module = importlib.import_module(module_name)
    AgentClass = getattr(module, class_name)

    if config is not None:
        # Try passing config to the constructor; if not supported, set after
        try:
            return AgentClass(config, model_service=model_service)
        except TypeError:
            agent = AgentClass(model_service=model_service)
            agent.config = config
            return agent
    return AgentClass(model_service=model_service)


def main():
    parser = argparse.ArgumentParser(description="Run an agent as a standalone service")
    parser.add_argument("--agent", required=True, help="Python path to agent class, e.g. agents.implementations.coding_agent:CodingAgent")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--config", help="Path to AgentConfig JSON", default=None)
    args = parser.parse_args()

    cfg = get_config()
    model_service = ModelService(cfg)

    agent_config = None
    if args.config:
        with open(args.config, "r") as f:
            agent_config = AgentConfig(**json.load(f))

    agent = load_agent(args.agent, model_service, agent_config)

    app = create_agent_app(agent)
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
