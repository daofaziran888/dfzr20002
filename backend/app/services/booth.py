"""展位编排领域服务：分配校验、面积核算、展位状态联动各模块。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class BoothService(BaseModuleService):
    MODULE = "booth"
    ENTITY = "展位"
    OPERATION_TERM = "确认展位"
    LIST_FIELDS = ["展位编号", "面积尺寸", "开口方向", "所属区域", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["展位编号", "面积尺寸", "开口方向", "所属区域"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认展位": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
    RELATED_MODULES = ["electrical", "design", "safety", "checklist", "handover"]

    def validate_entry(self, values: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        booth_no = str(values.get("展位编号", "")).strip()
        if not booth_no:
            errors.append("展位编号不能为空")
        else:
            existing = store.find_booth(booth_no)
            if existing:
                errors.append(f"展位编号 {booth_no} 已存在")
        return errors

    def validate_action(self, entry_id: int, action: str) -> tuple[bool, str]:
        if action == "确认展位":
            entry = store.find(self.MODULE, entry_id)
            if entry is None:
                return False, "展位不存在"
            booth_no = str(entry.get("展位编号", ""))
            # 检查是否有设计方案
            designs = store.rows("design")
            has_design = any(str(d.get("备注说明", "")) == booth_no for d in designs)
            if not has_design:
                return False, f"展位 {booth_no} 需要先完成方案设计"
        return True, ""

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        rows = store.rows(self.MODULE)
        confirmed = [r for r in rows if r.get("status") == "已确认"]
        base["confirmed_booths"] = [r.get("展位编号") for r in confirmed]
        # 计算总面积
        total_area = 0.0
        for booth in confirmed:
            try:
                area = float(str(booth.get("面积尺寸", "0")).replace("平米", "").replace("㎡", "").strip())
                total_area += area
            except (ValueError, AttributeError):
                pass
        base["total_confirmed_area"] = total_area
        return base