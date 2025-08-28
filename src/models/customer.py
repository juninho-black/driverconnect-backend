from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    data_nascimento = db.Column(db.Date, nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    cep = db.Column(db.String(10), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    foto_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='ativo')  # ativo, inativo, pendente, suspenso
    total_servicos = db.Column(db.Integer, default=0)
    total_gasto = db.Column(db.Float, default=0.00)
    avaliacao_media = db.Column(db.Float, default=0.00)
    metodo_pagamento_preferido = db.Column(db.String(20), default='pix')  # pix, cartao, dinheiro
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    services = db.relationship('Service', foreign_keys='Service.customer_id', backref='customer', lazy=True)
    payments = db.relationship('Payment', foreign_keys='Payment.customer_id', backref='customer', lazy=True)
    ratings = db.relationship('DriverRating', foreign_keys='DriverRating.customer_id', backref='customer', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cpf': self.cpf,
            'email': self.email,
            'telefone': self.telefone,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'estado': self.estado,
            'cep': self.cep,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'foto_url': self.foto_url,
            'status': self.status,
            'total_servicos': self.total_servicos,
            'total_gasto': self.total_gasto,
            'avaliacao_media': self.avaliacao_media,
            'metodo_pagamento_preferido': self.metodo_pagamento_preferido,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Customer {self.nome}>'