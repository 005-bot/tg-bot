import logging
from typing import TYPE_CHECKING

from address_parser import AddressParser, Match
from aiogram import F, Router, filters, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import decode_payload

if TYPE_CHECKING:
    from app.admin import Notificator
    from app.services import Storage

logger = logging.getLogger(__name__)

router = Router(name=__name__)


class Filter(StatesGroup):
    filter = State()


@router.message(filters.CommandStart())
async def start_handler(
    message: types.Message,
    command: filters.CommandObject,
    state: FSMContext,
    storage: "Storage",
    notificator: "Notificator",
    address_parser: AddressParser,
):
    if not message.from_user:
        return

    user_id = message.from_user.id
    args = decode_payload(command.args) if command.args else None

    await storage.subscribe(str(user_id), None)
    parsed = await parse_and_subscribe(args, message, storage, state, address_parser)
    if args and not parsed:
        return

    base = "Вы подписались на уведомления об отключениях"
    if parsed:
        details = f" по адресу {parsed.name}"
    else:
        details = (
            ".\r\n"
            "Чтобы получать уведомления только по конкретной улице, "
            "введите команду /filter"
        )
    msg = (
        f"{base}{details}\n\n"
        "Источник информации об отключениях: https://005красноярск.рф"
    )
    await message.answer(msg)

    logger.info("User %d subscribed to updates", user_id)

    await notificator.new_user(message.from_user)


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
        + (f"\n\nТекущее значение: {f.street}" if f.street else ""),
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
            f"Вы подписаны на уведомления для {f.street}"
            if f.street
            else "Вы подписаны на все уведомления"
        ),
        reply_markup=types.ReplyKeyboardRemove(),
    )


@router.message(Filter.filter, ~F.text.startswith("/"))
async def filter_value_handler(
    message: types.Message,
    storage: "Storage",
    state: FSMContext,
    address_parser: AddressParser,
):
    parsed = await parse_and_subscribe(
        message.text, message, storage, state, address_parser
    )
    if not parsed:
        return

    await state.clear()
    await message.answer(
        "Создана подписка: " + parsed.name,
        reply_markup=types.ReplyKeyboardRemove(),
    )


async def parse_and_subscribe(
    value: str | None,
    message: types.Message,
    storage: "Storage",
    state: FSMContext,
    address_parser: AddressParser,
) -> Match | None:
    if not message.from_user or not value:
        return

    user_id = message.from_user.id
    value = value.strip()

    parsed = await address_parser.normalize(value)
    if not parsed:
        await state.set_state(Filter.filter)
        await message.answer(
            "Не удалось определить улицу. Пожалуйста, укажите наименование без дополнительных слов, "
            "например: 'Ленина' или 'Мира'"
        )
        return

    if parsed.confidence < 0.85:
        await state.set_state(Filter.filter)
        await message.answer(
            f"Вы имели в виду {parsed.name}?\n\nИспользуйте кнопку для подтверждения или введите другой вариант.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text=parsed.name)],
                    [types.KeyboardButton(text="Отмена")],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return

    await storage.subscribe(str(user_id), parsed.name)

    return parsed
