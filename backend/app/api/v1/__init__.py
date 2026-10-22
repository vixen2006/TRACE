"""
TRACE API V1 Router Aggregation.
Combines auth, integrations, projects, activities, contributions, agent, reports, sync, exports, and dashboard.
"""
from fastapi import APIRouter, Depends

from app.api.v1.activities import router as activities_router
from app.api.v1.agent import router as agent_router
from app.api.v1.auth import router as auth_router
from app.api.v1.contributions import router as contributions_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.exports import router as exports_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.projects import router as projects_router
from app.api.v1.reports import router as reports_router
from app.api.v1.sync import router as sync_router
from app.core.deps import get_current_user

router = APIRouter()

# Auth and integrations handle authentication & OAuth callbacks
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])

# All protected application routes strictly require authentication
auth_dep = [Depends(get_current_user)]
router.include_router(projects_router, prefix="/projects", tags=["projects"], dependencies=auth_dep)
router.include_router(activities_router, prefix="/activities", tags=["activities"], dependencies=auth_dep)
router.include_router(contributions_router, prefix="/contributions", tags=["contributions"], dependencies=auth_dep)
router.include_router(agent_router, prefix="/agent", tags=["agent"], dependencies=auth_dep)
router.include_router(reports_router, prefix="/reports", tags=["reports"], dependencies=auth_dep)
router.include_router(sync_router, prefix="/sync", tags=["sync"], dependencies=auth_dep)
router.include_router(exports_router, prefix="/exports", tags=["exports"], dependencies=auth_dep)
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"], dependencies=auth_dep)
