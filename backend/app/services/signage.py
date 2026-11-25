"""导视系统领域服务：指示内容规范校验、安装点位重复检查。"""
from __future__ import annotations
from typing import Any
from app.services.base import BaseModuleService
from app.store import store


class SignageService(BaseModuleService):
    MODULE = "signage"
    ENTITY = "导视牌"
    OPERATION_TERM = "确认导视"
    LIST_FIELDS = ["指示内容", "安装点位", "尺寸规格", "发光类型", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["指示内容", "安装点位", "尺寸规格"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认导视": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
    RELATED_MODULES = ["electrical"]

    def validate_entry(self, values: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        location = str(values.get("安装点位", "")).strip()
        if location:
            existing = store.rows(self.MODULE)
            for s in existing:
                if str(s.get("安装点位", "")) == location and s.get("status") != "已撤回":
                    errors.append(f"安装点位 {location} 已被占用")
                    break
        return errors

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        return base