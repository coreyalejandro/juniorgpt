"""Lightweight service wrapper for running an agent as a microservice.

Exposes two HTTP endpoints:
    * `/health`  - simple health check returning agent metadata
    * `/process` - process an incoming message using the agent

The service is intentionally minimal so individual agents can be deployed
independently and interacted with over HTTP. Each request is executed in a
new asyncio event loop to keep the dependencies light.
"""
from __future__ import annotations

import asyncio
from flask import Flask, jsonify, request

from .base_agent import BaseAgent


def create_agent_app(agent: BaseAgent) -> Flask:
    """Create a Flask application wrapping the provided agent.

    Args:
        agent: Instance of an agent implementing :class:`BaseAgent`.

    Returns:
        Configured :class:`flask.Flask` application.
    """
    app = Flask(__name__)

    @app.get("/health")
    def health():
        """Return basic agent information for health checks."""
        return jsonify({"status": "ok", "agent_id": agent.config.agent_id})

    @app.post("/process")
    def process():
        """Process a message using the wrapped agent."""
        data = request.get_json(force=True) or {}
        message = data.get("message", "")
        context = data.get("context")

        # Each request runs the async agent in its own event loop
        response = asyncio.run(agent.execute(message, context))
        return jsonify(response.to_dict())

    return app
