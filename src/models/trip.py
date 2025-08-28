from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Trip(db.Model):
    __tablename__ = 'trips'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamentos
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)  # Para serviços de pessoa física
    
    # Status da viagem
    status = db.Column(db.String(30), default='iniciada')  # iniciada, em_andamento, pausada, concluida, cancelada
    
    # Dados da viagem
    distancia_percorrida = db.Column(db.Float, nullable=True)  # em km
    tempo_viagem = db.Column(db.Integer, nullable=True)  # em minutos
    
    # Localização de início e fim
    inicio_latitude = db.Column(db.Float, nullable=True)
    inicio_longitude = db.Column(db.Float, nullable=True)
    fim_latitude = db.Column(db.Float, nullable=True)
    fim_longitude = db.Column(db.Float, nullable=True)
    
    # Datas e horários
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime, nullable=True)
    
    # Avaliação
    avaliacao_empresa = db.Column(db.Float, nullable=True)  # Avaliação da empresa sobre o motorista
    avaliacao_motorista = db.Column(db.Float, nullable=True)  # Avaliação do motorista sobre a empresa
    comentario_empresa = db.Column(db.Text, nullable=True)
    comentario_motorista = db.Column(db.Text, nullable=True)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'service_id': self.service_id,
            'driver_id': self.driver_id,
            'company_id': self.company_id,
            'customer_id': self.customer_id,
            'status': self.status,
            'distancia_percorrida': self.distancia_percorrida,
            'tempo_viagem': self.tempo_viagem,
            'inicio_latitude': self.inicio_latitude,
            'inicio_longitude': self.inicio_longitude,
            'fim_latitude': self.fim_latitude,
            'fim_longitude': self.fim_longitude,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'avaliacao_empresa': self.avaliacao_empresa,
            'avaliacao_motorista': self.avaliacao_motorista,
            'comentario_empresa': self.comentario_empresa,
            'comentario_motorista': self.comentario_motorista,
            'observacoes': self.observacoes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Trip {self.id}>'

