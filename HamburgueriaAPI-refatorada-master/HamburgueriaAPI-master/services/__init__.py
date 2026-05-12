# services/__init__.py
# Pacote de serviços da API Hamburgueria.
# Centraliza regras de negócio que são compartilhadas entre múltiplas rotas.
from services.receita_service import (
    processar_receita,
    ajustes_para_json,
    ReceitaError,
    LancheSeReceita,
    InsumoNaoEncontrado,
    EstoqueInsuficiente,
)
