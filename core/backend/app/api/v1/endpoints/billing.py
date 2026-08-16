"""NeuroSync — OAuth, Billing & Master Dashboard API Router."""

from fastapi import APIRouter
from typing import Dict, List, Any
from app.services.cloud_auth_billing_engine import (
    cloud_auth_billing_engine,
    SubscriptionPlan,
    MasterDashboardOverview
)

router = APIRouter(prefix="/billing", tags=["OAuth, Subscription Billing & Dashboard"])


@router.get("/google-auth-url", response_model=Dict[str, str], summary="Get Google OAuth redirect URL")
async def get_google_auth_url():
    """Get Google OAuth 2.0 redirect URL for Google login."""
    return cloud_auth_billing_engine.get_google_auth_url()


@router.get("/plans", response_model=List[SubscriptionPlan], summary="List subscription plans")
async def get_plans():
    """List available pricing plans."""
    return cloud_auth_billing_engine.get_subscription_plans()


@router.post("/checkout", response_model=Dict[str, str], summary="Create Stripe checkout session")
async def create_checkout(user_id: str, plan_id: str):
    """Create Stripe checkout session for Pro candidate or B2B enterprise tier."""
    return cloud_auth_billing_engine.create_stripe_checkout(user_id, plan_id)


@router.get("/dashboard/master", response_model=MasterDashboardOverview, summary="Get master dashboard metrics")
async def get_master_dashboard(user_id: str = "usr_biswal"):
    """Retrieve master unified 3-pillar ecosystem dashboard metrics."""
    return cloud_auth_billing_engine.get_master_dashboard(user_id)
