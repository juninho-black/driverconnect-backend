from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from src.models.user import db
from src.models.customer import Customer
from src.models.service import Service
from src.models.driver import Driver
from src.models.payment import Payment

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customer/register', methods=['POST'])
def register_customer():
    """Cadastro de novo cliente pessoa física"""
    try:
        data = request.get_json()
        
        # Verificar se cliente já existe
        existing_customer = Customer.query.filter_by(email=data['email']).first()
        if existing_customer:
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        existing_cpf = Customer.query.filter_by(cpf=data['cpf']).first()
        if existing_cpf:
            return jsonify({'error': 'CPF já cadastrado'}), 400
        
        # Criar novo cliente
        customer = Customer(
            nome=data['nome'],
            cpf=data['cpf'],
            email=data['email'],
            telefone=data.get('telefone'),
            data_nascimento=datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date() if data.get('data_nascimento') else None,
            endereco=data.get('endereco'),
            cidade=data.get('cidade'),
            estado=data.get('estado'),
            cep=data.get('cep'),
            senha=generate_password_hash(data['password']),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            metodo_pagamento_preferido=data.get('metodo_pagamento_preferido', 'pix')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        # Criar token de acesso
        access_token = create_access_token(
            identity={'id': customer.id, 'type': 'customer'},
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'message': 'Cliente cadastrado com sucesso',
            'access_token': access_token,
            'customer': customer.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customer/login', methods=['POST'])
def login_customer():
    """Login de cliente pessoa física"""
    try:
        data = request.get_json()
        
        customer = Customer.query.filter_by(email=data['email']).first()
        
        if customer and check_password_hash(customer.senha, data['password']):
            if customer.status != 'ativo':
                return jsonify({'error': 'Cliente inativo ou suspenso'}), 403
            
            access_token = create_access_token(
                identity={'id': customer.id, 'type': 'customer'},
                expires_delta=timedelta(days=7)
            )
            
            return jsonify({
                'message': 'Login realizado com sucesso',
                'access_token': access_token,
                'customer': customer.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Email ou senha inválidos'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customer/profile', methods=['GET'])
@jwt_required()
def get_customer_profile():
    """Obter perfil do cliente"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'customer':
            return jsonify({'error': 'Acesso negado'}), 403
        
        customer = Customer.query.get(current_user['id'])
        if not customer:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        return jsonify({'customer': customer.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customer/dashboard/stats', methods=['GET'])
@jwt_required()
def get_customer_dashboard_stats():
    """Obter estatísticas para o dashboard do cliente"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'customer':
            return jsonify({'error': 'Acesso negado'}), 403
        
        customer_id = current_user['id']
        
        # Estatísticas básicas
        total_services = Service.query.filter_by(customer_id=customer_id).count()
        active_services = Service.query.filter(
            Service.customer_id == customer_id,
            Service.status.in_(['pendente', 'aceito', 'em_andamento'])
        ).count()
        completed_services = Service.query.filter_by(
            customer_id=customer_id, 
            status='concluido'
        ).count()
        
        # Gasto total
        total_payments = Payment.query.filter_by(
            customer_id=customer_id,
            status_pagamento='pago'
        ).all()
        total_spent = sum(payment.valor_total for payment in total_payments)
        
        # Gasto do mês atual
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_payments = Payment.query.filter(
            Payment.customer_id == customer_id,
            Payment.data_pagamento >= current_month,
            Payment.status_pagamento == 'pago'
        ).all()
        monthly_spent = sum(payment.valor_total for payment in monthly_payments)
        
        # Serviços recentes
        recent_services = Service.query.filter_by(customer_id=customer_id)\
            .order_by(Service.created_at.desc())\
            .limit(5)\
            .all()
        
        return jsonify({
            'stats': {
                'total_services': total_services,
                'active_services': active_services,
                'completed_services': completed_services,
                'total_spent': total_spent,
                'monthly_spent': monthly_spent
            },
            'recent_services': [service.to_dict() for service in recent_services]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customer/services', methods=['GET'])
@jwt_required()
def get_customer_services():
    """Listar serviços do cliente"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'customer':
            return jsonify({'error': 'Acesso negado'}), 403
        
        customer_id = current_user['id']
        
        # Parâmetros de query
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        # Query base
        query = Service.query.filter_by(customer_id=customer_id)
        
        # Filtrar por status se especificado
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
        
        # Incluir dados do motorista para cada serviço
        services_data = []
        for service in services.items:
            service_data = service.to_dict()
            if service.driver_id:
                driver = Driver.query.get(service.driver_id)
                if driver:
                    service_data['driver'] = {
                        'id': driver.id,
                        'nome': driver.nome,
                        'telefone': driver.telefone,
                        'avaliacao': driver.avaliacao,
                        'veiculo_modelo': driver.veiculo_modelo,
                        'veiculo_placa': driver.veiculo_placa
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

@customer_bp.route('/customer/services', methods=['POST'])
@jwt_required()
def create_customer_service():
    """Criar novo serviço pelo cliente"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'customer':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        customer_id = current_user['id']
        
        # Criar novo serviço
        service = Service(
            customer_id=customer_id,
            solicitante_tipo='customer',
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
            observacoes=data.get('observacoes')
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