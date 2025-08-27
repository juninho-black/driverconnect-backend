from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class DriverRating(db.Model):
    __tablename__ = 'driver_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Quem avaliou
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Quem foi avaliado
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    
    # Serviço relacionado (opcional, mas bom para contexto)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    
    # Avaliação
    stars = db.Column(db.Float, nullable=False) # 1.0 a 5.0
    feedback = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'driver_id': self.driver_id,
            'service_id': self.service_id,
            'stars': self.stars,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DriverRating {self.id} - Driver {self.driver_id} - Stars {self.stars}>'


