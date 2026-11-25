"""场馆规划领域服务：面积校验、场地激活后联动展位编排。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.services import exhibition


class VenueService(BaseModuleService):
    MODULE = "venue"
    ENTITY = "场馆"
    OPERATION_TERM = "确认场馆"
    LIST_FIELDS = ["场馆名称", "可用面积", "层高限制", "地面承重", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["场馆名称", "可用面积", "层高限制"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认场馆": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
    RELATED_MODULES = ["booth", "electrical"]

    def validate_entry(self, values: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        try:
            area = float(str(values.get("可用面积", "0")).replace("平米", "").replace("㎡", "").strip())
            if area <= 0:
                errors.append("可用面积必须大于0")
        except (ValueError, AttributeError):
            errors.append("可用面积格式不正确")
        return errors

    def validate_action(self, entry_id: int, action: str) -> tuple[bool, str]:
        if action == "确认场馆":
            venue = store.find(self.MODULE, entry_id)
            if venue is None:
                return False, "场馆不存在"
            # 确认场馆时联动校验面积配额
            area_result = exhibition.check_venue_capacity(entry_id)
            if not area_result["ok"] and area_result["quota"]:
                return False, area_result["reason"]
        return True, ""

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        rows = store.rows(self.MODULE)
        confirmed = [r for r in rows if r.get("status") == "已确认"]
        base["confirmed_venues"] = [{r.get("场馆名称"): r.get("可用面积")} for r in confirmed]
        return base