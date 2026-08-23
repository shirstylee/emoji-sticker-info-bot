from __future__ import annotations

import asyncio
import logging
import signal
import sys
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from .config import Config
from .db import Database
from .exports import ExportStore
from .handlers import router
from .security import RequestProtection


async def _stop_on_windows_signal(
    dispatcher: Dispatcher, shutdown_requested: asyncio.Event
) -> None:
    await shutdown_requested.wait()
    while True:
        try:
            await dispatcher.stop_polling()
            return
        except RuntimeError:
            # Ctrl+C may arrive a fraction of a second before polling acquires its lock.
            await asyncio.sleep(0.05)


async def main() -> None:
    config = Config.from_env()
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    database = Database(config.db_path)
    await database.connect()
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    export_store = ExportStore()
    protection = RequestProtection()

    shutdown_requested: asyncio.Event | None = None
    shutdown_watcher: asyncio.Task[None] | None = None
    previous_sigint = None
    if sys.platform == "win32":
        shutdown_requested = asyncio.Event()
        loop = asyncio.get_running_loop()
        previous_sigint = signal.getsignal(signal.SIGINT)
        interrupt_count = 0

        def handle_sigint(signum: int, frame: object) -> None:
            nonlocal interrupt_count
            interrupt_count += 1
            if interrupt_count > 1 and callable(previous_sigint):
                previous_sigint(signum, frame)
                return
            loop.call_soon_threadsafe(shutdown_requested.set)

        signal.signal(signal.SIGINT, handle_sigint)

    try:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Главное меню"),
                BotCommand(command="settings", description="Настройки"),
                BotCommand(command="help", description="Помощь и примеры"),
            ]
        )
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Main menu"),
                BotCommand(command="settings", description="Settings"),
                BotCommand(command="help", description="Help and examples"),
            ],
            language_code="en",
        )
        if shutdown_requested is not None:
            shutdown_watcher = asyncio.create_task(
                _stop_on_windows_signal(dispatcher, shutdown_requested)
            )
        await dispatcher.start_polling(
            bot,
            db=database,
            exports=export_store,
            protection=protection,
            handle_signals=shutdown_requested is None,
            close_bot_session=False,
            tasks_concurrency_limit=50,
        )
    finally:
        if shutdown_watcher is not None:
            shutdown_watcher.cancel()
            with suppress(asyncio.CancelledError):
                await shutdown_watcher
        if previous_sigint is not None:
            signal.signal(signal.SIGINT, previous_sigint)
        await database.close()
        await bot.session.close()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # A second Ctrl+C is a forced stop and should still exit without a traceback.
        pass


if __name__ == "__main__":
    run()
