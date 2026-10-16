"""指南能力的 MCP Server。多智能体平台通过 MCP 协议调用。"""
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.capabilities.guideline_service import get_guideline_service
from src.contracts.guideline import (
    RetrievalRequest, RuleCheckRequest,
    CitationCheckRequest, ComplianceRequest,
)
from src.schemas import PatientProfile


app = Server("t2dm-guideline")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_guideline",
            description="检索2型糖尿病临床指南知识。当需要指南依据、推荐意见、证据等级时调用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索问题"},
                    "top_k": {"type": "integer", "default": 3},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="check_guideline_compliance",
            description="校验方案是否符合指南。生成食谱/运动处方后必须调用此工具验证。",
            inputSchema={
                "type": "object",
                "properties": {
                    "plan": {"type": "object", "description": "待校验的方案"},
                    "domain": {"type": "string", "enum": ["diet", "exercise", "medication"]},
                },
                "required": ["plan", "domain"],
            },
        ),
        Tool(
            name="check_rules",
            description="对患者画像和方案执行硬规则校验，返回违规列表。",
            inputSchema={
                "type": "object",
                "properties": {
                    "patient": {"type": "object"},
                    "plan": {"type": "object"},
                },
                "required": ["patient"],
            },
        ),
        Tool(
            name="verify_citations",
            description="核验答案的引用是否能追溯到原文。输出前建议调用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "citations": {"type": "array"},
                },
                "required": ["answer", "citations"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    svc = get_guideline_service()

    if name == "search_guideline":
        resp = svc.retrieve(RetrievalRequest(**arguments))
        return [TextContent(type="text", text=resp.model_dump_json())]

    if name == "check_guideline_compliance":
        resp = svc.check_compliance(ComplianceRequest(**arguments))
        return [TextContent(type="text", text=resp.model_dump_json())]

    if name == "check_rules":
        req = RuleCheckRequest(
            patient=PatientProfile(**arguments["patient"]),
            plan=arguments.get("plan", {}),
        )
        resp = svc.check_rules(req)
        return [TextContent(type="text", text=resp.model_dump_json())]

    if name == "verify_citations":
        resp = svc.check_citations(CitationCheckRequest(**arguments))
        return [TextContent(type="text", text=resp.model_dump_json())]

    return [TextContent(type="text", text=f"未知工具: {name}")]


async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())