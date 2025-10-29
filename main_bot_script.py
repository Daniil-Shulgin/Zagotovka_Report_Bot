import asyncio
import logging
import time
import sys
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart

from sheets_data_loader_and_analysis import report_week, compare_year_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = '8336463112:AAFa57WQU1Vi8PVWoyOHgSN_PVMhPt1INSQ'
dp = Dispatcher()

# --- HANDLERS ---

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обрабатывает команду /start."""
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name

    buttons = [
        [InlineKeyboardButton(text="📈 Отчет за прошлую неделю", callback_data="report_week")],
        [InlineKeyboardButton(text="📊 Сравнение заготовки (2022-2025)", callback_data="compare_year_report")]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    logging.info(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] User started bot: ID={user_id}, Name={user_full_name}')

    await message.reply(
        f'Привет, {user_full_name}!\n'
        f'Я — бот для отправки отчетов о заготовке зерна.\n'
        f'Какой отчет нужен?',
        reply_markup=keyboard
    )

# Обработка кнопки [report_week]   

@dp.callback_query(F.data == "report_week")
async def callback_report_week(callback: CallbackQuery) -> None:
    """Обрабатывает нажатие кнопки 'report_week'."""
    buttons = [
        [InlineKeyboardButton(text="Обновить отчет", callback_data="report_week")]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        report_data = report_week()

        if 'error' in report_data:
            await callback.message.answer(f"❌ Ошибка: {report_data['error']}")
            return

        chart_bytes = report_data['chart_bytes']
        cahrt_1 = BufferedInputFile(chart_bytes, filename="weekly_report.png")

        metrics_data = report_data['metrics']
        current_delta_date = metrics_data['current_delta_date']
        ttl_trg_w = metrics_data['ttl_trg_w']
        Safonov_trg_w = metrics_data['Safonov_trg_w']
        Grushin_trg_w = metrics_data['Grushin_trg_w']
        Katishev_trg_w = metrics_data['Katishev_trg_w']

        await callback.message.answer_photo(
            photo=cahrt_1,
            caption=f"📈 Отчет за прошлую неделю: {current_delta_date}\n"
            f"\nВсего за прошлую неделю купили: {ttl_trg_w} тонн.\n"
            f"Из них:\n"
            f"- Cафонов: {Safonov_trg_w}\n"
            f"- Грушин: {Grushin_trg_w}\n"
            f"- Катышев: {Katishev_trg_w}\n",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка в callback_report_week: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()

# Обработка кнопки [compare_year_report]   

@dp.callback_query(F.data == "compare_year_report")
async def callback_compare_year(callback: CallbackQuery) -> None:
    """Обрабатывает нажатие кнопки 'compare_year_report'."""
    buttons = [
        [InlineKeyboardButton(text="Обновить отчет", callback_data="compare_year_report")]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        chart_bytes = compare_year_report()

        if isinstance(chart_bytes, dict) and 'error' in chart_bytes:
            await callback.message.answer(f"❌ Ошибка при формировании графика: {chart_bytes['error']}")
            return

        cahrt_2 = BufferedInputFile(chart_bytes, filename="compare_year_report.png")

        await callback.message.answer_photo(
            photo=cahrt_2,
            caption=f"ℹ️ График сглажен.\n"
            f"Что это значит? - сглажены колебания.\n"
            f"Зачем? - так легче сравнивать.\n",
            reply_markup=keyboard
        )

    except Exception as e:
        logging.error(f"Ошибка в callback_compare_year_report: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()

# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА ---

async def main() -> None:
    bot = Bot(token=TOKEN)

    logging.info("Запуск Zagotovka_Report_Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен вручную.")

