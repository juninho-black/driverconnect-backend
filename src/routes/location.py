from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.driver import Driver
from src.models.company import Company
from src.models.trip import Trip
from datetime import datetime

location_bp = Blueprint('location', __name__)

@location_bp.route('/location/update', methods=['POST'])
@jwt_required()
def update_location():
    """Atualizar localização do motorista"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validar dados obrigatórios
        required_fields = ['latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se é um motorista
        driver = Driver.query.filter_by(email=current_user).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Apenas motoristas podem atualizar localização'}), 403
        
        # Validar coordenadas
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return jsonify({'success': False, 'message': 'Coordenadas inválidas'}), 400
                
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Coordenadas devem ser números válidos'}), 400
        
        # Atualizar localização do motorista
        driver.latitude = latitude
        driver.longitude = longitude
        driver.last_location_update = datetime.utcnow()
        driver.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Localização atualizada com sucesso',
            'location': {
                'latitude': driver.latitude,
                'longitude': driver.longitude,
                'last_update': driver.last_location_update.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@location_bp.route('/location/driver/<int:driver_id>', methods=['GET'])
@jwt_required()
def get_driver_location(driver_id):
    """Buscar localização atual de um motorista"""
    try:
        current_user = get_jwt_identity()
        
        # Verificar se o motorista existe
        driver = Driver.query.get(driver_id)
        if not driver:
            return jsonify({'success': False, 'message': 'Motorista não encontrado'}), 404
        
        # Verificar permissão (empresa, admin ou o próprio motorista)
        company = Company.query.filter_by(email=current_user).first()
        driver_user = Driver.query.filter_by(email=current_user).first()
        
        # Admin sempre tem acesso (verificar se é admin pelo email)
        is_admin = current_user == 'admin@driverconnect.com'
        
        if not (is_admin or company or (driver_user and driver_user.id == driver_id)):
            return jsonify({'success': False, 'message': 'Sem permissão para acessar localização'}), 403
        
        return jsonify({
            'success': True,
            'driver': {
                'id': driver.id,
                'nome': driver.nome,
                'latitude': driver.latitude,
                'longitude': driver.longitude,
                'last_location_update': driver.last_location_update.isoformat() if driver.last_location_update else None,
                'status': driver.status
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@location_bp.route('/location/drivers/online', methods=['GET'])
@jwt_required()
def get_online_drivers():
    """Buscar todos os motoristas online com suas localizações"""
    try:
        current_user = get_jwt_identity()
        
        # Verificar permissão (empresa ou admin)
        company = Company.query.filter_by(email=current_user).first()
        is_admin = current_user == 'admin@driverconnect.com'
        
        if not (is_admin or company):
            return jsonify({'success': False, 'message': 'Sem permissão para acessar localizações'}), 403
        
        # Buscar motoristas ativos com localização recente (últimas 2 horas)
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=2)
        
        online_drivers = Driver.query.filter(
            Driver.status == 'ativo',
            Driver.latitude.isnot(None),
            Driver.longitude.isnot(None),
            Driver.last_location_update >= cutoff_time
        ).all()
        
        drivers_data = []
        for driver in online_drivers:
            drivers_data.append({
                'id': driver.id,
                'nome': driver.nome,
                'latitude': driver.latitude,
                'longitude': driver.longitude,
                'last_location_update': driver.last_location_update.isoformat(),
                'avaliacao': driver.avaliacao,
                'veiculo_modelo': driver.veiculo_modelo,
                'veiculo_placa': driver.veiculo_placa
            })
        
        return jsonify({
            'success': True,
            'online_drivers': drivers_data,
            'total': len(drivers_data)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@location_bp.route('/location/drivers/in-trip', methods=['GET'])
@jwt_required()
def get_drivers_in_trip():
    """Buscar motoristas que estão em viagem com suas localizações"""
    try:
        current_user = get_jwt_identity()
        
        # Verificar permissão (apenas admin)
        is_admin = current_user == 'admin@driverconnect.com'
        
        if not is_admin:
            return jsonify({'success': False, 'message': 'Apenas admin pode acessar motoristas em viagem'}), 403
        
        # Buscar viagens ativas
        active_trips = Trip.query.filter(Trip.status == 'em_andamento').all()
        
        drivers_in_trip = []
        for trip in active_trips:
            driver = trip.driver
            if driver and driver.latitude and driver.longitude:
                drivers_in_trip.append({
                    'trip_id': trip.id,
                    'driver': {
                        'id': driver.id,
                        'nome': driver.nome,
                        'latitude': driver.latitude,
                        'longitude': driver.longitude,
                        'last_location_update': driver.last_location_update.isoformat() if driver.last_location_update else None,
                        'veiculo_modelo': driver.veiculo_modelo,
                        'veiculo_placa': driver.veiculo_placa
                    },
                    'trip': {
                        'id': trip.id,
                        'origem': trip.origem,
                        'destino': trip.destino,
                        'started_at': trip.started_at.isoformat() if trip.started_at else None,
                        'estimated_arrival': trip.estimated_arrival.isoformat() if trip.estimated_arrival else None
                    }
                })
        
        return jsonify({
            'success': True,
            'drivers_in_trip': drivers_in_trip,
            'total': len(drivers_in_trip)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@location_bp.route('/location/nearby-drivers', methods=['POST'])
@jwt_required()
def get_nearby_drivers():
    """Buscar motoristas próximos a uma localização"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validar dados obrigatórios
        required_fields = ['latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Campo {field} é obrigatório'}), 400
        
        # Verificar permissão (empresa ou admin)
        company = Company.query.filter_by(email=current_user).first()
        is_admin = current_user == 'admin@driverconnect.com'
        
        if not (is_admin or company):
            return jsonify({'success': False, 'message': 'Sem permissão para buscar motoristas'}), 403
        
        try:
            target_lat = float(data['latitude'])
            target_lng = float(data['longitude'])
            radius_km = float(data.get('radius_km', 10))  # Raio padrão de 10km
            
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Coordenadas devem ser números válidos'}), 400
        
        # Buscar motoristas ativos com localização recente
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=2)
        
        online_drivers = Driver.query.filter(
            Driver.status == 'ativo',
            Driver.latitude.isnot(None),
            Driver.longitude.isnot(None),
            Driver.last_location_update >= cutoff_time
        ).all()
        
        # Calcular distância e filtrar por raio
        nearby_drivers = []
        for driver in online_drivers:
            distance = calculate_distance(target_lat, target_lng, driver.latitude, driver.longitude)
            
            if distance <= radius_km:
                nearby_drivers.append({
                    'id': driver.id,
                    'nome': driver.nome,
                    'latitude': driver.latitude,
                    'longitude': driver.longitude,
                    'distance_km': round(distance, 2),
                    'avaliacao': driver.avaliacao,
                    'veiculo_modelo': driver.veiculo_modelo,
                    'veiculo_placa': driver.veiculo_placa,
                    'last_location_update': driver.last_location_update.isoformat()
                })
        
        # Ordenar por distância
        nearby_drivers.sort(key=lambda x: x['distance_km'])
        
        return jsonify({
            'success': True,
            'nearby_drivers': nearby_drivers,
            'total': len(nearby_drivers),
            'search_params': {
                'latitude': target_lat,
                'longitude': target_lng,
                'radius_km': radius_km
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calcular distância entre duas coordenadas usando fórmula de Haversine"""
    import math
    
    # Converter graus para radianos
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Fórmula de Haversine
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Raio da Terra em quilômetros
    r = 6371
    
    return c * r

