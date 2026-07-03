"""Sesión SQLAlchemy async hacia BD Dedicated en provisioning (PR-F4-07)."""

from __future__ import annotations



from contextlib import asynccontextmanager

from typing import AsyncIterator

from urllib.parse import quote_plus



from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine



from app.core.config import settings

from app.core.exceptions import DatabaseError, ValidationError

from app.infrastructure.provisioning.dedicated_ddl_client import (

    validate_provisioning_ddl_settings,

)





def build_provisioning_sqlalchemy_url(*, database_name: str) -> str:

    validate_provisioning_ddl_settings()

    user = quote_plus(settings.PROVISIONING_DDL_USER)

    password = quote_plus(settings.PROVISIONING_DDL_PASSWORD)

    server = settings.PROVISIONING_DDL_SERVER

    port = settings.PROVISIONING_DDL_PORT

    db = quote_plus(database_name)

    driver = quote_plus(settings.DB_DRIVER)

    return (

        f"mssql+aioodbc://{user}:{password}@{server}:{port}/{db}"

        f"?driver={driver}&TrustServerCertificate=yes"

    )





@asynccontextmanager

async def provisioning_dedicated_session(

    database_name: str,

) -> AsyncIterator[AsyncSession]:

    if not settings.PROVISIONING_DDL_EXECUTOR_ENABLED:

        raise ValidationError(

            detail=(

                "Sesión provisioning dedicated deshabilitada "

                "(PROVISIONING_DDL_EXECUTOR_ENABLED=false)."

            ),

            internal_code="PROVISIONING_DDL_EXECUTOR_DISABLED",

        )

    engine = create_async_engine(

        build_provisioning_sqlalchemy_url(database_name=database_name),

        pool_pre_ping=True,

    )

    try:

        async with AsyncSession(engine, expire_on_commit=False) as session:

            async with session.begin():

                yield session

    except ValidationError:

        raise

    except Exception as exc:

        raise DatabaseError(

            detail="No se pudo abrir sesión provisioning en BD dedicada.",

            internal_code="PROVISIONING_DEDICATED_SESSION_FAILED",

        ) from exc

    finally:

        await engine.dispose()





__all__ = [

    "build_provisioning_sqlalchemy_url",

    "provisioning_dedicated_session",

]

