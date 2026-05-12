"""
services/receita_service.py
---------------------------
Serviço central de processamento de receita.

Responsabilidade única: toda a lógica de:
  - carregar receita base de um lanche
  - aplicar adicionais e remoções (observacoes)
  - validar estoque antes de qualquer persistência
  - dar baixa no estoque
  - retornar ajustes no formato padronizado

Esse módulo é utilizado pelas três rotas que manipulam receita:
  POST /pedidos
  PUT  /pedidos/<id>
  POST /vendas

Nenhuma dessas rotas precisa mais conter lógica de receita —
apenas chamam as funções deste serviço e tratam as exceções.
"""

import json

from sqlalchemy import select

from models import Insumo, Lanche_insumo


# ---------------------------------------------------------------------------
# EXCEÇÕES PRÓPRIAS DO SERVIÇO
# Permitem que as rotas diferenciem o tipo de erro sem inspecionar strings.
# ---------------------------------------------------------------------------

class ReceitaError(Exception):
    """Erro genérico do processamento de receita."""
    pass


class LancheSeReceita(ReceitaError):
    """Lançado quando o lanche não tem nenhuma receita cadastrada."""
    pass


class InsumoNaoEncontrado(ReceitaError):
    """Lançado quando um insumo referenciado não existe no banco."""
    def __init__(self, insumo_id: int):
        super().__init__(f"Insumo ID {insumo_id} não encontrado")
        self.insumo_id = insumo_id


class EstoqueInsuficiente(ReceitaError):
    """Lançado quando o estoque não comporta a quantidade necessária."""
    def __init__(self, nome_insumo: str, disponivel: int, necessario: int):
        super().__init__(
            f"Estoque insuficiente para: {nome_insumo} "
            f"(disponível: {disponivel}, necessário: {necessario})"
        )
        self.nome_insumo = nome_insumo


# ---------------------------------------------------------------------------
# FUNÇÕES INTERNAS — usadas apenas dentro do serviço
# ---------------------------------------------------------------------------

def _carregar_receita_base(db_session, lanche_id: int) -> dict:
    """
    Busca os insumos da receita base de um lanche no banco.

    Retorna um dict {insumo_id (int): quantidade_base (int)}.
    Levanta LancheSeReceita se o lanche não tiver receita cadastrada.
    """
    receita_rows = db_session.execute(
        select(Lanche_insumo).filter_by(lanche_id=lanche_id)
    ).scalars().all()

    if not receita_rows:
        raise LancheSeReceita(
            f"Lanche ID {lanche_id} não tem receita cadastrada"
        )

    return {item.insumo_id: item.qtd_insumo for item in receita_rows}


def _aplicar_observacoes(receita: dict, observacoes: dict) -> dict:
    """
    Aplica adicionais e remoções sobre a receita base.

    Regra de quantidade:
      - Cada unidade de qtd no payload equivale a 100 (gramas/unidade interna).
      - Remoção não pode levar a quantidade abaixo de zero.

    Parâmetros:
      receita     — dict {insumo_id: qtd_base} já carregado do banco
      observacoes — {"adicionar": [...], "remover": [...]}

    Retorna um novo dict com as quantidades ajustadas.
    A receita original não é modificada.
    """
    resultado = dict(receita)  # cópia para não mutar o original

    # Aplicar remoções
    for rem in observacoes.get("remover", []):
        insumo_id = rem.get("insumo_id")
        qtd = rem.get("qtd", 0)

        if insumo_id is None:
            continue

        insumo_id = int(insumo_id)

        if insumo_id in resultado:
            resultado[insumo_id] = max(0, resultado[insumo_id] - qtd * 100)

    # Aplicar adicionais
    for add in observacoes.get("adicionar", []):
        insumo_id = add.get("insumo_id")
        qtd = add.get("qtd", 0)

        if insumo_id is None:
            continue

        insumo_id = int(insumo_id)
        resultado[insumo_id] = resultado.get(insumo_id, 0) + qtd * 100

    return resultado


def _verificar_estoque(db_session, receita_ajustada: dict, qtd_lanche: int) -> None:
    """
    Percorre cada insumo da receita ajustada e verifica se o estoque
    comporta a quantidade total necessária (qtd_insumo * qtd_lanche).

    Levanta InsumoNaoEncontrado ou EstoqueInsuficiente em caso de falha.
    Não altera nenhum dado — é uma validação pura de leitura.
    """
    for insumo_id, qtd_por_lanche in receita_ajustada.items():
        insumo = db_session.execute(
            select(Insumo).filter_by(id_insumo=insumo_id)
        ).scalar_one_or_none()

        if not insumo:
            raise InsumoNaoEncontrado(insumo_id)

        necessario = qtd_por_lanche * qtd_lanche
        if insumo.qtd_insumo < necessario:
            raise EstoqueInsuficiente(
                nome_insumo=insumo.nome_insumo,
                disponivel=insumo.qtd_insumo,
                necessario=necessario
            )


def _dar_baixa_estoque(db_session, receita_ajustada: dict, qtd_lanche: int) -> None:
    """
    Deduz do estoque a quantidade consumida por cada insumo.

    Só deve ser chamada DEPOIS de _verificar_estoque() ter passado,
    garantindo que não haverá rollback por falta de estoque.

    Não faz commit — a responsabilidade do commit é da rota/transação chamadora.
    """
    for insumo_id, qtd_por_lanche in receita_ajustada.items():
        insumo = db_session.execute(
            select(Insumo).filter_by(id_insumo=insumo_id)
        ).scalar_one()

        insumo.qtd_insumo -= qtd_por_lanche * qtd_lanche
        db_session.add(insumo)


def _montar_ajustes_formatados(db_session, receita_ajustada: dict) -> list:
    """
    Converte o dict interno {insumo_id: qtd} para a lista padronizada
    que é armazenada em ajustes_receita e devolvida ao cliente.

    Formato de saída (por item):
      {
        "insumo_id":   <int>,
        "insumo_nome": <str>,
        "quantidade":  <int>
      }

    Os nomes são resolvidos do banco neste momento, uma única vez.
    """
    ajustes = []

    for insumo_id, qtd in receita_ajustada.items():
        insumo = db_session.execute(
            select(Insumo).filter_by(id_insumo=insumo_id)
        ).scalar_one_or_none()

        ajustes.append({
            "insumo_id":   insumo_id,
            "insumo_nome": insumo.nome_insumo if insumo else None,
            "quantidade":  qtd
        })

    return ajustes


# ---------------------------------------------------------------------------
# API PÚBLICA DO SERVIÇO
# ---------------------------------------------------------------------------

def processar_receita(
    db_session,
    lanche_id: int,
    observacoes: dict,
    qtd_lanche: int
) -> list:
    """
    Ponto de entrada único para o processamento completo de receita.

    Executa em ordem:
      1. Carrega receita base do lanche
      2. Aplica adicionais e remoções (observacoes)
      3. Valida estoque para a quantidade de lanches pedida
      4. Dá baixa no estoque (sem commit)
      5. Retorna os ajustes no formato padronizado

    Parâmetros:
      db_session  — sessão SQLAlchemy ativa (sem commit)
      lanche_id   — ID do lanche a ser processado
      observacoes — {"adicionar": [...], "remover": [...]}
                    Pode ser None ou {} — tratado como sem ajustes
      qtd_lanche  — quantidade de lanches do pedido (para cálculo de estoque)

    Retorna:
      Lista de dicts no formato padronizado:
        [{"insumo_id": int, "insumo_nome": str, "quantidade": int}, ...]

    Levanta:
      LancheSeReceita      — se o lanche não tem receita
      InsumoNaoEncontrado  — se um insumo referenciado não existe
      EstoqueInsuficiente  — se o estoque não comporta a demanda

    As exceções são intencionalmente propagadas para a rota,
    que as captura e retorna o HTTP adequado.
    """
    # Garante estrutura mínima de observações
    if not observacoes or not isinstance(observacoes, dict):
        observacoes = {"adicionar": [], "remover": []}

    # Passo 1: receita base
    receita_base = _carregar_receita_base(db_session, lanche_id)

    # Passo 2: aplicar ajustes
    receita_ajustada = _aplicar_observacoes(receita_base, observacoes)

    # Passo 3: validação de estoque (leitura pura — não persiste)
    _verificar_estoque(db_session, receita_ajustada, qtd_lanche)

    # Passo 4: baixa no estoque (sem commit)
    _dar_baixa_estoque(db_session, receita_ajustada, qtd_lanche)

    # Passo 5: montar e retornar ajustes formatados
    return _montar_ajustes_formatados(db_session, receita_ajustada)


def ajustes_para_json(ajustes_formatados: list) -> str:
    """
    Serializa a lista de ajustes para string JSON,
    pronta para armazenar no campo ajustes_receita do banco.

    Separado de processar_receita() para que a rota controle
    exatamente o que persiste no modelo.
    """
    return json.dumps(ajustes_formatados, ensure_ascii=False)
