import logging
from typing import TYPE_CHECKING

from aiogram import F, Router, filters, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)

router = Router(name=__name__)

if TYPE_CHECKING:
    from app.admin import Notificator


class FeedbackState(StatesGroup):
    feedback = State()


@router.message(filters.Command("feedback"))
async def feedback_handler(message: types.Message, state: FSMContext):
    if not message.from_user:
        return

    await state.set_state(FeedbackState.feedback)

    await message.answer(
        "Что бы Вы хотели нам сказать?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Ничего")]],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    logger.info("User %d started feedback", message.from_user.id)


@router.message(FeedbackState.feedback, F.text == "Ничего")
async def feedback_cancel_handler(message: types.Message, state: FSMContext):
    if not message.from_user:
        return

    await state.clear()
    await message.answer(
        "Отзыв не отправлен",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    logger.info("User %d canceled feedback", message.from_user.id)


@router.message(FeedbackState.feedback, ~F.text.startswith("/"))
async def feedback_value_handler(
    message: types.Message, state: FSMContext, notificator: "Notificator"
):
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id
    await notificator.feedback(message)

    await state.clear()
    await message.answer(
        "Спасибо за отзыв!",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    logger.info("User %d sent feedback", user_id)
