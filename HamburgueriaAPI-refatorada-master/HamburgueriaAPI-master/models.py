import json
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash
import enum

# Configuração do banco de dados
engine = create_engine('sqlite:///BancoRoyal.db', connect_args={"check_same_thread": False})
local_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()


class Lanche(Base):
    __tablename__ = 'lanches'
    id_lanche = Column(Integer, primary_key=True)
    nome_lanche = Column(String(20), nullable=False, index=True)
    descricao_lanche = Column(String(255), index=True)
    valor_lanche = Column(Float, index=True)
    disponivel = Column(Boolean, default=True, index=True)

    def __repr__(self):
        return '<Lanche: {} {}>'.format(self.id_lanche, self.nome_lanche)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        var_lanche = {
            'id_lanche': self.id_lanche,
            'nome_lanche': self.nome_lanche,
            'descricao_lanche': self.descricao_lanche,
            'disponivel': self.disponivel,
            'valor_lanche': self.valor_lanche,
        }
        return var_lanche



class Insumo(Base):
    __tablename__ = 'insumos'
    id_insumo = Column(Integer, primary_key=True)
    nome_insumo = Column(String(20), nullable=False, index=True)
    qtd_insumo = Column(Integer, default=0, nullable=False, index=True)
    custo = Column(Float, nullable=False, index=True)
    categoria_id = Column(Integer, ForeignKey('categorias.id_categoria'), nullable=False)

    def __repr__(self):
        return '<Insumo: {} {}>'.format(self.id_insumo, self.nome_insumo)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        var_insumo = {
            'id_insumo': self.id_insumo,
            'nome_insumo': self.nome_insumo,
            'qtd_insumo': self.qtd_insumo,
            'categoria_id': self.categoria_id,
            'custo': self.custo,
        }
        return var_insumo


class Lanche_insumo(Base):
    __tablename__ = 'lanche_insumos'
    id_lanche_insumo = Column(Integer, primary_key=True)
    qtd_insumo = Column(Integer, index=True)
    lanche_id = Column(Integer, ForeignKey('lanches.id_lanche'))
    insumo_id = Column(Integer, ForeignKey('insumos.id_insumo'))

    def __repr__(self):
        return '<Lanche_insumo: {} {}>'.format(self.id_lanche_insumo, self.qtd_insumo)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        var_lanche_insumo = {
            'id_lanche_insumo': self.id_lanche_insumo,
            'qtd_insumo': self.qtd_insumo,
            'lanche_id': self.lanche_id,
            'insumo_id': self.insumo_id,
        }
        return var_lanche_insumo


class Categoria(Base):
    __tablename__ = 'categorias'
    id_categoria = Column(Integer, primary_key=True)
    nome_categoria = Column(String(20), nullable=False, index=True)

    def __repr__(self):
        return '<Categoria: {} {}>'.format(self.id_categoria, self.nome_categoria)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        var_categoria = {
            'id_categoria': self.id_categoria,
            'nome_categoria': self.nome_categoria,
        }
        return var_categoria


class Venda(Base):
    __tablename__ = 'vendas'
    id_venda = Column(Integer, primary_key=True)
    data_venda = Column(String(10), nullable=False, index=True)
    valor_venda = Column(Float, nullable=False, index=True)
    status_venda = Column(Boolean, default=True, index=True)
    detalhamento = Column(String(50), nullable=False, index=True)
    ajustes_receita = Column(String(100), nullable=False, index=True)
    endereco = Column(String, nullable=False)
    forma_pagamento = Column(String, nullable=False)
    tipo_venda = Column(String(20), nullable=True, default=None)

    pedidos = relationship("Pedido", back_populates="venda")
    # relacionamento com Lanche
    lanche_id = Column(Integer, ForeignKey('lanches.id_lanche'), nullable=True)
    # relacionamento com Pessoa
    pessoa_id = Column(Integer, ForeignKey('pessoas.id_pessoa'), nullable=False)

    bebida_id = Column(Integer, ForeignKey('bebidas.id_bebida'), nullable=True)

    pessoa = relationship("Pessoa")
    lanche = relationship("Lanche")
    bebida = relationship("Bebida")

    def __repr__(self):
        return '<Venda: {} {}>'.format(self.id_venda, self.data_venda)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        var_venda = {
            "id_venda": self.id_venda,
            "tipo_venda": self.tipo_venda,
            "data_venda": self.data_venda,
            "valor_venda": self.valor_venda,
            "status_venda": self.status_venda,
            "detalhamento": self.detalhamento,
            "ajustes_receita": self.ajustes_receita,
            "lanche_id": self.lanche_id,
            "bebida_id": self.bebida_id,
            "pessoa_id": self.pessoa_id,
            "forma_pagamento": self.forma_pagamento,
            "endereco": self.endereco,
            "lanche": self.lanche.nome_lanche if self.lanche else None,
            "pessoa": self.pessoa.nome_pessoa if self.pessoa else None,
            "bebida": self.bebida.nome_bebida if self.bebida else None,
        }
        return var_venda


class Pedido(Base):
    __tablename__ = 'pedidos'

    id_pedido = Column(Integer, primary_key=True, autoincrement=True)
    id_venda = Column(Integer, ForeignKey("vendas.id_venda"), nullable=True)

    data_pedido = Column(String(19), nullable=False, index=True)
    numero_mesa = Column(Integer, nullable=True, index=True)

    id_lanche = Column(Integer, ForeignKey('lanches.id_lanche'), nullable=True)
    id_bebida = Column(Integer, ForeignKey('bebidas.id_bebida'), nullable=True)
    id_pessoa = Column(Integer, ForeignKey('pessoas.id_pessoa'), nullable=True)

    # ✅ NOVAS COLUNAS
    qtd_lanche = Column(Integer, nullable=False, default=1)
    qtd_bebida = Column(Integer, nullable=False, default=0)

    detalhamento = Column(String(50), nullable=True, index=True)
    ajustes_receita = Column(String(200), nullable=True)

    status = Column(Integer, nullable=False, index=True)
    status_fechado = Column(Boolean, nullable=False, index=True)

    venda = relationship("Venda", back_populates="pedidos")

    def __repr__(self):
        return 'Pedido: {}, {}, {}, {}'.format(self.id_pedido, self.numero_mesa, self.status_fechado, self.data_venda)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        """
        Serializa o pedido para dicionário.

        Campo ajustes_receita:
          Sempre retorna uma lista de objetos no formato padronizado:
            [{"insumo_id": int, "insumo_nome": str | None, "quantidade": int}]

          Compatibilidade com registros antigos:
            - Se o banco contiver lista (formato novo): usa diretamente.
            - Se contiver dict com chave string (formato antigo): converte para lista.
            - Se nulo ou inválido: retorna None.

          Isso garante que clientes (Flet, web app) não precisem lidar
          com dois formatos diferentes — recebem sempre uma lista.
        """
        ajustes = None

        if self.ajustes_receita:
            try:
                dados = json.loads(self.ajustes_receita)

                if isinstance(dados, list):
                    # Formato novo (ReceitaService): lista de objetos — usa diretamente
                    ajustes = dados

                elif isinstance(dados, dict):
                    # Formato antigo: {"1": 200, "3": 100} — converte para lista padronizada
                    # Compatibilidade temporária para registros já gravados no banco
                    ajustes = [
                        {
                            "insumo_id":   int(k),
                            "insumo_nome": None,   # nome não estava disponível no formato antigo
                            "quantidade":  v
                        }
                        for k, v in dados.items()
                    ]

            except Exception:
                ajustes = None

        return {
            "id_pedido": self.id_pedido,
            "id_venda": self.id_venda,
            "numero_mesa": self.numero_mesa,
            "id_lanche": self.id_lanche,
            "id_bebida": self.id_bebida,
            "id_pessoa": self.id_pessoa,
            "qtd_lanche": self.qtd_lanche,
            "qtd_bebida": self.qtd_bebida,
            "detalhamento": self.detalhamento,
            "status": self.status,
            "status_fechado": self.status_fechado,
            "data_pedido": self.data_pedido,
            "ajustes_receita": ajustes,

            # tipo venda
            "tipo_venda": self.venda.tipo_venda if self.venda else "Presencial",
        }


class Bebida(Base):
    __tablename__ = 'bebidas'
    id_bebida = Column(Integer, primary_key=True)
    nome_bebida = Column(String(20), nullable=False, index=True)
    descricao = Column(String(20), nullable=False, index=True)
    valor = Column(Float, nullable=False, index=True)
    quantidade = Column(Integer, nullable=False, index=True)
    categoria = Column(Integer, ForeignKey('categorias.id_categoria'), nullable=False)
    status_bebida = Column(Boolean, nullable=False, index=True, default=True)

    def __repr__(self):
        return '<Bebida: {} {}>'.format(self.id_bebida, self.nome_bebida)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        return {
            "id_bebida": self.id_bebida,
            "nome_bebida": self.nome_bebida,
            "descricao": self.descricao,
            "valor": self.valor,
            "quantidade": self.quantidade,
            "categoria": self.categoria,
            "status_bebida": self.status_bebida,
        }


class Entrada(Base):
    __tablename__ = 'entradas'
    id_entrada = Column(Integer, primary_key=True)
    nota_fiscal = Column(String(20), index=True)
    data_entrada = Column(String(10), nullable=False, index=True)
    qtd_entrada = Column(Integer, nullable=False, index=True)
    valor_entrada = Column(Float, nullable=False, index=True)

    # relacionamento com Insumo
    insumo_id = Column(Integer, ForeignKey('insumos.id_insumo'), nullable=True)
    bebida_id = Column(Integer, ForeignKey('bebidas.id_bebida'), nullable=True)

    def __repr__(self):
        return f'<Entrada: {self.id_entrada} {self.data_entrada}>'

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        return {
            'id_entrada': self.id_entrada,
            'nota_fiscal': self.nota_fiscal,
            'data_entrada': self.data_entrada,
            'qtd_entrada': self.qtd_entrada,
            'valor_entrada': self.valor_entrada,
            'insumo_id': self.insumo_id,
            'bebida_id': self.bebida_id,
        }


class Pessoa(Base):
    __tablename__ = 'pessoas'
    id_pessoa = Column(Integer, primary_key=True)
    nome_pessoa = Column(String(20), nullable=True, index=True)
    cpf = Column(String(11), nullable=True, index=True)
    salario = Column(Float, nullable=True, index=True)
    papel = Column(String(20), nullable=True, index=True)
    status_pessoa = Column(String, nullable=True)
    senha_hash = Column(String, nullable=False)
    email = Column(String, nullable=True, unique=True)

    def __repr__(self):
        return 'Pessoa: {} {}>'.format(self.id_pessoa, self.nome_pessoa)

    def set_senha_hash(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password_hash(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except:
            db_session.rollback()
            raise

    def serialize(self):
        var_pessoa = {
            'id_pessoa': self.id_pessoa,
            'nome_pessoa': self.nome_pessoa,
            'cpf': self.cpf,
            'salario': self.salario,
            'papel': self.papel,
            'status_pessoa': self.status_pessoa,
            'email': self.email,
            'senha_hash': self.senha_hash

        }
        return var_pessoa


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    init_db()
