import logging
from typing import TYPE_CHECKING

from aiogram import Router, filters, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import decode_payload

if TYPE_CHECKING:
    from app.services import Storage

logger = logging.getLogger(__name__)

router = Router(name=__name__)


class Filter(StatesGroup):
    filter = State()


@router.message(filters.CommandStart())
async def start_handler(
    message: types.Message, command: filters.CommandObject, storage: "Storage"
):
    if not message.from_user:
        return

    user_id = message.from_user.id
    args = decode_payload(command.args) if command.args else None

    await storage.subscribe(str(user_id), args)

    msg = "Вы подписались на уведомления об отключениях" + (
        " на улице " + args
        if args
        else (
            ".\r\n"
            "Чтобы получать уведомления только по конкретной улице, "
            "введите команду /filter"
        )
    )
    await message.answer(msg)

    logger.info("User %d subscribed to updates", user_id)


@router.message(filters.Command("stop"))
async def stop_handler(message: types.Message, storage: "Storage"):
    if not message.from_user:
        return

    user_id = message.from_user.id
    await storage.unsubscribe(str(user_id))
    await message.answer("Вы отписались от уведомлений об отключениях")

    logger.info("User %d unsubscribed from updates", user_id)


@router.message(filters.Command("filter"))
async def filter_handler(message: types.Message, storage: "Storage", state: FSMContext):
    if not message.from_user:
        return

    f = await storage.get_filter(str(message.from_user.id))

    await state.set_state(Filter.filter)
    await message.answer(
        "Пожалуйста, введите наименование улицы, по которой интересны уведомления."
        + (f" Текущее значение: {f.street}" if f.street else ""),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Отмена")]],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )


@router.message(Filter.filter, F.text == "Отмена")
async def filter_cancel_handler(
    message: types.Message, state: FSMContext, storage: "Storage"
):
    if not message.from_user:
        return

    await state.clear()

    f = await storage.get_filter(str(message.from_user.id))
    await message.answer(
        (
            f"Вы подписаны на уведомления для улицы {f.street}"
            if f.street
            else "Вы подписаны на все уведомления"
        ),
        reply_markup=types.ReplyKeyboardRemove(),
    )


@router.message(Filter.filter, ~F.text.startswith("/"))
async def filter_value_handler(
    message: types.Message, storage: "Storage", state: FSMContext
):
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id
    value = message.text.strip()

    await storage.subscribe(str(user_id), value)
    # await storage.set_filter(str(user_id), message.text)

    await state.clear()
    await message.answer(
        "Вы подписаны на уведомления для улицы " + value,
        reply_markup=types.ReplyKeyboardRemove(),
    )
