from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamentos
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    
    # Detalhes do serviço
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo_servico = db.Column(db.String(50), nullable=False)  # entrega, transporte, mudanca, etc.
    
    # Localização
    origem_endereco = db.Column(db.String(300), nullable=False)
    origem_latitude = db.Column(db.Float, nullable=True)
    origem_longitude = db.Column(db.Float, nullable=True)
    
    destino_endereco = db.Column(db.String(300), nullable=False)
    destino_latitude = db.Column(db.Float, nullable=True)
    destino_longitude = db.Column(db.Float, nullable=True)
    
    # Valores e pagamento
    valor_base = db.Column(db.Float, nullable=False)
    valor_final = db.Column(db.Float, nullable=True)
    comissao_plataforma = db.Column(db.Float, default=0.15)  # 15% padrão
    valor_comissao = db.Column(db.Float, nullable=True)
    valor_motorista = db.Column(db.Float, nullable=True)
    
    # Status e datas
    status = db.Column(db.String(30), default='disponivel')  # disponivel, aceito, em_andamento, concluido, cancelado
    prioridade = db.Column(db.String(20), default='normal')  # baixa, normal, alta, urgente
    
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_aceite = db.Column(db.DateTime, nullable=True)
    data_inicio = db.Column(db.DateTime, nullable=True)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    data_limite = db.Column(db.DateTime, nullable=True)
    
    # Informações adicionais
    observacoes = db.Column(db.Text, nullable=True)
    peso_estimado = db.Column(db.Float, nullable=True)  # em kg
    distancia_estimada = db.Column(db.Float, nullable=True)  # em km
    tempo_estimado = db.Column(db.Integer, nullable=True)  # em minutos
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    trips = db.relationship('Trip', backref='service', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='service', lazy=True, cascade='all, delete-orphan')
    # messages = db.relationship('ChatMessage', backref='service', lazy=True, cascade='all, delete-orphan')  # Removido: ChatMessage não tem service_id
    
    def calculate_commission(self):
        """Calcula a comissão da plataforma"""
        if self.valor_final:
            self.valor_comissao = self.valor_final * self.comissao_plataforma
            self.valor_motorista = self.valor_final - self.valor_comissao
        elif self.valor_base:
            self.valor_comissao = self.valor_base * self.comissao_plataforma
            self.valor_motorista = self.valor_base - self.valor_comissao
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'driver_id': self.driver_id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'tipo_servico': self.tipo_servico,
            'origem_endereco': self.origem_endereco,
            'origem_latitude': self.origem_latitude,
            'origem_longitude': self.origem_longitude,
            'destino_endereco': self.destino_endereco,
            'destino_latitude': self.destino_latitude,
            'destino_longitude': self.destino_longitude,
            'valor_base': self.valor_base,
            'valor_final': self.valor_final,
            'comissao_plataforma': self.comissao_plataforma,
            'valor_comissao': self.valor_comissao,
            'valor_motorista': self.valor_motorista,
            'status': self.status,
            'prioridade': self.prioridade,
            'data_solicitacao': self.data_solicitacao.isoformat() if self.data_solicitacao else None,
            'data_aceite': self.data_aceite.isoformat() if self.data_aceite else None,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_conclusao': self.data_conclusao.isoformat() if self.data_conclusao else None,
            'data_limite': self.data_limite.isoformat() if self.data_limite else None,
            'observacoes': self.observacoes,
            'peso_estimado': self.peso_estimado,
            'distancia_estimada': self.distancia_estimada,
            'tempo_estimado': self.tempo_estimado,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Service {self.titulo}>'

