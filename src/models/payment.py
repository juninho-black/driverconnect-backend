from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamentos
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    
    # Valores do pagamento
    valor_total = db.Column(db.Float, nullable=False)
    valor_comissao = db.Column(db.Float, nullable=False)
    valor_motorista = db.Column(db.Float, nullable=False)
    
    # Método de pagamento
    metodo_pagamento = db.Column(db.String(50), nullable=False)  # pix, cartao_credito, cartao_debito, dinheiro, boleto
    
    # Status do pagamento
    status_pagamento = db.Column(db.String(30), default='pendente')  # pendente, processando, aprovado, rejeitado, estornado
    
    # Dados do pagamento
    transaction_id = db.Column(db.String(100), nullable=True)  # ID da transação no gateway
    gateway_response = db.Column(db.Text, nullable=True)  # Resposta completa do gateway
    
    # Datas
    data_pagamento = db.Column(db.DateTime, default=datetime.utcnow)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    data_repasse = db.Column(db.DateTime, nullable=True)  # Data do repasse para o motorista
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'service_id': self.service_id,
            'company_id': self.company_id,
            'driver_id': self.driver_id,
            'valor_total': self.valor_total,
            'valor_comissao': self.valor_comissao,
            'valor_motorista': self.valor_motorista,
            'metodo_pagamento': self.metodo_pagamento,
            'status_pagamento': self.status_pagamento,
            'transaction_id': self.transaction_id,
            'data_pagamento': self.data_pagamento.isoformat() if self.data_pagamento else None,
            'data_aprovacao': self.data_aprovacao.isoformat() if self.data_aprovacao else None,
            'data_repasse': self.data_repasse.isoformat() if self.data_repasse else None,
            'observacoes': self.observacoes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Payment {self.id} - R$ {self.valor_total}>'


class Commission(db.Model):
    __tablename__ = 'commissions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamentos
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Valores da comissão
    valor_comissao = db.Column(db.Float, nullable=False)
    percentual_comissao = db.Column(db.Float, nullable=False)
    valor_servico = db.Column(db.Float, nullable=False)
    
    # Status da comissão
    status = db.Column(db.String(30), default='pendente')  # pendente, processada, paga
    
    # Datas
    data_comissao = db.Column(db.DateTime, default=datetime.utcnow)
    data_processamento = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'company_id': self.company_id,
            'valor_comissao': self.valor_comissao,
            'percentual_comissao': self.percentual_comissao,
            'valor_servico': self.valor_servico,
            'status': self.status,
            'data_comissao': self.data_comissao.isoformat() if self.data_comissao else None,
            'data_processamento': self.data_processamento.isoformat() if self.data_processamento else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Commission {self.id} - R$ {self.valor_comissao}>'


class DriverEarning(db.Model):
    __tablename__ = 'driver_earnings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamentos
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    
    # Valores dos ganhos
    valor_bruto = db.Column(db.Float, nullable=False)  # Valor total do serviço
    valor_comissao = db.Column(db.Float, nullable=False)  # Comissão da plataforma
    valor_liquido = db.Column(db.Float, nullable=False)  # Valor que o motorista recebe
    
    # Status do repasse
    status_repasse = db.Column(db.String(30), default='pendente')  # pendente, processando, pago, erro
    
    # Dados bancários para repasse
    banco = db.Column(db.String(100), nullable=True)
    agencia = db.Column(db.String(10), nullable=True)
    conta = db.Column(db.String(20), nullable=True)
    tipo_conta = db.Column(db.String(20), nullable=True)  # corrente, poupanca
    
    # Datas
    data_ganho = db.Column(db.DateTime, default=datetime.utcnow)
    data_repasse = db.Column(db.DateTime, nullable=True)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'driver_id': self.driver_id,
            'payment_id': self.payment_id,
            'service_id': self.service_id,
            'valor_bruto': self.valor_bruto,
            'valor_comissao': self.valor_comissao,
            'valor_liquido': self.valor_liquido,
            'status_repasse': self.status_repasse,
            'banco': self.banco,
            'agencia': self.agencia,
            'conta': self.conta,
            'tipo_conta': self.tipo_conta,
            'data_ganho': self.data_ganho.isoformat() if self.data_ganho else None,
            'data_repasse': self.data_repasse.isoformat() if self.data_repasse else None,
            'observacoes': self.observacoes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DriverEarning {self.id} - R$ {self.valor_liquido}>'

