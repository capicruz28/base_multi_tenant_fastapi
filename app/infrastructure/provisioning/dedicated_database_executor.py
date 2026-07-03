"""

DedicatedDatabaseExecutor — DDL físico SQL Server (PR-F4-04 / Q-061).



S3 saga: CREATE DATABASE + login SQL app + grants mínimos.

Desacoplado — consumo exclusivo por orchestrator F4-08.

"""

from __future__ import annotations



import logging

import re

from typing import Optional



from app.core.config import settings

from app.core.exceptions import ConflictError, DatabaseError, ValidationError

from app.core.security.password_generator import generar_contrasena_segura

from app.infrastructure.provisioning.dedicated_database_naming import (

    assert_sql_identifier,

    build_dedicated_app_login_name,

    build_dedicated_database_name,

    escape_sql_literal,

    quote_sql_identifier,

)

from app.infrastructure.provisioning.dedicated_database_types import (

    DedicatedDatabaseDropRequest,

    DedicatedDatabaseDropResult,

    DedicatedDatabaseProvisionRequest,

    DedicatedDatabaseProvisionResult,

)

from app.infrastructure.provisioning.dedicated_ddl_client import (

    DedicatedDdlClient,

    DedicatedDdlSession,

    create_default_ddl_client,

)



logger = logging.getLogger(__name__)



_DUPLICATE_DB_RE = re.compile(

    r"(already exists|exist.*database|1801|1927)",

    re.IGNORECASE,

)

_DUPLICATE_LOGIN_RE = re.compile(

    r"(already exists|exist.*login|15025|15023)",

    re.IGNORECASE,

)





class DedicatedDatabaseExecutor:

    """Ejecutor DDL platform segregado (ADR-F4-01)."""



    def __init__(self, ddl_client: Optional[DedicatedDdlClient] = None) -> None:

        self._ddl = ddl_client



    def _client(self) -> DedicatedDdlClient:

        if self._ddl is not None:

            return self._ddl

        return create_default_ddl_client()



    @staticmethod

    def _resolve_server(request: DedicatedDatabaseProvisionRequest) -> str:

        server = request.servidor or settings.PROVISIONING_DDL_SERVER

        if not server:

            raise ValidationError(

                detail="servidor SQL no configurado para provisioning DDL.",

                internal_code="PROVISIONING_DDL_SERVER_MISSING",

            )

        return server



    async def database_exists(self, database_name: str) -> bool:

        async with self._client().open_session(database="master") as session:

            return await self._database_exists(session, database_name)



    async def login_exists(self, login_name: str) -> bool:

        async with self._client().open_session(database="master") as session:

            return await self._login_exists(session, login_name)



    @staticmethod

    async def _database_exists(session: DedicatedDdlSession, database_name: str) -> bool:

        assert_sql_identifier(database_name, field="database_name")

        quoted = escape_sql_literal(database_name)

        db_id = await session.scalar_int(f"SELECT DB_ID(N'{quoted}')")

        return db_id is not None



    @staticmethod

    async def _login_exists(session: DedicatedDdlSession, login_name: str) -> bool:

        assert_sql_identifier(login_name, field="app_login_name")

        quoted = escape_sql_literal(login_name)

        sid = await session.scalar_int(f"SELECT SUSER_ID(N'{quoted}')")

        return sid is not None



    async def provision_physical_database(

        self,

        request: DedicatedDatabaseProvisionRequest,

    ) -> DedicatedDatabaseProvisionResult:

        """

        Idempotente: re-ejecución no falla si BD/login ya existen.



        No registra ``cliente_conexion`` — S8/F4-09.

        """

        database_name = request.database_name or build_dedicated_database_name(

            request.codigo_cliente,

            cliente_id=request.cliente_id,

        )

        login_name = request.app_login_name or build_dedicated_app_login_name(

            request.codigo_cliente,

            cliente_id=request.cliente_id,

        )

        login_password = request.app_login_password or generar_contrasena_segura(16)

        servidor = self._resolve_server(request)



        async with self._client().open_session(database="master") as session:

            db_exists_before = await self._database_exists(session, database_name)

            login_exists_before = await self._login_exists(session, login_name)



            database_created = False

            if not db_exists_before:

                await self._create_database(session, database_name)

                database_created = True

            else:

                logger.info(

                    "Dedicated DB already exists cliente_id=%s database=%s",

                    request.cliente_id,

                    database_name,

                )



            login_created = False

            if not login_exists_before:

                await self._create_login(session, login_name, login_password)

                login_created = True

            else:

                logger.info(

                    "Dedicated login already exists cliente_id=%s login=%s",

                    request.cliente_id,

                    login_name,

                )



            await self._ensure_database_user(session, database_name, login_name)



        return DedicatedDatabaseProvisionResult(

            cliente_id=request.cliente_id,

            servidor=servidor,

            database_name=database_name,

            app_login_name=login_name,

            app_login_password=login_password,

            database_created=database_created,

            login_created=login_created,

            database_already_existed=db_exists_before,

            login_already_existed=login_exists_before,

        )



    @staticmethod

    async def _create_database(session: DedicatedDdlSession, database_name: str) -> None:

        quoted_db = quote_sql_identifier(database_name)

        collation = settings.PROVISIONING_DEDICATED_DB_COLLATION

        if not re.fullmatch(r"[A-Za-z0-9_]+", collation or ""):

            raise ValidationError(

                detail="PROVISIONING_DEDICATED_DB_COLLATION inválida.",

                internal_code="INVALID_DEDICATED_COLLATION",

            )

        sql = f"CREATE DATABASE {quoted_db} COLLATE {collation};"

        try:

            await session.execute(sql)

        except DatabaseError as exc:

            cause_text = str(exc.__cause__ or exc.detail or "")

            if _DUPLICATE_DB_RE.search(cause_text):

                logger.info("CREATE DATABASE race/idempotent database=%s", database_name)

                return

            raise ConflictError(

                detail="No se pudo crear la base de datos dedicada.",

                internal_code="DEDICATED_DB_CREATE_FAILED",

            ) from exc



    @staticmethod

    async def _create_login(

        session: DedicatedDdlSession,

        login_name: str,

        password: str,

    ) -> None:

        quoted_login = quote_sql_identifier(login_name)

        escaped_password = escape_sql_literal(password)

        sql = (

            f"CREATE LOGIN {quoted_login} WITH PASSWORD = N'{escaped_password}', "

            f"CHECK_POLICY = ON, CHECK_EXPIRATION = OFF;"

        )

        try:

            await session.execute(sql)

        except DatabaseError as exc:

            cause_text = str(exc.__cause__ or exc.detail or "")

            if _DUPLICATE_LOGIN_RE.search(cause_text):

                logger.info("CREATE LOGIN race/idempotent login=%s", login_name)

                return

            raise ConflictError(

                detail="No se pudo crear el login SQL de la BD dedicada.",

                internal_code="DEDICATED_LOGIN_CREATE_FAILED",

            ) from exc



    @staticmethod

    async def _ensure_database_user(

        session: DedicatedDdlSession,

        database_name: str,

        login_name: str,

    ) -> None:

        quoted_db = quote_sql_identifier(database_name)

        quoted_login = quote_sql_identifier(login_name)

        escaped_login = escape_sql_literal(login_name)



        batch = f"""

USE {quoted_db};

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'{escaped_login}')

    CREATE USER {quoted_login} FOR LOGIN {quoted_login};

IF IS_ROLEMEMBER('db_owner', N'{escaped_login}') = 0

    ALTER ROLE db_owner ADD MEMBER {quoted_login};

"""

        try:

            await session.execute(batch)

        except DatabaseError as exc:

            raise ConflictError(

                detail="No se pudo provisionar usuario/grants en BD dedicada.",

                internal_code="DEDICATED_DB_USER_GRANT_FAILED",

            ) from exc



    async def drop_physical_database(

        self,

        request: DedicatedDatabaseDropRequest,

    ) -> DedicatedDatabaseDropResult:

        """

        Compensación S3 — DROP DATABASE y login SQL app (idempotente).



        Solo invocar cuando ``provisioning_state=failed`` (guard en compensation service).

        """

        database_name = request.database_name

        login_name = request.app_login_name

        assert_sql_identifier(database_name, field="database_name")

        assert_sql_identifier(login_name, field="app_login_name")



        async with self._client().open_session(database="master") as session:

            db_existed = await self._database_exists(session, database_name)

            login_existed = (

                await self._login_exists(session, login_name)

                if request.drop_login

                else False

            )



            database_dropped = False

            if db_existed:

                await self._drop_database(session, database_name)

                database_dropped = True

            else:

                logger.info(

                    "DROP DATABASE idempotent skip — database absent cliente_id=%s db=%s",

                    request.cliente_id,

                    database_name,

                )



            login_dropped = False

            if request.drop_login:

                if login_existed:

                    await self._drop_login(session, login_name)

                    login_dropped = True

                else:

                    logger.info(

                        "DROP LOGIN idempotent skip — login absent cliente_id=%s login=%s",

                        request.cliente_id,

                        login_name,

                    )



        return DedicatedDatabaseDropResult(

            cliente_id=request.cliente_id,

            database_name=database_name,

            app_login_name=login_name,

            database_existed=db_existed,

            database_dropped=database_dropped,

            login_existed=login_existed,

            login_dropped=login_dropped,

        )



    @staticmethod

    async def _drop_database(session: DedicatedDdlSession, database_name: str) -> None:

        quoted_db = quote_sql_identifier(database_name)

        sql = f"DROP DATABASE {quoted_db};"

        try:

            await session.execute(sql)

        except DatabaseError as exc:

            raise ConflictError(

                detail="No se pudo eliminar la base de datos dedicada.",

                internal_code="DEDICATED_DB_DROP_FAILED",

            ) from exc



    @staticmethod

    async def _drop_login(session: DedicatedDdlSession, login_name: str) -> None:

        quoted_login = quote_sql_identifier(login_name)

        sql = f"DROP LOGIN {quoted_login};"

        try:

            await session.execute(sql)

        except DatabaseError as exc:

            raise ConflictError(

                detail="No se pudo eliminar el login SQL de la BD dedicada.",

                internal_code="DEDICATED_LOGIN_DROP_FAILED",

            ) from exc





__all__ = ["DedicatedDatabaseExecutor"]


