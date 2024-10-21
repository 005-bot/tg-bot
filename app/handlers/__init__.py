from aiogram import Router

from .subscription import router as subscription_router
from .help import router as help_router

router = Router(name=__name__)

router.include_routers(subscription_router, help_router)
