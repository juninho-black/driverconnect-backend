from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from src.models.user import db
from src.models.company import Company
from src.models.service import Service
from src.models.driver import Driver
from src.models.payment import Payment, Commission, DriverEarning
from src.models.trip import Trip

company_bp = Blueprint('company', __name__)

@company_bp.route('/company/register', methods=['POST'])
def register_company():
    """Cadastro de nova empresa"""
    try:
        data = request.get_json()
        
        # Verificar se empresa já existe
        existing_company = Company.query.filter_by(email=data['email']).first()
        if existing_company:
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        existing_cnpj = Company.query.filter_by(cnpj=data['cnpj']).first()
        if existing_cnpj:
            return jsonify({'error': 'CNPJ já cadastrado'}), 400
        
        # Criar nova empresa
        company = Company(
            nome=data['nome'],
            cnpj=data['cnpj'],
            email=data['email'],
            telefone=data['telefone'],
            endereco=data['endereco'],
            cidade=data['cidade'],
            estado=data['estado'],
            cep=data['cep'],
            responsavel_nome=data['responsavel_nome'],
            responsavel_cargo=data['responsavel_cargo'],
            password_hash=generate_password_hash(data['password']),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        
        db.session.add(company)
        db.session.commit()
        
        # Criar token de acesso
        access_token = create_access_token(
            identity={'id': company.id, 'type': 'company'},
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'message': 'Empresa cadastrada com sucesso',
            'access_token': access_token,
            'company': company.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@company_bp.route('/company/login', methods=['POST'])
def login_company():
    """Login de empresa"""
    try:
        data = request.get_json()
        
        company = Company.query.filter_by(email=data['email']).first()
        
        if company and check_password_hash(company.password_hash, data['password']):
            if company.status != 'ativa':
                return jsonify({'error': 'Empresa inativa ou suspensa'}), 403
            
            access_token = create_access_token(
                identity={'id': company.id, 'type': 'company'},
                expires_delta=timedelta(days=7)
            )
            
            return jsonify({
                'message': 'Login realizado com sucesso',
                'access_token': access_token,
                'company': company.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Email ou senha inválidos'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('/company/services', methods=['GET'])
@jwt_required()
def get_company_services():
    """Listar serviços da empresa"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'company':
            return jsonify({'error': 'Acesso negado'}), 403
        
        company_id = current_user['id']
        
        # Parâmetros de filtro
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Query base
        query = Service.query.filter_by(company_id=company_id)
        
        # Aplicar filtros
        if status:
            query = query.filter_by(status=status)
        
        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(Service.created_at.desc())
        
        # Paginação
        services = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'services': [service.to_dict() for service in services.items],
            'total': services.total,
            'pages': services.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('/company/services', methods=['POST'])
@jwt_required()
def create_service():
    """Criar novo serviço"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'company':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        company_id = current_user['id']
        
        # Criar novo serviço
        service = Service(
            company_id=company_id,
            titulo=data['titulo'],
            descricao=data.get('descricao'),
            tipo_servico=data['tipo_servico'],
            origem_endereco=data['origem_endereco'],
            origem_latitude=data.get('origem_latitude'),
            origem_longitude=data.get('origem_longitude'),
            destino_endereco=data['destino_endereco'],
            destino_latitude=data.get('destino_latitude'),
            destino_longitude=data.get('destino_longitude'),
            valor_base=float(data['valor_base']),
            prioridade=data.get('prioridade', 'normal'),
            data_limite=datetime.fromisoformat(data['data_limite']) if data.get('data_limite') else None,
            observacoes=data.get('observacoes'),
            peso_estimado=data.get('peso_estimado'),
            distancia_estimada=data.get('distancia_estimada'),
            tempo_estimado=data.get('tempo_estimado')
        )
        
        # Calcular comissão
        service.calculate_commission()
        
        db.session.add(service)
        db.session.commit()
        
        return jsonify({
            'message': 'Serviço criado com sucesso',
            'service': service.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@company_bp.route('/company/services/<int:service_id>', methods=['GET'])
@jwt_required()
def get_service_details():
    """Obter detalhes de um serviço específico"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'company':
            return jsonify({'error': 'Acesso negado'}), 403
        
        company_id = current_user['id']
        service_id = request.view_args['service_id']
        
        service = Service.query.filter_by(id=service_id, company_id=company_id).first()
        if not service:
            return jsonify({'error': 'Serviço não encontrado'}), 404
        
        # Incluir dados do motorista se atribuído
        service_data = service.to_dict()
        if service.driver_id:
            driver = Driver.query.get(service.driver_id)
            if driver:
                service_data['driver'] = driver.to_dict()
        
        # Incluir dados da viagem se existir
        trip = Trip.query.filter_by(service_id=service.id).first()
        if trip:
            service_data['trip'] = trip.to_dict()
        
        return jsonify({'service': service_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('/company/services/<int:service_id>', methods=['PUT'])
@jwt_required()
def update_service():
    """Atualizar serviço"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'company':
            return jsonify({'error': 'Acesso negado'}), 403
        
        company_id = current_user['id']
        service_id = request.view_args['service_id']
        data = request.get_json()
        
        service = Service.query.filter_by(id=service_id, company_id=company_id).first()
        if not service:
            return jsonify({'error': 'Serviço não encontrado'}), 404
        
        # Atualizar campos permitidos
        updatable_fields = [
            'titulo', 'descricao', 'valor_base', 'prioridade', 
            'data_limite', 'observacoes', 'status'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'data_limite' and data[field]:
                    setattr(service, field, datetime.fromisoformat(data[field]))
                elif field == 'valor_base':
                    setattr(service, field, float(data[field]))
                    service.calculate_commission()  # Recalcular comissão
                else:
                    setattr(service, field, data[field])
        
        service.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Serviço atualizado com sucesso',
            'service': service.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@company_bp.route('/company/drivers', methods=['GET'])
@jwt_required()
def get_company_drivers():
    """Listar motoristas da empresa"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'company':
            return jsonify({'error': 'Acesso negado'}), 403
        
        company_id = current_user['id']
        
        drivers = Driver.query.filter_by(company_id=company_id).all()
        
        return jsonify({
            'drivers': [driver.to_dict() for driver in drivers]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('/company/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Obter estatísticas para o dashboard da empresa"""
    try:
        current_user = get_jwt_identity()
        if current_user['type'] != 'company':
            return jsonify({'error': 'Acesso negado'}), 403
        
        company_id = current_user['id']
        
        # Estatísticas básicas
        total_services = Service.query.filter_by(company_id=company_id).count()
        active_services = Service.query.filter_by(company_id=company_id, status='em_andamento').count()
        total_drivers = Driver.query.filter_by(company_id=company_id).count()
        active_drivers = Driver.query.filter_by(company_id=company_id, status='ativo').count()
        
        # Receita do mês atual
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_payments = Payment.query.filter(
            Payment.company_id == company_id,
            Payment.data_pagamento >= current_month,
            Payment.status_pagamento == 'aprovado'
        ).all()
        
        monthly_revenue = sum(payment.valor_total for payment in monthly_payments)
        
        # Serviços recentes
        recent_services = Service.query.filter_by(company_id=company_id)\
            .order_by(Service.created_at.desc())\
            .limit(5)\
            .all()
        
        return jsonify({
            'stats': {
                'total_services': total_services,
                'active_services': active_services,
                'total_drivers': total_drivers,
                'active_drivers': active_drivers,
                'monthly_revenue': monthly_revenue
            },
            'recent_services': [service.to_dict() for service in recent_services]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

