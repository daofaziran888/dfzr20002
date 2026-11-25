"""突发事件领域服务：事件等级分类、处置时效跟踪。"""
from __future__ import annotations
from typing import Any
from app.services.base import BaseModuleService


class IncidentService(BaseModuleService):
    MODULE = "incident"
    ENTITY = "事件记录"
    OPERATION_TERM = "确认处置"
    LIST_FIELDS = ["事件类型", "发生位置", "处置班组", "处置结果", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["事件类型", "发生位置", "处置班组", "处置结果"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认处置": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
    RELATED_MODULES = ["safety"]

    def validate_entry(self, values: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        etype = str(values.get("事件类型", "")).strip()
        if etype not in ("设施故障", "安全事故", "人员异常", "自然灾害", "其他"):
            errors.append(f"事件类型 {etype} 不在允许范围")
        return errors

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        rows = self.related_rows("incident")
        by_type: dict[str, int] = {}
        for r in rows:
            t = str(r.get("事件类型", "未分类"))
            by_type[t] = by_type.get(t, 0) + 1
        base["by_type"] = by_type
        return base