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
        
        # Por enquanto, retornando estatísticas simplificadas
        # TODO: Implementar relacionamento Customer-Service quando necessário
        
        return jsonify({
            'stats': {
                'total_services': 0,
                'active_services': 0, 
                'completed_services': 0,
                'total_spent': 0.0,
                'monthly_spent': 0.0
            },
            'recent_services': []
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
        
        # Parâmetros de query
        page = request.args.get('page', 1, type=int)
        
        # Por enquanto, retornando lista vazia
        # TODO: Implementar relacionamento Customer-Service quando necessário
        
        return jsonify({
            'services': [],
            'total': 0,
            'pages': 0,
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
        
        # Por enquanto, retornando erro pois não há relacionamento implementado
        return jsonify({
            'error': 'Funcionalidade em desenvolvimento',
            'message': 'Criação de serviços por clientes será implementada em breve'
        }), 501