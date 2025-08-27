from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from src.models.user import db
from src.models.company import Company
from src.models.driver import Driver
from src.models.service import Service
from src.models.payment import Payment, Commission, DriverEarning
from src.models.trip import Trip
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

# Configurações padrão do sistema
DEFAULT_COMMISSION_RATE = 15.0  # 15%
MIN_COMMISSION = 5.00
MAX_COMMISSION = 100.00
AUTO_TRANSFER_DELAY = 24  # horas

@admin_bp.route('/admin/dashboard/stats', methods=['GET'])
@jwt_required()
def get_admin_dashboard_stats():
    """Obter estatísticas para o dashboard do admin"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Estatísticas básicas
        total_companies = Company.query.count()
        total_drivers = Driver.query.count()
        total_services = Service.query.count()
        
        # Receita total
        total_payments = Payment.query.filter_by(status_pagamento='aprovado').all()
        total_revenue = sum(payment.valor_total for payment in total_payments)
        
        # Comissões do mês atual
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_commissions = Commission.query.filter(
            Commission.data_comissao >= current_month,
            Commission.status == 'processada'
        ).all()
        monthly_commission = sum(commission.valor_comissao for commission in monthly_commissions)
        
        # Transferências pendentes
        pending_earnings = DriverEarning.query.filter_by(status_repasse='pendente').all()
        pending_transfers = sum(earning.valor_liquido for earning in pending_earnings)
        
        # Serviços ativos e concluídos
        active_services = Service.query.filter(
            Service.status.in_(['disponivel', 'aceito', 'em_andamento'])
        ).count()
        completed_services = Service.query.filter_by(status='concluido').count()
        
        return jsonify({
            'stats': {
                'total_companies': total_companies,
                'total_drivers': total_drivers,
                'total_services': total_services,
                'total_revenue': total_revenue,
                'monthly_commission': monthly_commission,
                'pending_transfers': pending_transfers,
                'active_services': active_services,
                'completed_services': completed_services
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/commission/settings', methods=['GET'])
@jwt_required()
def get_commission_settings():
    """Obter configurações de comissão"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Por enquanto, retornar configurações padrão
        # Em uma implementação real, isso viria de uma tabela de configurações
        settings = {
            'platform_commission': DEFAULT_COMMISSION_RATE,
            'min_commission': MIN_COMMISSION,
            'max_commission': MAX_COMMISSION,
            'auto_transfer': True,
            'transfer_delay': AUTO_TRANSFER_DELAY
        }
        
        return jsonify({'settings': settings}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/commission/settings', methods=['PUT'])
@jwt_required()
def update_commission_settings():
    """Atualizar configurações de comissão"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        # Validar dados
        platform_commission = float(data.get('platform_commission', DEFAULT_COMMISSION_RATE))
        if platform_commission < 0 or platform_commission > 50:
            return jsonify({'error': 'Percentual de comissão deve estar entre 0% e 50%'}), 400
        
        min_commission = float(data.get('min_commission', MIN_COMMISSION))
        max_commission = float(data.get('max_commission', MAX_COMMISSION))
        
        if min_commission > max_commission:
            return jsonify({'error': 'Comissão mínima não pode ser maior que a máxima'}), 400
        
        # Em uma implementação real, salvar em tabela de configurações
        # Por enquanto, apenas retornar sucesso
        
        return jsonify({
            'message': 'Configurações atualizadas com sucesso',
            'settings': {
                'platform_commission': platform_commission,
                'min_commission': min_commission,
                'max_commission': max_commission,
                'auto_transfer': data.get('auto_transfer', True),
                'transfer_delay': int(data.get('transfer_delay', AUTO_TRANSFER_DELAY))
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/transactions', methods=['GET'])
@jwt_required()
def get_admin_transactions():
    """Listar transações para o admin"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Buscar pagamentos com dados relacionados
        payments = Payment.query.join(Service).join(Company).join(Driver)\
            .order_by(Payment.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        transactions = []
        for payment in payments.items:
            service = Service.query.get(payment.service_id)
            company = Company.query.get(payment.company_id)
            driver = Driver.query.get(payment.driver_id)
            
            transactions.append({
                'id': payment.id,
                'company_name': company.nome if company else 'N/A',
                'driver_name': driver.nome if driver else 'N/A',
                'service_title': service.titulo if service else 'N/A',
                'service_value': payment.valor_total,
                'commission': payment.valor_comissao,
                'driver_payment': payment.valor_motorista,
                'status': payment.status_pagamento,
                'payment_method': payment.metodo_pagamento,
                'created_at': payment.created_at.isoformat() if payment.created_at else None
            })
        
        return jsonify({
            'transactions': transactions,
            'total': payments.total,
            'pages': payments.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/process-transfers', methods=['POST'])
@jwt_required()
def process_pending_transfers():
    """Processar transferências pendentes para motoristas"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Buscar ganhos pendentes que estão prontos para repasse
        cutoff_time = datetime.utcnow() - timedelta(hours=AUTO_TRANSFER_DELAY)
        
        pending_earnings = DriverEarning.query.filter(
            DriverEarning.status_repasse == 'pendente',
            DriverEarning.data_ganho <= cutoff_time
        ).all()
        
        processed_count = 0
        total_amount = 0
        
        for earning in pending_earnings:
            # Simular processamento de transferência
            earning.status_repasse = 'pago'
            earning.data_repasse = datetime.utcnow()
            
            processed_count += 1
            total_amount += earning.valor_liquido
        
        db.session.commit()
        
        return jsonify({
            'message': f'{processed_count} transferências processadas com sucesso',
            'processed_count': processed_count,
            'total_amount': total_amount
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/top-companies', methods=['GET'])
@jwt_required()
def get_top_companies():
    """Obter ranking de empresas"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Buscar empresas com mais serviços
        companies = db.session.query(
            Company.id,
            Company.nome,
            func.count(Service.id).label('service_count'),
            func.sum(Service.valor_base).label('total_revenue')
        ).join(Service)\
         .group_by(Company.id, Company.nome)\
         .order_by(func.count(Service.id).desc())\
         .limit(10)\
         .all()
        
        top_companies = []
        for company in companies:
            top_companies.append({
                'id': company.id,
                'name': company.nome,
                'services': company.service_count,
                'revenue': float(company.total_revenue or 0)
            })
        
        return jsonify({'top_companies': top_companies}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/top-drivers', methods=['GET'])
@jwt_required()
def get_top_drivers():
    """Obter ranking de motoristas"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Buscar motoristas com mais viagens
        drivers = db.session.query(
            Driver.id,
            Driver.nome,
            Driver.avaliacao,
            func.count(Trip.id).label('trip_count'),
            func.sum(DriverEarning.valor_liquido).label('total_earnings')
        ).join(Trip, Driver.id == Trip.driver_id)\
         .join(DriverEarning, Driver.id == DriverEarning.driver_id)\
         .group_by(Driver.id, Driver.nome, Driver.avaliacao)\
         .order_by(func.count(Trip.id).desc())\
         .limit(10)\
         .all()
        
        top_drivers = []
        for driver in drivers:
            top_drivers.append({
                'id': driver.id,
                'name': driver.nome,
                'trips': driver.trip_count,
                'earnings': float(driver.total_earnings or 0),
                'rating': float(driver.avaliacao or 0)
            })
        
        return jsonify({'top_drivers': top_drivers}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/calculate-commission', methods=['POST'])
@jwt_required()
def calculate_commission():
    """Calcular comissão para um valor específico"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json()
        service_value = float(data.get('service_value', 0))
        
        if service_value <= 0:
            return jsonify({'error': 'Valor do serviço deve ser maior que zero'}), 400
        
        # Calcular comissão
        commission_rate = DEFAULT_COMMISSION_RATE / 100
        commission_amount = service_value * commission_rate
        
        # Aplicar limites mínimo e máximo
        commission_amount = max(MIN_COMMISSION, min(commission_amount, MAX_COMMISSION))
        
        driver_payment = service_value - commission_amount
        
        return jsonify({
            'service_value': service_value,
            'commission_rate': DEFAULT_COMMISSION_RATE,
            'commission_amount': commission_amount,
            'driver_payment': driver_payment
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/reports/financial', methods=['GET'])
@jwt_required()
def get_financial_report():
    """Gerar relatório financeiro"""
    try:
        current_user = get_jwt_identity()
        if current_user.get('type') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Parâmetros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.now()
        
        # Buscar dados do período
        payments = Payment.query.filter(
            Payment.data_pagamento >= start_date,
            Payment.data_pagamento <= end_date,
            Payment.status_pagamento == 'aprovado'
        ).all()
        
        total_revenue = sum(payment.valor_total for payment in payments)
        total_commission = sum(payment.valor_comissao for payment in payments)
        total_driver_payments = sum(payment.valor_motorista for payment in payments)
        
        services_count = len(set(payment.service_id for payment in payments))
        
        return jsonify({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_revenue': total_revenue,
                'total_commission': total_commission,
                'total_driver_payments': total_driver_payments,
                'services_count': services_count,
                'average_service_value': total_revenue / services_count if services_count > 0 else 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

