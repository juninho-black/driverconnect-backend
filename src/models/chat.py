from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamento com a sala de chat
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    
    # Remetente da mensagem
    sender_id = db.Column(db.Integer, nullable=False)  # ID do usuário (admin, company, driver)
    sender_type = db.Column(db.String(20), nullable=False)  # 'admin', 'company', 'driver'
    
    # Conteúdo da mensagem
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, image, file, location
    
    # Metadados
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Dados adicionais para diferentes tipos de mensagem
    file_url = db.Column(db.String(500), nullable=True)  # Para imagens/arquivos
    file_name = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True)  # Para localização
    longitude = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_room_id': self.chat_room_id,
            'sender_id': self.sender_id,
            'sender_type': self.sender_type,
            'message': self.message,
            'message_type': self.message_type,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'


class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Participantes da sala de chat (genérico para qualquer tipo de usuário)
    participant1_id = db.Column(db.Integer, nullable=False)
    participant1_type = db.Column(db.String(20), nullable=False) # 'admin', 'company', 'driver'
    participant2_id = db.Column(db.Integer, nullable=False)
    participant2_type = db.Column(db.String(20), nullable=False) # 'admin', 'company', 'driver'
    
    # Opcional: ID do serviço se o chat for relacionado a um serviço específico
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    
    # Status da sala
    is_active = db.Column(db.Boolean, default=True)
    
    # Última atividade
    last_message_at = db.Column(db.DateTime, nullable=True)
    last_message_preview = db.Column(db.String(200), nullable=True)
    
    # Contadores de mensagens não lidas (por participante)
    unread_count_p1 = db.Column(db.Integer, default=0)
    unread_count_p2 = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'participant1_id': self.participant1_id,
            'participant1_type': self.participant1_type,
            'participant2_id': self.participant2_id,
            'participant2_type': self.participant2_type,
            'service_id': self.service_id,
            'is_active': self.is_active,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'last_message_preview': self.last_message_preview,
            'unread_count_p1': self.unread_count_p1,
            'unread_count_p2': self.unread_count_p2,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_last_message(self, message, sender_id):
        self.last_message_at = datetime.utcnow()
        self.last_message_preview = message[:200] if len(message) > 200 else message
        
        # Incrementar contador de não lidas para o destinatário
        if sender_id == self.participant1_id:
            self.unread_count_p2 += 1
        elif sender_id == self.participant2_id:
            self.unread_count_p1 += 1
    
    def mark_messages_as_read(self, reader_id):
        """Marca mensagens como lidas e zera o contador para o leitor"""
        if reader_id == self.participant1_id:
            self.unread_count_p1 = 0
        elif reader_id == self.participant2_id:
            self.unread_count_p2 = 0
    
    def __repr__(self):
        return f'<ChatRoom {self.id}>'


