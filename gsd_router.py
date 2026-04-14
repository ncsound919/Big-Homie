"""gsd_router.py — Big Homie GSD (Get Shit Done) Task Router
Sits between cognitive_core.py / heartbeat.py and the three revenue verticals.

Usage:
    from gsd_router import gsd_router
    result = await gsd_router.dispatch("@rap make a trap video about hustling")
"""
from __future__ import annotations
import asyncio, re
from typing import Any, Dict, Optional
from loguru import logger


CONTEXT_PATTERNS = {
    "@rap":      r"@rap|rap video|make.*video|generate.*video|music video",
    "@content":  r"@content|write.*post|blog|thread|tiktok|script|newsletter|caption",
    "@site":     r"@site|build.*site|create.*website|website|landing page",
    "@code":     r"@code|write.*code|build.*app|implement|debug|opencode",
    "@research": r"@research|research|find|search|look up|analyse|report on",
    "@revenue":  r"@revenue|earn|monetise|sell|billing|stripe|invoice",
}


class GSDRouter:
    """
    Routes a natural-language task string to the correct Big Homie vertical.
    Falls back to sub_agents generic task execution when no context matches.
    """

    def detect_context(self, task: str) -> str:
        low = task.lower()
        for ctx, pattern in CONTEXT_PATTERNS.items():
            if re.search(pattern, low):
                return ctx
        return "@general"

    async def dispatch(self, task: str,
                        brief_dict: Optional[Dict] = None) -> Dict[str, Any]:
        ctx = self.detect_context(task)
        logger.info(f"[GSDRouter] detected context={ctx} for task='{task[:80]}'")

        if ctx == "@rap":
            from rap_video_engine import handle_rap_request
            return await handle_rap_request(task)

        elif ctx == "@content":
            from content_factory import handle_content_request
            return await handle_content_request(task)

        elif ctx == "@site":
            from site_builder import handle_site_request
            return await handle_site_request(task, brief_dict)

        elif ctx == "@code":
            return await self._handle_code(task)

        elif ctx == "@research":
            return await self._handle_research(task)

        elif ctx == "@revenue":
            return await self._handle_revenue(task)

        else:
            return await self._handle_general(task)

    async def _handle_code(self, task: str) -> Dict:
        try:
            from sub_agents import orchestrator
            result = await orchestrator.execute_task_with_sub_agents(task=task, parallel=False)
            return {"context": "@code", "result": result}
        except ImportError:
            return {"context": "@code", "result": f"[code stub for: {task}]"}

    async def _handle_research(self, task: str) -> Dict:
        try:
            from sub_agents import orchestrator
            result = await orchestrator.execute_task_with_sub_agents(task=task, parallel=True)
            return {"context": "@research", "result": result}
        except ImportError:
            return {"context": "@research", "result": f"[research stub for: {task}]"}

    async def _handle_revenue(self, task: str) -> Dict:
        try:
            from revenue_engine import RevenueEngine
            engine = RevenueEngine()
            report = engine.get_daily_report()
            return {"context": "@revenue", "report": str(report)}
        except ImportError:
            return {"context": "@revenue", "result": "[revenue stub]"}

    async def _handle_general(self, task: str) -> Dict:
        try:
            from sub_agents import orchestrator
            result = await orchestrator.execute_task_with_sub_agents(task=task)
            return {"context": "@general", "result": result}
        except ImportError:
            return {"context": "@general", "result": f"[general stub for: {task}]"}


gsd_router = GSDRouter()


async def process_gsd_queue(queue_items: list) -> list:
    """
    Called by heartbeat.py to drain the GSD inbox.
    Each item is a dict with at least {"task": str}.
    """
    results = []
    for item in queue_items:
        try:
            res = await gsd_router.dispatch(
                item.get("task", ""),
                brief_dict=item.get("brief_dict"),
            )
            results.append({"item": item, "result": res, "status": "ok"})
        except Exception as e:
            logger.error(f"[GSDRouter] queue item failed: {e}")
            results.append({"item": item, "error": str(e), "status": "failed"})
    return results


if __name__ == "__main__":
    import sys
    async def _run():
        task = " ".join(sys.argv[1:]) or "@content write a tiktok script about AI beats"
        print(f"\nDispatching: '{task}'\n")
        result = await gsd_router.dispatch(task)
        import json
        print(json.dumps(result, indent=2, default=str))
    asyncio.run(_run())
