"""业务路由汇总：通用资源路由 + 跨模块会展引擎。"""
from __future__ import annotations

from app.routers import resource
from app.routers.exhibition_routes import exhibition_router

ROUTERS = [resource, exhibition_router]