"""灯光编排领域服务：灯位坐标校验、色温范围与光束角度合规检查。"""
from __future__ import annotations
from typing import Any
from app.services.base import BaseModuleService


class LightingService(BaseModuleService):
    MODULE = "lighting"
    ENTITY = "灯光方案"
    OPERATION_TERM = "确认灯光"
    LIST_FIELDS = ["灯位坐标", "色温设定", "光束角度", "控制通道", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["灯位坐标", "色温设定", "光束角度"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认灯光": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
    RELATED_MODULES = ["electrical"]

    def validate_entry(self, values: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        temp = str(values.get("色温设定", "")).strip()
        if temp and not temp.endswith("K"):
            try:
                k = int(temp)
                if k < 2700 or k > 6500:
                    errors.append(f"色温 {k}K 不在 2700-6500K 范围")
            except ValueError:
                errors.append(f"色温 {temp} 格式不正确")
        angle = str(values.get("光束角度", "")).strip()
        if angle:
            try:
                a = int(angle.replace("°", ""))
                if a <= 0 or a > 120:
                    errors.append(f"光束角度 {a}° 不在 1-120° 范围")
            except ValueError:
                errors.append(f"光束角度 {angle} 格式不正确")
        return errors

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        return base