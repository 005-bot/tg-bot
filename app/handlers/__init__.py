from aiogram import Router

from .help import router as help_router
from .subscription import router as subscription_router
from .feedback import router as feedback_router

router = Router(name=__name__)

router.include_routers(subscription_router, feedback_router, help_router)
