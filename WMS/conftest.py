"""
Configuração global de testes para o módulo WMS
Fixtures compartilhadas para todos os testes
"""

import pytest
import pytest_asyncio
import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from wms.infrastructure.database import get_async_session, Base
from wms.infrastructure import models as _all_models  # noqa: F401
from wms.interfaces.api_xml_analise import router
from wms.application.xml_analise_service import XMLAnaliseService
from tests._sync_asgi_client import SyncASGITestClient

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback quando dotenv nao estiver instalado
    load_dotenv = None

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parent / ".env")


# Configuração de banco de dados para testes
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv(
        "ASYNC_DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            os.getenv(
                "WMS_POSTGRES_DSN",
                "postgresql+asyncpg://wms:wms@localhost:5432/wms",
            ),
        ),
    ),
)

# Engine assíncrono para testes
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"timeout": 5},
)

# Session factory para testes
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

USE_EXISTING_SCHEMA = os.getenv(
    "WMS_TEST_USE_EXISTING_SCHEMA",
    "true",
).strip().lower() in {"1", "true", "yes", "on"}

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Cria uma sessão de banco de dados para testes.
    Usa um banco separado para não afetar os dados de desenvolvimento.
    """
    # Criar engine de teste
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        connect_args={"timeout": 5},
    )
    
    # Criar session factory
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    if not USE_EXISTING_SCHEMA:
        # Criar tabelas somente quando o ambiente nao fornece schema pronto.
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    # Criar e yield da sessão
    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        
        if not USE_EXISTING_SCHEMA:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client() -> Generator[SyncASGITestClient, None, None]:
    """
    Fixture que fornece um cliente de teste FastAPI
    """
    from fastapi import FastAPI
    from fastapi import HTTPException
    from fastapi.encoders import jsonable_encoder
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(_, exc: RequestValidationError):
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = first_error.get("loc", ["payload"])[-1]
            mensagem = f"{field}: {first_error.get('msg', 'Payload inválido')}"
        else:
            mensagem = "Payload inválido"
        return JSONResponse(
            status_code=422,
            content={
                "erro": "VALIDATION_ERROR",
                "mensagem": mensagem,
                "detalhes": jsonable_encoder(errors),
            },
        )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(_, exc: HTTPException):
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "erro": "HTTP_ERROR",
                "mensagem": str(exc.detail),
            },
        )
    
    with SyncASGITestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def xml_service(db_session: AsyncSession) -> XMLAnaliseService:
    """
    Fixture que fornece uma instância do serviço de análise XML
    """
    return XMLAnaliseService(db_session)


@pytest.fixture(scope="function")
def sample_tenant_id() -> str:
    """ID de tenant para testes"""
    return str(uuid4())


@pytest.fixture(scope="function")
def sample_fornecedor_id() -> str:
    """ID de fornecedor para testes"""
    return "98765432109876"


@pytest.fixture(scope="function")
def sample_xml_content() -> str:
    """XML NF-e de exemplo para testes"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
        <infNFe versao="4.00" Id="NFe43210678901234567890123456789012345678">
            <ide>
                <cUF>35</cUF>
                <cNF>123456</cNF>
                <natOp>VENDA</natOp>
                <mod>55</mod>
                <serie>501</serie>
                <nNF>123456</nNF>
                <dhEmi>2023-12-25T10:30:00-03:00</dhEmi>
                <tpNF>1</tpNF>
                <idDest>1</idDest>
                <cMunFG>3550308</cMunFG>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <cDV>2</cDV>
                <tpAmb>1</tpAmb>
                <finNFe>1</finNFe>
                <indFinal>1</indFinal>
                <indPres>0</indPres>
                <procEmi>0</procEmi>
                <verProc>4.00</verProc>
            </ide>
            <emit>
                <CNPJ>98765432109876</CNPJ>
                <xNome>DISTRIBUIDORA SOLAR DE BEBIDAS LTDA</xNome>
                <xFant>Solar Distribuidora</xFant>
                <enderEmit>
                    <xLgr>Rua das Bebidas</xLgr>
                    <nro>123</nro>
                    <xBairro>Centro</xBairro>
                    <xMun>São Paulo</xMun>
                    <UF>SP</UF>
                    <CEP>01234567</CEP>
                    <cPais>1058</cPais>
                    <xPais>Brasil</xPais>
                </enderEmit>
            </emit>
            <det nItem="1">
                <prod>
                    <cProd>COCA-COLA-2L-PET</cProd>
                    <cEAN>7894900010237</cEAN>
                    <xProd>Refrigerante Coca-Cola 2L PET</xProd>
                    <NCM>22021000</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>10.0000</qCom>
                    <vUnCom>8.50</vUnCom>
                    <vProd>85.00</vProd>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>"""


@pytest.fixture(scope="function")
def invalid_xml_content() -> str:
    """XML inválido para testes de validação"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00">
    <NFe>
        <infNFe>
            <!-- XML malformado - tags não fechadas -->
            <ide>
                <cUF>35</cUF>
                <cNF>123456
            </ide>
        </infNFe>
    </NFe>"""


# Configuração do pytest-asyncio
def pytest_configure(config):
    """Configuração do pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test to run with asyncio"
    )


@pytest.fixture(scope="session")
def anyio_backend():
    """Backend para pytest-anyio"""
    return "asyncio"
