# smoke_test_factory.py — executar uma vez após o refactor completo
"""
Valida que execute_use_case injeta os repositórios corretos em cada use case.
Detecta erros de contrato que testes unitários não capturam.
Rodar: python3 smoke_test_factory.py
"""
import inspect

# Ajuste os imports conforme a estrutura real do projeto
from wms.application.use_cases.registrar_movimentacao_estoque import RegistrarMovimentacaoEstoque
from wms.application.use_cases.registrar_ajuste_estoque import RegistrarAjusteEstoque
from wms.application.use_cases.registrar_avaria_estoque import RegistrarAvariaEstoque
from wms.application.use_cases.registrar_recebimento import RegistrarRecebimento
from wms.application.use_cases.registrar_inventario_ciclico import RegistrarInventarioCiclico
from wms.application.use_cases.registrar_politica_kanban import RegistrarPoliticaKanban
from wms.application.use_cases.processar_curva_abcd import ProcessarCurvaABCD
from wms.application.use_cases.processar_giro_estoque import ProcessarGiroEstoque
from wms.application.use_cases.processar_sazonalidade_operacional import ProcessarSazonalidadeOperacional
from wms.application.use_cases.processar_governanca_orcamentaria import ProcessarGovernancaOrcamentaria

def verificar_contrato(use_case_class, repository_factories):
    """Compara parâmetros esperados pelo __init__ com o que a fábrica entrega."""
    params_esperados = set(inspect.signature(use_case_class.__init__).parameters.keys())
    params_esperados.discard("self")
    
    # Simula a lógica da execute_use_case inteligente
    params_entregues = set(repository_factories.keys())
    # Adiciona universais apenas se o use case pedir
    if 'estoque_repo' in params_esperados:
        params_entregues.add('estoque_repo')
    if 'publisher' in params_esperados:
        params_entregues.add('publisher')

    faltando = params_esperados - params_entregues
    sobrando = params_entregues - params_esperados

    if faltando or sobrando:
        print(f"❌  {use_case_class.__name__}")
        if faltando: print(f"    Faltando : {faltando}")
        if sobrando: print(f"    Sobrando : {sobrando}")
        return False
    else:
        print(f"✅  {use_case_class.__name__} — contrato OK")
        return True

casos = [
    (RegistrarMovimentacaoEstoque,     {"movimentacao_repo": None}),
    (RegistrarAjusteEstoque,           {"movimentacao_repo": None}),
    (RegistrarAvariaEstoque,           {"movimentacao_repo": None}),
    (RegistrarRecebimento,             {"recebimento_repo": None}),
    (RegistrarInventarioCiclico,       {"movimentacao_repo": None, "inventario_repo": None}),
    (RegistrarPoliticaKanban,          {"kanban_repo": None}),
    (ProcessarCurvaABCD,               {"politica_repo": None}),
    (ProcessarGiroEstoque,             {"politica_repo": None}),
    (ProcessarSazonalidadeOperacional, {"sinal_repo": None, "politica_repo": None}),
    (ProcessarGovernancaOrcamentaria,  {"orcamento_repo": None}),
]

print("=== Smoke Test — Contrato de Fábrica ===\n")
resultados = [verificar_contrato(uc, f) for uc, f in casos]
print(f"\n{'✅ Todos os contratos OK' if all(resultados) else '❌ FALHAS ENCONTRADAS — revisar antes do commit'}")
