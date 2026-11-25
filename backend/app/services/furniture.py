"""家具配置领域服务：家具类型校验、数量需求与展位面积匹配检查。"""
from __future__ import annotations
from typing import Any
from app.services.base import BaseModuleService


class FurnitureService(BaseModuleService):
    MODULE = "furniture"
    ENTITY = "家具方案"
    OPERATION_TERM = "确认配置"
    LIST_FIELDS = ["家具类型", "摆放位置", "数量需求", "风格色调", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["家具类型", "摆放位置", "数量需求"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认配置": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
    RELATED_MODULES = ["booth"]

    def validate_entry(self, values: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        try:
            qty = int(str(values.get("数量需求", "0")).strip())
            if qty <= 0:
                errors.append("数量需求必须大于0")
        except (ValueError, AttributeError):
            errors.append("数量需求格式不正确")
        return errors

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        rows = self.related_rows("furniture")
        if rows:
            base["total_furniture_count"] = sum(
                int(str(r.get("数量需求", "0")).strip()) for r in rows
            )
        return base