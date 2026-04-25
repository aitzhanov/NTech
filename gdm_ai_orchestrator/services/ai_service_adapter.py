# -*- coding: utf-8 -*-
"""
ai_service_adapter.py
=====================
Единая точка входа для AI-анализа в gdm_ai_orchestrator.

Делегирует вызовы в claude_agent_adapter, который работает
с gdm.claude.agent из модуля arch_claude_client.

Если в будущем AI-провайдер сменится — достаточно изменить
только этот файл, не трогая orchestrator_service.
"""
from .claude_agent_adapter import analyze_with_claude, merge_results

__all__ = ['analyze_with_claude', 'merge_results']
