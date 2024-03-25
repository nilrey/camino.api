
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'common', 'comment': 'Список пользователей системы'}

    id = Column(UUID, primary_key=True, comment='ID пользователя')
    name = Column(String(64), comment='имя пользователя')
    role_code = Column(String(64), comment='код роли')
    login = Column(String, comment='логин пользователя')
    password = Column(String, comment='хэш пароля пользователя')
    description = Column(Text, comment='описание пользователя')
    is_deleted = Column(Boolean, comment='признак удаления пользователя')
