"""Deterministic orchestrator for the AI-Hedgefonds agent pipeline.

This package contains no LLM logic itself. It sequences the seven agents
described in agents/*.md, validates their JSON output against fixed
schemas, enforces hard risk limits in code (not by trusting an agent's
judgment), and persists a full audit trail of every run — exactly the
"Orchestrierung" section of docs/02-architektur.md.
"""
