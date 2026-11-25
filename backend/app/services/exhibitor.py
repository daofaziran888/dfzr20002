"""参展商管理领域服务：合同金额校验、展品类别与展位匹配校验。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService


class ExhibitorService(BaseModuleService):
    MODULE = "exhibitor"
    ENTITY = "参展商"
    OPERATION_TERM = "确认参展"
    LIST_FIELDS = ["企业名称", "展品类别", "联系人", "合同金额", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["企业名称", "展品类别", "联系人", "合同金额"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认参展": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
    RELATED_MODULES = ["booth"]

    def validate_entry(self, values: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        try:
            amount = float(str(values.get("合同金额", "0")).replace("万元", "").replace(",", "").strip())
            if amount <= 0:
                errors.append("合同金额必须大于0")
        except (ValueError, AttributeError):
            errors.append("合同金额格式不正确")
        return errors

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        rows = self.related_rows("exhibitor")
        confirmed = [r for r in rows if r.get("status") == "已确认"]
        total_amount = 0.0
        for r in confirmed:
            try:
                total_amount += float(str(r.get("合同金额", "0")).replace("万元", "").replace(",", "").strip())
            except (ValueError, AttributeError):
                pass
        base["total_contract_amount"] = total_amount
        return base