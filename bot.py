# bot.py
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import User, engine, Notification, Session

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота
TOKEN = "TOKKKKEN"

# Создание сессии
Session = sessionmaker(bind=engine)

# Планировщик уведомлений
scheduler = AsyncIOScheduler()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start."""
    user = update.effective_user
    session = Session()
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    
    if not db_user:
        db_user = User(telegram_id=user.id, username=user.username or 'NoName')
        session.add(db_user)
        session.commit()
        
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\n"
        "Я бот, который поможет тебе съесть сосиски."
    )
    session.close()

async def sosiska(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /eat_sausage."""
    user = update.effective_user
    session = Session()
    db_user = session.query(User).filter_by(telegram_id=user.id).first()

    if db_user:
        db_user.sausages_eaten += 1
        session.commit()
        await update.message.reply_text(
            f"🌭 Ты съел сосиску! Теперь у тебя {db_user.sausages_eaten} сосисок."
        )
    else:
        await update.message.reply_text("Пожалуйста, сначала используй команду /start.")
        
    session.close()

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает таблицу лидеров по съеденным сосискам."""
    session = Session()
    top_users = session.query(User).order_by(User.sausages_eaten.desc()).limit(10).all()
    
    if not top_users:
        await update.message.reply_text("Пока ещё никто не ел сосиски. Будь первым!")
        return

    message_text = "🏆 **Таблица лидеров по сосискам** 🏆\n\n"
    for i, user in enumerate(top_users):
        message_text += f"{i+1}. {user.username or 'NoName'} — {user.sausages_eaten} 🌭\n"

    await update.message.reply_text(message_text)
    session.close()

# Функция для отправки уведомлений
async def send_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет уведомление всем пользователям."""
    session = Session()
    users = session.query(User).all()
    
    for user in users:
        try:
            # Отправляем сообщение
            await context.bot.send_message(user.telegram_id, "🔔 Это запланированное уведомление!")
            # Логируем отправку
            logger.info(f"Отправлено уведомление пользователю {user.username} ({user.telegram_id})")
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление пользователю {user.username} ({user.telegram_id}): {e}")
    
    session.close()

# Запуск планировщика
def run_scheduler() -> None:
    """Запускает планировщик задач."""
    # Запланировать отправку уведомлений, например, каждые 24 часа
    scheduler.add_job(send_notification, 'interval', hours=24)
    scheduler.start()

def main() -> None:
    """Основная функция для запуска бота."""
    application = Application.builder().token(TOKEN).build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sosiska", sosiska)) # <-- ИЗМЕНЕНО НА /sosiska
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    
    # Запуск планировщика уведомлений с помощью встроенного job_queue
    # Уведомление будет отправляться каждые 24 часа
    application.job_queue.run_repeating(send_notification_job, interval=timedelta(hours=24)) # <-- ИЗМЕНЕНО ЗДЕСЬ
    
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def send_notification_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Эта функция будет вызываться job_queue и передавать 'context'.
    Она вызывает оригинальную функцию send_notification.
    """
    await send_notification(context)
    
async def send_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет уведомление всем пользователям."""
    session = Session()
    users = session.query(User).all()
    
    for user in users:
        try:
            await context.bot.send_message(user.telegram_id, "🔔 Это запланированное уведомление!")
            logger.info(f"Отправлено уведомление пользователю {user.username} ({user.telegram_id})")
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление пользователю {user.username} ({user.telegram_id}): {e}")
    
    session.close()

if __name__ == '__main__':
    main()
