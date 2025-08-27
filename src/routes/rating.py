from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.rating import DriverRating
from src.models.driver import Driver
from src.models.company import Company
from datetime import datetime

rating_bp = Blueprint('rating', __name__)

@rating_bp.route('/rating/create', methods=['POST'])
@jwt_required()
def create_rating():
    """Criar uma nova avaliação para um motorista"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validar dados obrigatórios
        required_fields = ['driver_id', 'stars']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Campo {field} é obrigatório'}), 400
        
        # Validar se a avaliação está entre 1 e 5
        stars = float(data['stars'])
        if stars < 1.0 or stars > 5.0:
            return jsonify({'success': False, 'message': 'Avaliação deve estar entre 1 e 5 estrelas'}), 400
        
        # Verificar se o motorista existe
        driver = Driver.query.get(data['driver_id'])
        if not driver:
            return jsonify({'success': False, 'message': 'Motorista não encontrado'}), 404
        
        # Verificar se a empresa existe (assumindo que apenas empresas podem avaliar)
        company = Company.query.filter_by(email=current_user).first()
        if not company:
            return jsonify({'success': False, 'message': 'Apenas empresas podem avaliar motoristas'}), 403
        
        # Criar nova avaliação
        new_rating = DriverRating(
            company_id=company.id,
            driver_id=data['driver_id'],
            service_id=data.get('service_id'),  # Opcional
            stars=stars,
            feedback=data.get('feedback', '')
        )
        
        db.session.add(new_rating)
        
        # Atualizar média de avaliação do motorista
        update_driver_rating(data['driver_id'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avaliação criada com sucesso',
            'rating': new_rating.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@rating_bp.route('/rating/driver/<int:driver_id>', methods=['GET'])
def get_driver_ratings(driver_id):
    """Buscar todas as avaliações de um motorista"""
    try:
        # Verificar se o motorista existe
        driver = Driver.query.get(driver_id)
        if not driver:
            return jsonify({'success': False, 'message': 'Motorista não encontrado'}), 404
        
        # Buscar avaliações
        ratings = DriverRating.query.filter_by(driver_id=driver_id).order_by(DriverRating.created_at.desc()).all()
        
        # Calcular estatísticas
        total_ratings = len(ratings)
        if total_ratings > 0:
            average_stars = sum(rating.stars for rating in ratings) / total_ratings
            stars_distribution = {
                '5': len([r for r in ratings if r.stars == 5.0]),
                '4': len([r for r in ratings if r.stars == 4.0]),
                '3': len([r for r in ratings if r.stars == 3.0]),
                '2': len([r for r in ratings if r.stars == 2.0]),
                '1': len([r for r in ratings if r.stars == 1.0])
            }
        else:
            average_stars = 2.0  # Avaliação inicial
            stars_distribution = {'5': 0, '4': 0, '3': 0, '2': 1, '1': 0}
        
        return jsonify({
            'success': True,
            'driver': driver.to_dict(),
            'ratings': [rating.to_dict() for rating in ratings],
            'statistics': {
                'total_ratings': total_ratings,
                'average_stars': round(average_stars, 1),
                'stars_distribution': stars_distribution
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@rating_bp.route('/rating/company/<int:company_id>', methods=['GET'])
@jwt_required()
def get_company_ratings(company_id):
    """Buscar todas as avaliações feitas por uma empresa"""
    try:
        current_user = get_jwt_identity()
        
        # Verificar se a empresa existe e se o usuário tem permissão
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        
        # Verificar permissão (empresa só pode ver suas próprias avaliações)
        if company.email != current_user:
            return jsonify({'success': False, 'message': 'Sem permissão para acessar essas avaliações'}), 403
        
        # Buscar avaliações
        ratings = DriverRating.query.filter_by(company_id=company_id).order_by(DriverRating.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'company': company.to_dict(),
            'ratings': [rating.to_dict() for rating in ratings]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@rating_bp.route('/rating/top-drivers', methods=['GET'])
def get_top_drivers():
    """Buscar motoristas com melhor avaliação (4+ estrelas)"""
    try:
        # Buscar motoristas com 4+ estrelas, ordenados por avaliação
        top_drivers = Driver.query.filter(Driver.avaliacao >= 4.0).order_by(Driver.avaliacao.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'top_drivers': [driver.to_dict() for driver in top_drivers]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

def update_driver_rating(driver_id):
    """Função auxiliar para atualizar a média de avaliação do motorista"""
    try:
        driver = Driver.query.get(driver_id)
        if not driver:
            return
        
        # Buscar todas as avaliações do motorista
        ratings = DriverRating.query.filter_by(driver_id=driver_id).all()
        
        if ratings:
            # Calcular nova média
            total_stars = sum(rating.stars for rating in ratings)
            total_ratings = len(ratings) + 1  # +1 para incluir a avaliação inicial de 2 estrelas
            average = (total_stars + 2.0) / total_ratings  # +2.0 para a avaliação inicial
            
            driver.avaliacao = round(average, 1)
            driver.total_avaliacoes = total_ratings
        else:
            # Manter avaliação inicial
            driver.avaliacao = 2.0
            driver.total_avaliacoes = 1
        
        driver.updated_at = datetime.utcnow()
        
    except Exception as e:
        print(f"Erro ao atualizar avaliação do motorista {driver_id}: {str(e)}")

@rating_bp.route('/rating/update/<int:rating_id>', methods=['PUT'])
@jwt_required()
def update_rating(rating_id):
    """Atualizar uma avaliação existente"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Buscar avaliação
        rating = DriverRating.query.get(rating_id)
        if not rating:
            return jsonify({'success': False, 'message': 'Avaliação não encontrada'}), 404
        
        # Verificar permissão (apenas a empresa que criou pode editar)
        company = Company.query.get(rating.company_id)
        if not company or company.email != current_user:
            return jsonify({'success': False, 'message': 'Sem permissão para editar esta avaliação'}), 403
        
        # Atualizar campos
        if 'stars' in data:
            stars = float(data['stars'])
            if stars < 1.0 or stars > 5.0:
                return jsonify({'success': False, 'message': 'Avaliação deve estar entre 1 e 5 estrelas'}), 400
            rating.stars = stars
        
        if 'feedback' in data:
            rating.feedback = data['feedback']
        
        rating.updated_at = datetime.utcnow()
        
        # Atualizar média do motorista
        update_driver_rating(rating.driver_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avaliação atualizada com sucesso',
            'rating': rating.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@rating_bp.route('/rating/delete/<int:rating_id>', methods=['DELETE'])
@jwt_required()
def delete_rating(rating_id):
    """Deletar uma avaliação"""
    try:
        current_user = get_jwt_identity()
        
        # Buscar avaliação
        rating = DriverRating.query.get(rating_id)
        if not rating:
            return jsonify({'success': False, 'message': 'Avaliação não encontrada'}), 404
        
        # Verificar permissão (apenas a empresa que criou pode deletar)
        company = Company.query.get(rating.company_id)
        if not company or company.email != current_user:
            return jsonify({'success': False, 'message': 'Sem permissão para deletar esta avaliação'}), 403
        
        driver_id = rating.driver_id
        
        db.session.delete(rating)
        
        # Atualizar média do motorista
        update_driver_rating(driver_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avaliação deletada com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

