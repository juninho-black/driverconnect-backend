from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from src.models.user import db
from src.models.driver import Driver
from src.models.service import Service
from src.models.company import Company
from src.models.payment import Payment, DriverEarning
from src.models.trip import Trip

driver_bp = Blueprint('driver', __name__)

@driver_bp.route('/driver/register', methods=['POST'])
def register_driver():
    """Cadastro de novo motorista"""
    try:
        data = request.get_json()
        
        # Verificar se motorista já existe
        existing_driver = Driver.query.filter_by(email=data['email']).first()
        if existing_driver:
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        existing_cpf = Driver.query.filter_by(cpf=data['cpf']).first()
        if existing_cpf:
            return jsonify({'error': 'CPF já cadastrado'}), 400
        
        existing_cnh = Driver.query.filter_by(cnh=data['cnh']).first()
        if existing_cnh:
            return jsonify({'error': 'CNH já cadastrada'}), 400
        
        # Criar novo motorista
        driver = Driver(
            nome=data['nome'],
            email=data['email'],
            telefone=data['telefone'],
            cpf=data['cpf'],
            cnh=data['cnh'],
            password_hash=generate_password_hash(data['password']),
            veiculo_modelo=data['veiculo_modelo'],
            veiculo_placa=data['veiculo_placa'],
            veiculo_ano=int(data['veiculo_ano']),
            company_id=data.get('company_id')
        )
        
        db.session.add(driver)
        db.session.commit()
        
        # Criar token de acesso
        access_token = create_access_token(
            identity={'id': driver.id, 'type': 'driver'},
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'message': 'Motorista cadastrado com sucesso',
            'access_token': access_token,
            'driver': driver.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@driver_bp.route('/driver/login', methods=['POST'])
def login_driver():
    """Login de motorista"""
    try:
        data = request.get_json()
        
        driver = Driver.query.filter_by(email=data['email']).first()
        
        if driver and check_password_hash(driver.password_hash, data['password']):
            if driver.status != 'ativo':
                return jsonify({'error': 'Motorista inativo ou suspenso'}), 403
            
            access_token = create_access_token(
                identity={'id': driver.id, 'type': 'driver'},
                expires_delta=timedelta(days=7)
            )
            
            return jsonify({
                'message': 'Login realizado com sucesso',
                'access_token': access_token,
                'driver': driver.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Email ou senha inválidos'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@driver_bp.route('/driver/available-services', methods=['GET'])
@jwt_required()
def get_available_services():
    """Listar serviços disponíveis para o motorista"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'driver':
            return jsonify({'error': 'Acesso negado'}), 403
        
        driver_id = current_user['id']
        driver = Driver.query.get(driver_id)
        
        if not driver:
            return jsonify({'error': 'Motorista não encontrado'}), 404
        
        # Parâmetros de filtro
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Query para serviços disponíveis
        query = Service.query.filter_by(status='disponivel')
        
        # Se motorista está vinculado a uma empresa, mostrar apenas serviços dessa empresa
        if driver.company_id:
            query = query.filter_by(company_id=driver.company_id)
        
        # Ordenar por prioridade e data de criação
        query = query.order_by(
            Service.prioridade.desc(),
            Service.created_at.desc()
        )
        
        # Paginação
        services = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Incluir dados da empresa para cada serviço
        services_data = []
        for service in services.items:
            service_data = service.to_dict()
            company = Company.query.get(service.company_id)
            if company:
                service_data['company'] = {
                    'id': company.id,
                    'nome': company.nome,
                    'telefone': company.telefone,
                    'endereco': company.endereco
                }
            services_data.append(service_data)
        
        return jsonify({
            'services': services_data,
            'total': services.total,
            'pages': services.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@driver_bp.route('/driver/accept-service/<int:service_id>', methods=['POST'])
@jwt_required()
def accept_service():
    """Aceitar um serviço"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'driver':
            return jsonify({'error': 'Acesso negado'}), 403
        
        driver_id = current_user['id']
        service_id = request.view_args['service_id']
        
        # Verificar se o serviço existe e está disponível
        service = Service.query.get(service_id)
        if not service:
            return jsonify({'error': 'Serviço não encontrado'}), 404
        
        if service.status != 'disponivel':
            return jsonify({'error': 'Serviço não está mais disponível'}), 400
        
        # Verificar se motorista pode aceitar (se vinculado à empresa)
        driver = Driver.query.get(driver_id)
        if driver.company_id and driver.company_id != service.company_id:
            return jsonify({'error': 'Você não pode aceitar serviços desta empresa'}), 403
        
        # Atualizar serviço
        service.driver_id = driver_id
        service.status = 'aceito'
        service.data_aceite = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Serviço aceito com sucesso',
            'service': service.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@driver_bp.route('/driver/my-services', methods=['GET'])
@jwt_required()
def get_driver_services():
    """Listar serviços do motorista"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'driver':
            return jsonify({'error': 'Acesso negado'}), 403
        
        driver_id = current_user['id']
        
        # Parâmetros de filtro
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Query base
        query = Service.query.filter_by(driver_id=driver_id)
        
        # Aplicar filtros
        if status:
            query = query.filter_by(status=status)
        
        # Ordenar por data de aceite (mais recentes primeiro)
        query = query.order_by(Service.data_aceite.desc())
        
        # Paginação
        services = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Incluir dados da empresa para cada serviço
        services_data = []
        for service in services.items:
            service_data = service.to_dict()
            company = Company.query.get(service.company_id)
            if company:
                service_data['company'] = {
                    'id': company.id,
                    'nome': company.nome,
                    'telefone': company.telefone,
                    'endereco': company.endereco
                }
            services_data.append(service_data)
        
        return jsonify({
            'services': services_data,
            'total': services.total,
            'pages': services.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@driver_bp.route('/driver/start-trip/<int:service_id>', methods=['POST'])
@jwt_required()
def start_trip():
    """Iniciar viagem"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'driver':
            return jsonify({'error': 'Acesso negado'}), 403
        
        driver_id = current_user['id']
        service_id = request.view_args['service_id']
        data = request.get_json()
        
        # Verificar se o serviço pertence ao motorista
        service = Service.query.filter_by(id=service_id, driver_id=driver_id).first()
        if not service:
            return jsonify({'error': 'Serviço não encontrado'}), 404
        
        if service.status != 'aceito':
            return jsonify({'error': 'Serviço não pode ser iniciado'}), 400
        
        # Criar nova viagem
        trip = Trip(
            service_id=service_id,
            driver_id=driver_id,
            company_id=service.company_id,
            inicio_latitude=data.get('latitude'),
            inicio_longitude=data.get('longitude')
        )
        
        # Atualizar status do serviço
        service.status = 'em_andamento'
        service.data_inicio = datetime.utcnow()
        
        db.session.add(trip)
        db.session.commit()
        
        return jsonify({
            'message': 'Viagem iniciada com sucesso',
            'trip': trip.to_dict(),
            'service': service.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@driver_bp.route('/driver/complete-trip/<int:service_id>', methods=['POST'])
@jwt_required()
def complete_trip():
    """Finalizar viagem"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'driver':
            return jsonify({'error': 'Acesso negado'}), 403
        
        driver_id = current_user['id']
        service_id = request.view_args['service_id']
        data = request.get_json()
        
        # Verificar se o serviço pertence ao motorista
        service = Service.query.filter_by(id=service_id, driver_id=driver_id).first()
        if not service:
            return jsonify({'error': 'Serviço não encontrado'}), 404
        
        if service.status != 'em_andamento':
            return jsonify({'error': 'Serviço não está em andamento'}), 400
        
        # Buscar viagem
        trip = Trip.query.filter_by(service_id=service_id).first()
        if not trip:
            return jsonify({'error': 'Viagem não encontrada'}), 404
        
        # Finalizar viagem
        trip.status = 'concluida'
        trip.data_fim = datetime.utcnow()
        trip.fim_latitude = data.get('latitude')
        trip.fim_longitude = data.get('longitude')
        trip.distancia_percorrida = data.get('distancia_percorrida')
        trip.observacoes = data.get('observacoes')
        
        # Calcular tempo de viagem
        if trip.data_inicio:
            tempo_viagem = (trip.data_fim - trip.data_inicio).total_seconds() / 60
            trip.tempo_viagem = int(tempo_viagem)
        
        # Atualizar status do serviço
        service.status = 'concluido'
        service.data_conclusao = datetime.utcnow()
        
        # Definir valor final se não foi definido
        if not service.valor_final:
            service.valor_final = service.valor_base
            service.calculate_commission()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Viagem finalizada com sucesso',
            'trip': trip.to_dict(),
            'service': service.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@driver_bp.route('/driver/update-location', methods=['POST'])
@jwt_required()
def update_location():
    """Atualizar localização do motorista"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'driver':
            return jsonify({'error': 'Acesso negado'}), 403
        
        driver_id = current_user['id']
        data = request.get_json()
        
        driver = Driver.query.get(driver_id)
        if not driver:
            return jsonify({'error': 'Motorista não encontrado'}), 404
        
        # Atualizar localização
        driver.latitude = data.get('latitude')
        driver.longitude = data.get('longitude')
        driver.last_location_update = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Localização atualizada com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@driver_bp.route('/driver/dashboard/stats', methods=['GET'])
@jwt_required()
def get_driver_dashboard_stats():
    """Obter estatísticas para o dashboard do motorista"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'driver':
            return jsonify({'error': 'Acesso negado'}), 403
        
        driver_id = current_user['id']
        
        # Estatísticas básicas
        total_trips = Trip.query.filter_by(driver_id=driver_id, status='concluida').count()
        
        # Viagens hoje
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        trips_today = Trip.query.filter(
            Trip.driver_id == driver_id,
            Trip.data_inicio >= today,
            Trip.status == 'concluida'
        ).count()
        
        # Ganhos do mês atual
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_earnings = DriverEarning.query.filter(
            DriverEarning.driver_id == driver_id,
            DriverEarning.data_ganho >= current_month,
            DriverEarning.status_repasse == 'pago'
        ).all()
        
        monthly_income = sum(earning.valor_liquido for earning in monthly_earnings)
        
        # Avaliação média
        driver = Driver.query.get(driver_id)
        
        # Serviços recentes
        recent_services = Service.query.filter_by(driver_id=driver_id)\
            .order_by(Service.data_aceite.desc())\
            .limit(5)\
            .all()
        
        return jsonify({
            'stats': {
                'total_trips': total_trips,
                'trips_today': trips_today,
                'monthly_income': monthly_income,
                'average_rating': driver.avaliacao if driver else 0,
                'total_ratings': driver.total_avaliacoes if driver else 0
            },
            'recent_services': [service.to_dict() for service in recent_services]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

