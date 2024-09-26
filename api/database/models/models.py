# coding: utf-8
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Chain(Base):
    __tablename__ = 'chains'
    __table_args__ = {'schema': 'public', 'comment': 'список цепочек примитивов датасетов'}

    id = Column(UUID, primary_key=True, comment='ID цепочки')
    name = Column(String(64), comment='наименование цепочки')
    dataset_id = Column(UUID, comment='ID датасета')
    vector = Column(Text, comment='векторное описание цепочки (из выходных файлов ИНС, если есть)')
    description = Column(Text, comment='описание цепочки')
    author_id = Column(UUID, comment='ID создателя цепочки (если это не ИНС)')
    dt_created = Column(DateTime, comment='дата и время создания цепочки')
    is_deleted = Column(Boolean, comment='признак удаления цепочки')


class Dataset(Base):
    __tablename__ = 'datasets'
    __table_args__ = {'schema': 'public', 'comment': 'Список датасетов проектов'}

    id = Column(UUID, primary_key=True, comment='ID датасета')
    name = Column(String(64), comment='наименование датасета')
    type_id = Column(Integer, comment='тип датасета (enum: 0 – начальный, 1 – контуры, 2 – скелеты, 3 – субконтуры и пр.)')
    parent_id = Column(UUID, comment='ID исходного датасета (если не заполнен, то это начальный датасет)')
    project_id = Column(UUID, comment='ID проекта')
    source = Column(Text, comment='ссылка на удаленное хранилище файлов начального датасета (внешнее хранилище, URL)')
    nn_original = Column(String(64), comment='хэш Docker-образа исходной ИНС')
    nn_online = Column(String(64), comment='хэш Docker-контейнера работающей ИНС (для получения состояния и статистики при расчете, очищается после работы)')
    nn_teached = Column(String(64), comment='хэш Docker-образа обученной ИНС (только при обучении)')
    description = Column(Text, comment='описание датасета')
    author_id = Column(UUID, comment='ID создателя датасета')
    dt_created = Column(DateTime, comment='дата и время создания датасета')
    dt_calculated = Column(DateTime, comment='дата и время расчета датасета')
    is_calculated = Column(Boolean, comment='признак «рассчитанного» датасета')
    is_deleted = Column(Boolean, comment='признак удаления датасета')


class File(Base):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'public', 'comment': 'список файлов датасетов проектов'}

    id = Column(UUID, primary_key=True, comment='ID датасета')
    name = Column(String(64), comment='наименование файла')
    label = Column(String(64), comment='пользовательская метка файла')
    dataset_id = Column(UUID, comment='ID датасета')
    thumbnail = Column(String(64), comment='ссылка на иконку файла')
    description = Column(Text, comment='описание датасета')
    attributes = Column(JSON, comment='атрибуты файла (длительность, камера, кодек и пр.)')
    author_id = Column(UUID, comment='ID пользователя, загрузившего файл')
    dt_created = Column(DateTime, comment='дата и время создания (записи) файла')
    dt_uploaded = Column(DateTime, comment='дата и время загрузки файла')
    is_marked = Column(Boolean, comment='признак «размеченного» файла (для обучения)')
    is_deleted = Column(Boolean, comment='признак удаления файла')


class Markup(Base):
    __tablename__ = 'markups'
    __table_args__ = {'schema': 'public', 'comment': 'Список примитивов датасетов'}

    id = Column(UUID, primary_key=True, comment='ID примитива')
    previous_id = Column(UUID, comment='ID исходного примитива, заполняется для скорректированного примитива')
    dataset_id = Column(UUID, comment='ID датасета')
    file_id = Column(UUID, comment='ID файла датасета, откуда примитив извлечен')
    parent_id = Column(UUID, comment='ID примитива входного датасета, откуда примитив извлечен')
    mark_time = Column(Integer, comment='момент извлечения примитива (момент времени в файле исходного датасета)')
    mark_path = Column(JSON, comment='графический контур (или скелет) примитива (координаты кадра в файле исходного датасета, цвет и пр.)')
    vector = Column(Text, comment='векторное описание примитива (из выходных файлов ИНС, если есть)')
    description = Column(Text, comment='описание примитива')
    author_id = Column(UUID, comment='ID создателя примитива (если это не ИНС)')
    dt_created = Column(DateTime, comment='дата и время создания примитива')
    is_deleted = Column(Boolean, comment='признак удаления примитива')


class Privilege(Base):
    __tablename__ = 'privileges'
    __table_args__ = {'schema': 'public', 'comment': 'список прав пользователей системы'}

    code = Column(String(32), primary_key=True, comment='код права (используется в скриптах бэкенда)')
    name = Column(String(255), comment='имя права')

    roles = relationship('Role', secondary='public.roles_privileges')


t_project_tags = Table(
    'project_tags', metadata,
    Column('project_id', UUID, nullable=False, comment='ID проекта'),
    Column('tag', String(64), comment='Тэг'),
    schema='public',
    comment='Список тегов проектов (опционально, для систематизации проектов)'
)


class Project(Base):
    __tablename__ = 'projects'
    __table_args__ = {'schema': 'public', 'comment': 'Список проектов'}

    id = Column(UUID, primary_key=True, comment='ID проекта')
    name = Column(String(255), comment='наименование проекта')
    type_id = Column(Integer, comment='тип проекта (enum: 0 – обучение, 1 - оценка)')
    description = Column(Text, comment='описание проекта')
    author_id = Column(UUID, nullable=False, comment='ID создателя проекта')
    dt_created = Column(DateTime, comment='дата и время создания проекта')
    is_deleted = Column(Boolean, comment='признак удаления проекта')

    users = relationship('User', secondary='public.project_users')


class Role(Base):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'public', 'comment': 'Список ролей пользователей системы'}

    code = Column(String(16), primary_key=True, comment='код роли')
    name = Column(String(32), nullable=False, comment='имя роли')


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public', 'comment': 'Список пользователей системы'}

    id = Column(UUID, primary_key=True, comment='ID пользователя')
    name = Column(String(64), comment='имя пользователя')
    role_code = Column(String(64), comment='код роли')
    login = Column(String, comment='логин пользователя')
    password = Column(String, comment='хэш пароля пользователя')
    description = Column(Text, comment='описание пользователя')
    is_deleted = Column(Boolean, comment='признак удаления пользователя')


t_markups_chains = Table(
    'markups_chains', metadata,
    Column('chain_id', ForeignKey('public.chains.id'), comment='ID цепочки'),
    Column('markup_id', ForeignKey('public.markups.id'), comment='ID примитива (при коррекции примитива его ID в цепочке должен подменяться)'),
    Column('npp', Integer, comment='порядковый номер примитива в цепочке'),
    schema='public'
)


t_project_users = Table(
    'project_users', metadata,
    Column('project_id', ForeignKey('public.projects.id')),
    Column('user_id', ForeignKey('public.users.id')),
    schema='public',
    comment='Список пользователей системы'
)


t_roles_privileges = Table(
    'roles_privileges', metadata,
    Column('role_code', ForeignKey('public.roles.code'), nullable=False, comment='Код роли'),
    Column('privilege_code', ForeignKey('public.privileges.code'), nullable=False, comment='Код права'),
    schema='public',
    comment='Список привязок прав к ролям пользователей'
)


t_sessions = Table(
    'sessions', metadata,
    Column('user_id', ForeignKey('public.users.id'), comment='ID пользователя'),
    Column('token', String(256), comment='токен сессии пользователя'),
    Column('dt_start', DateTime, comment='начало сессии'),
    Column('life', Integer, comment='длительность сессии, минут'),
    Column('is_ended', Boolean, comment='признак конца действия токена'),
    schema='public'
)
