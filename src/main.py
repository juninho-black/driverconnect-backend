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

@app.route('/migrate-database')
def migrate_database():
    try:
        import pymysql
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()
        
        migrations_executed = []
        
        # 1. Adicionar colunas de endereço no Driver
        try:
            cursor.execute("ALTER TABLE drivers ADD COLUMN endereco VARCHAR(300)")
            migrations_executed.append('drivers.endereco')
        except Exception as e:
            if '1060' not in str(e):  # Ignora se coluna já existe
                raise e
        
        try:
            cursor.execute("ALTER TABLE drivers ADD COLUMN cidade VARCHAR(100)")
            migrations_executed.append('drivers.cidade')
        except Exception as e:
            if '1060' not in str(e):
                raise e
        
        try:
            cursor.execute("ALTER TABLE drivers ADD COLUMN estado VARCHAR(2)")
            migrations_executed.append('drivers.estado')
        except Exception as e:
            if '1060' not in str(e):
                raise e
        
        try:
            cursor.execute("ALTER TABLE drivers ADD COLUMN cep VARCHAR(10)")
            migrations_executed.append('drivers.cep')
        except Exception as e:
            if '1060' not in str(e):
                raise e
        
        # 2. Adicionar customer_id nas outras tabelas
        try:
            cursor.execute("ALTER TABLE services ADD COLUMN customer_id INT, ADD FOREIGN KEY (customer_id) REFERENCES customers(id)")
            migrations_executed.append('services.customer_id')
        except Exception as e:
            if '1060' not in str(e):
                raise e
        
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN customer_id INT, ADD FOREIGN KEY (customer_id) REFERENCES customers(id)")
            migrations_executed.append('payments.customer_id')
        except Exception as e:
            if '1060' not in str(e):
                raise e
        
        try:
            cursor.execute("ALTER TABLE trips ADD COLUMN customer_id INT, ADD FOREIGN KEY (customer_id) REFERENCES customers(id)")
            migrations_executed.append('trips.customer_id')
        except Exception as e:
            if '1060' not in str(e):
                raise e
        
        try:
            cursor.execute("ALTER TABLE driver_ratings ADD COLUMN customer_id INT, ADD FOREIGN KEY (customer_id) REFERENCES customers(id)")
            migrations_executed.append('driver_ratings.customer_id')
        except Exception as e:
            if '1060' not in str(e):
                raise e
        
        # 3. Tornar company_id opcional nas tabelas
        try:
            cursor.execute("ALTER TABLE services MODIFY company_id INT NULL")
            migrations_executed.append('services.company_id_nullable')
        except Exception as e:
            pass  # Ignora se já é nullable
        
        try:
            cursor.execute("ALTER TABLE driver_ratings MODIFY company_id INT NULL")
            migrations_executed.append('driver_ratings.company_id_nullable')
        except Exception as e:
            pass
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            'status': 'success',
            'message': 'Migração executada com sucesso!',
            'migrations_executed': migrations_executed,
            'total_migrations': len(migrations_executed)
        }, 200
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro na migração: {str(e)}',
            'tipo_erro': type(e).__name__
        }, 500

@app.route('/create-test-users')
def create_test_users():
    try:
        from werkzeug.security import generate_password_hash
        created_users = []
        
        # 1. Criar empresa de teste
        existing_company = Company.query.filter_by(email='empresa@teste.com').first()
        if not existing_company:
            company = Company(
                nome='Empresa Teste',
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
            created_users.append('empresa')
        
        # 2. Criar motorista de teste
        existing_driver = Driver.query.filter_by(email='motorista@teste.com').first()
        if not existing_driver:
            driver = Driver(
                nome='Motorista Teste',
                email='motorista@teste.com',
                cpf='12345678901',
                telefone='(11) 88888-8888',
                endereco='Rua Motorista, 456',
                cidade='São Paulo',
                estado='SP',
                cep='02000-000',
                cnh='12345678901',
                veiculo_modelo='Honda Civic',
                veiculo_placa='ABC-1234',
                veiculo_ano=2020,
                status='ativo',
                password_hash=generate_password_hash('motorista123')
            )
            db.session.add(driver)
            created_users.append('motorista')
        
        # 3. Criar cliente de teste
        existing_customer = Customer.query.filter_by(email='cliente@teste.com').first()
        if not existing_customer:
            customer = Customer(
                nome='Cliente Teste',
                email='cliente@teste.com',
                cpf='98765432100',
                telefone='(11) 77777-7777',
                endereco='Rua Cliente, 789',
                cidade='São Paulo',
                estado='SP',
                cep='03000-000',
                metodo_pagamento_preferido='pix',
                senha=generate_password_hash('cliente123')
            )
            db.session.add(customer)
            created_users.append('cliente')
        
        db.session.commit()
        
        return {
            'status': 'success',
            'message': f'Usuários criados: {created_users}',
            'users': {
                'empresa': 'empresa@teste.com / empresa123',
                'motorista': 'motorista@teste.com / motorista123',
                'cliente': 'cliente@teste.com / cliente123',
                'admin': 'admin@driverconnect.com / admin123'
            },
            'total_users': {
                'empresas': Company.query.count(),
                'motoristas': Driver.query.count(),
                'clientes': Customer.query.count()
            }
        }, 200
        
    except Exception as e:
        db.session.rollback()
        return {
            'status': 'error',
            'message': f'Erro: {str(e)}',
            'tipo_erro': type(e).__name__
        }, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando DriverConnect Backend na porta {port}")
    print(f"📋 Banco: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
