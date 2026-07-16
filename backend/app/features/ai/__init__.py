"""
AI Feature Module

Provides AI-powered expense parsing using Google Gemini 3 API.
Implements natural language to structured expense data conversion
with personality-flavored commentary and SSE streaming.

Components:
- models: Pydantic models for request/response schemas
- parser_service: Core AI parsing logic and Gemini API integration
- parser_router: SSE streaming endpoint for real-time parsing
"""

__all__ = ["models", "parser_service", "parser_router"]
