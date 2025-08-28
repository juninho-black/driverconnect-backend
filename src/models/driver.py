from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Driver(db.Model):
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    cnh = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Dados de endereço
    endereco = db.Column(db.String(300), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    cep = db.Column(db.String(10), nullable=True)
    
    # Dados do veículo
    veiculo_modelo = db.Column(db.String(100), nullable=False)
    veiculo_placa = db.Column(db.String(8), unique=True, nullable=False)
    veiculo_ano = db.Column(db.Integer, nullable=False)
    
    # Status e avaliação
    status = db.Column(db.String(20), default='ativo')  # ativo, inativo, suspenso
    avaliacao = db.Column(db.Float, default=2.0) # Motorista inicia com 2 estrelas
    total_avaliacoes = db.Column(db.Integer, default=1) # Considera a avaliação inicial
    
    # Localização atual
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    last_location_update = db.Column(db.DateTime, nullable=True)
    
    # Relacionamento com empresa
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    services = db.relationship('Service', backref='driver', lazy=True)
    trips = db.relationship('Trip', backref='driver', lazy=True)
    ratings = db.relationship('DriverRating', backref='driver', lazy=True) # Adiciona relacionamento com avaliações
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'cpf': self.cpf,
            'cnh': self.cnh,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'estado': self.estado,
            'cep': self.cep,
            'veiculo_modelo': self.veiculo_modelo,
            'veiculo_placa': self.veiculo_placa,
            'veiculo_ano': self.veiculo_ano,
            'status': self.status,
            'avaliacao': self.avaliacao,
            'total_avaliacoes': self.total_avaliacoes,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'last_location_update': self.last_location_update.isoformat() if self.last_location_update else None,
            'company_id': self.company_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Driver {self.nome}>'


