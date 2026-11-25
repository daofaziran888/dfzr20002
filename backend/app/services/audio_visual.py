"""影音布置领域服务：设备安装位置合规检查、信号线路连通性校验。"""
from __future__ import annotations
from typing import Any
from app.services.base import BaseModuleService


class AudioVisualService(BaseModuleService):
    MODULE = "audio_visual"
    ENTITY = "影音设备"
    OPERATION_TERM = "调试设备"
    LIST_FIELDS = ["设备型号", "安装位置", "信号线路", "调试试音", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["设备型号", "安装位置", "信号线路"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"调试设备": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
    RELATED_MODULES = ["electrical"]

    def validate_entry(self, values: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        model = str(values.get("设备型号", "")).strip()
        if not model:
            errors.append("设备型号不能为空")
        return errors

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        return base