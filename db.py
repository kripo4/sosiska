# db.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Подключение к базе данных (создаем файл sausage_bot.db)
engine = create_engine('sqlite:///sausage_bo.db')
Base = declarative_base()

# Определение модели пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    sausages_eaten = Column(Integer, default=0)
    
# Определение модели уведомлений
class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    message = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)

# Создание таблицы в базе данных
Base.metadata.create_all(engine)

# Создание сессии для работы с базой данных
Session = sessionmaker(bind=engine)
