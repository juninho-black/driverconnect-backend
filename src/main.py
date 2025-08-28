import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from src.models.user import db

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-in-production')

# Configuração do banco de dados Railway
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'driverconnect')

# String de conexão do MySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': -1,
    'pool_pre_ping': True
}

# Configurar CORS
CORS(app, origins="*")

# Inicializar SQLAlchemy
db.init_app(app)

# Configurar SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurar JWT
jwt = JWTManager(app)

# Importar rotas após configurar o app
with app.app_context():
    # Importar todos os modelos
    from src.models.company import Company
    from src.models.driver import Driver
    from src.models.customer import Customer
    from src.models.service import Service
    from src.models.payment import Payment
    from src.models.trip import Trip
    from src.models.chat import ChatMessage, ChatRoom
    from src.models.rating import DriverRating
    
    # Importar todas as rotas
    from src.routes.company import company_bp
    from src.routes.driver import driver_bp
    from src.routes.customer import customer_bp
    from src.routes.admin import admin_bp
    from src.routes.chat import chat_bp
    from src.routes.rating import rating_bp
    from src.routes.location import location_bp
    from src.routes.user import user_bp
    
    # Registrar blueprints
    app.register_blueprint(company_bp, url_prefix='/api')
    app.register_blueprint(driver_bp, url_prefix='/api')
    app.register_blueprint(customer_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(rating_bp, url_prefix='/api/rating')
    app.register_blueprint(location_bp, url_prefix='/api/location')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    
    # Criar tabelas se não existirem
    try:
        db.create_all()
        print("✅ Banco de dados conectado e tabelas criadas!")
    except Exception as e:
        print(f"❌ Erro ao conectar com banco: {e}")

@app.route('/')
def home():
    return {'message': 'DriverConnect Backend is running', 'version': '1.0'}, 200

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'Backend is running'}, 200

@app.route('/db-test')
def db_test():
    try:
        # Testar conexão usando as mesmas configurações
        import pymysql
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return {
            'status': 'success', 
            'message': 'Database connection OK',
            'db_host': DB_HOST,
            'db_name': DB_NAME,
            'database_url': DATABASE_URL.replace(DB_PASSWORD, '*****'),  # Ocultar senha
            'result': result
        }, 200
    except Exception as e:
        return {
            'status': 'error', 
            'message': f'Database connection failed: {str(e)}',
            'db_host': DB_HOST,
            'db_name': DB_NAME,
            'database_url': DATABASE_URL.replace(DB_PASSWORD, '*****') if DB_PASSWORD else 'No password set'
        }, 500

@app.route('/create-test-users')
def create_test_users():
    try:
        from werkzeug.security import generate_password_hash
        
        # Vamos criar apenas uma empresa de teste primeiro
        existing_company = Company.query.filter_by(email='empresa@teste.com').first()
        if not existing_company:
            company = Company(
                nome_empresa='Empresa Teste',
                email='empresa@teste.com',
                cnpj='12345678000123',
                telefone='(11) 99999-9999',
                endereco='Rua Teste, 123',
                cidade='São Paulo',
                estado='SP',
                cep='01000-000',
                responsavel_nome='João Silva',
                responsavel_cargo='Gerente',
                password_hash=generate_password_hash('empresa123')
            )
            db.session.add(company)
            db.session.commit()
        
        return {
            'status': 'success',
            'message': 'Empresa de teste criada!',
            'users': {
                'empresa': 'empresa@teste.com / empresa123',
                'admin': 'admin@driverconnect.com / admin123'
            }
        }, 200
        
    except Exception as e:
        db.session.rollback()
        return {
            'status': 'error',
            'message': f'Erro ao criar usuários: {str(e)}'
        }, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando DriverConnect Backend na porta {port}")
    print(f"📋 Banco: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
