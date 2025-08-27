import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager

# Importar todos os modelos
from src.models.user import db
from src.models.company import Company
from src.models.driver import Driver
from src.models.service import Service
from src.models.payment import Payment, Commission, DriverEarning
from src.models.trip import Trip
from src.models.chat import ChatMessage, ChatRoom
from src.models.rating import DriverRating

# Importar rotas
from src.routes.user import user_bp
from src.routes.company import company_bp
from src.routes.driver import driver_bp
from src.routes.chat import chat_bp, register_socketio_events
from src.routes.rating import rating_bp
from src.routes.location import location_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'

# Configurar CORS
CORS(app, origins="*")

# Configurar SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurar JWT
jwt = JWTManager(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(company_bp, url_prefix='/api')
app.register_blueprint(driver_bp, url_prefix='/api')
app.register_blueprint(chat_bp, url_prefix='/api')
app.register_blueprint(rating_bp, url_prefix='/api')
app.register_blueprint(location_bp, url_prefix='/api')

# Registrar eventos do SocketIO
register_socketio_events(socketio)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/driverconnect?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

