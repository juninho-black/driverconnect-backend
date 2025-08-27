from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from src.models.user import db
from src.models.chat import ChatMessage, ChatRoom
from src.models.service import Service
from src.models.company import Company
from src.models.driver import Driver

chat_bp = Blueprint('chat', __name__)

# Eventos do SocketIO para chat universal em tempo real
def register_socketio_events(socketio):
    
    @socketio.on('join_chat')
    def on_join_chat(data):
        """Entrar em uma sala de chat universal"""
        try:
            chat_room_id = data['chat_room_id']
            user_type = data['user_type']  # 'admin', 'company', 'driver'
            user_id = data['user_id']
            
            # Verificar se o usuário tem permissão para entrar na sala
            chat_room = ChatRoom.query.get(chat_room_id)
            if not chat_room:
                emit('error', {'message': 'Sala de chat não encontrada'})
                return
            
            # Verificar se o usuário é participante da sala ou admin
            is_participant = (
                (user_type == chat_room.participant1_type and user_id == chat_room.participant1_id) or
                (user_type == chat_room.participant2_type and user_id == chat_room.participant2_id) or
                user_type == 'admin'
            )
            
            if not is_participant:
                emit('error', {'message': 'Acesso negado a esta sala de chat'})
                return
            
            # Entrar na sala
            room_name = f"chat_{chat_room_id}"
            join_room(room_name)
            
            # Marcar mensagens como lidas
            chat_room.mark_messages_as_read(user_id)
            db.session.commit()
            
            emit('joined_chat', {
                'room': room_name,
                'chat_room_id': chat_room_id,
                'chat_room': chat_room.to_dict()
            })
            
        except Exception as e:
            emit('error', {'message': str(e)})
    
    @socketio.on('leave_chat')
    def on_leave_chat(data):
        """Sair de uma sala de chat"""
        try:
            chat_room_id = data['chat_room_id']
            room_name = f"chat_{chat_room_id}"
            leave_room(room_name)
            
            emit('left_chat', {'room': room_name})
            
        except Exception as e:
            emit('error', {'message': str(e)})
    
    @socketio.on('send_message')
    def on_send_message(data):
        """Enviar mensagem no chat universal"""
        try:
            chat_room_id = data['chat_room_id']
            sender_type = data['sender_type']  # 'admin', 'company', 'driver'
            sender_id = data['sender_id']
            message = data['message']
            message_type = data.get('message_type', 'text')
            
            # Verificar se o usuário tem permissão
            chat_room = ChatRoom.query.get(chat_room_id)
            if not chat_room:
                emit('error', {'message': 'Sala de chat não encontrada'})
                return
            
            # Verificar se o usuário é participante da sala ou admin
            is_participant = (
                (sender_type == chat_room.participant1_type and sender_id == chat_room.participant1_id) or
                (sender_type == chat_room.participant2_type and sender_id == chat_room.participant2_id) or
                sender_type == 'admin'
            )
            
            if not is_participant:
                emit('error', {'message': 'Acesso negado para enviar mensagem'})
                return
            
            # Criar mensagem
            chat_message = ChatMessage(
                chat_room_id=chat_room_id,
                sender_id=sender_id,
                sender_type=sender_type,
                message=message,
                message_type=message_type,
                file_url=data.get('file_url'),
                file_name=data.get('file_name'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude')
            )
            
            db.session.add(chat_message)
            
            # Atualizar sala de chat
            chat_room.update_last_message(message, sender_id)
            
            db.session.commit()
            
            # Enviar mensagem para todos na sala
            room_name = f"chat_{chat_room_id}"
            emit('new_message', {
                'message': chat_message.to_dict(),
                'chat_room_id': chat_room_id
            }, room=room_name)
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': str(e)})
    
    @socketio.on('typing')
    def on_typing(data):
        """Indicar que usuário está digitando"""
        try:
            chat_room_id = data['chat_room_id']
            sender_type = data['sender_type']
            sender_id = data['sender_id']
            is_typing = data.get('is_typing', True)
            
            room_name = f"chat_{chat_room_id}"
            emit('user_typing', {
                'sender_type': sender_type,
                'sender_id': sender_id,
                'is_typing': is_typing
            }, room=room_name, include_self=False)
            
        except Exception as e:
            emit('error', {'message': str(e)})

@chat_bp.route('/chat/create-room', methods=['POST'])
@jwt_required()
def create_chat_room():
    """Criar uma nova sala de chat entre dois usuários"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validar dados obrigatórios
        required_fields = ['participant_id', 'participant_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Campo {field} é obrigatório'}), 400
        
        # Determinar tipo do usuário atual
        company = Company.query.filter_by(email=current_user).first()
        driver = Driver.query.filter_by(email=current_user).first()
        is_admin = current_user == 'admin@driverconnect.com'
        
        if company:
            current_user_type = 'company'
            current_user_id = company.id
        elif driver:
            current_user_type = 'driver'
            current_user_id = driver.id
        elif is_admin:
            current_user_type = 'admin'
            current_user_id = 1  # ID fixo para admin
        else:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        participant_id = data['participant_id']
        participant_type = data['participant_type']
        service_id = data.get('service_id')  # Opcional
        
        # Verificar se já existe uma sala entre esses usuários
        existing_room = ChatRoom.query.filter(
            ((ChatRoom.participant1_id == current_user_id and ChatRoom.participant1_type == current_user_type and
              ChatRoom.participant2_id == participant_id and ChatRoom.participant2_type == participant_type) or
             (ChatRoom.participant1_id == participant_id and ChatRoom.participant1_type == participant_type and
              ChatRoom.participant2_id == current_user_id and ChatRoom.participant2_type == current_user_type))
        ).first()
        
        if existing_room:
            return jsonify({
                'success': True,
                'message': 'Sala de chat já existe',
                'chat_room': existing_room.to_dict()
            }), 200
        
        # Criar nova sala de chat
        new_room = ChatRoom(
            participant1_id=current_user_id,
            participant1_type=current_user_type,
            participant2_id=participant_id,
            participant2_type=participant_type,
            service_id=service_id
        )
        
        db.session.add(new_room)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sala de chat criada com sucesso',
            'chat_room': new_room.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@chat_bp.route('/chat/rooms', methods=['GET'])
@jwt_required()
def get_chat_rooms():
    """Listar salas de chat do usuário"""
    try:
        current_user = get_jwt_identity()
        
        # Determinar tipo do usuário atual
        company = Company.query.filter_by(email=current_user).first()
        driver = Driver.query.filter_by(email=current_user).first()
        is_admin = current_user == 'admin@driverconnect.com'
        
        if company:
            current_user_type = 'company'
            current_user_id = company.id
        elif driver:
            current_user_type = 'driver'
            current_user_id = driver.id
        elif is_admin:
            current_user_type = 'admin'
            current_user_id = 1  # ID fixo para admin
        else:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Buscar salas onde o usuário é participante
        if is_admin:
            # Admin pode ver todas as salas
            chat_rooms = ChatRoom.query.filter_by(is_active=True).all()
        else:
            chat_rooms = ChatRoom.query.filter(
                ChatRoom.is_active == True,
                ((ChatRoom.participant1_id == current_user_id and ChatRoom.participant1_type == current_user_type) or
                 (ChatRoom.participant2_id == current_user_id and ChatRoom.participant2_type == current_user_type))
            ).all()
        
        # Incluir dados dos participantes para cada sala
        rooms_data = []
        for room in chat_rooms:
            room_data = room.to_dict()
            
            # Adicionar informações dos participantes
            if room.participant1_type == 'company':
                p1 = Company.query.get(room.participant1_id)
                room_data['participant1_name'] = p1.nome if p1 else 'Empresa'
            elif room.participant1_type == 'driver':
                p1 = Driver.query.get(room.participant1_id)
                room_data['participant1_name'] = p1.nome if p1 else 'Motorista'
            else:
                room_data['participant1_name'] = 'Admin'
            
            if room.participant2_type == 'company':
                p2 = Company.query.get(room.participant2_id)
                room_data['participant2_name'] = p2.nome if p2 else 'Empresa'
            elif room.participant2_type == 'driver':
                p2 = Driver.query.get(room.participant2_id)
                room_data['participant2_name'] = p2.nome if p2 else 'Motorista'
            else:
                room_data['participant2_name'] = 'Admin'
            
            # Adicionar dados do serviço se existir
            if room.service_id:
                service = Service.query.get(room.service_id)
                if service:
                    room_data['service'] = {
                        'id': service.id,
                        'titulo': service.titulo,
                        'status': service.status,
                        'origem_endereco': service.origem_endereco,
                        'destino_endereco': service.destino_endereco
                    }
            
            rooms_data.append(room_data)
        
        return jsonify({
            'success': True,
            'chat_rooms': rooms_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@chat_bp.route('/chat/messages/<int:chat_room_id>', methods=['GET'])
@jwt_required()
def get_chat_messages(chat_room_id):
    """Obter mensagens de um chat"""
    try:
        current_user = get_jwt_identity()
        
        # Determinar tipo do usuário atual
        company = Company.query.filter_by(email=current_user).first()
        driver = Driver.query.filter_by(email=current_user).first()
        is_admin = current_user == 'admin@driverconnect.com'
        
        if company:
            current_user_type = 'company'
            current_user_id = company.id
        elif driver:
            current_user_type = 'driver'
            current_user_id = driver.id
        elif is_admin:
            current_user_type = 'admin'
            current_user_id = 1  # ID fixo para admin
        else:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Verificar permissão
        chat_room = ChatRoom.query.get(chat_room_id)
        if not chat_room:
            return jsonify({'success': False, 'message': 'Sala de chat não encontrada'}), 404
        
        # Verificar se o usuário é participante da sala ou admin
        is_participant = (
            (current_user_type == chat_room.participant1_type and current_user_id == chat_room.participant1_id) or
            (current_user_type == chat_room.participant2_type and current_user_id == chat_room.participant2_id) or
            is_admin
        )
        
        if not is_participant:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Parâmetros de paginação
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Buscar mensagens
        messages = ChatMessage.query.filter_by(chat_room_id=chat_room_id)\
            .order_by(ChatMessage.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        # Marcar mensagens como lidas
        chat_room.mark_messages_as_read(current_user_id)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'messages': [message.to_dict() for message in reversed(messages.items)],
            'total': messages.total,
            'pages': messages.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@chat_bp.route('/chat/mark-read/<int:chat_room_id>', methods=['POST'])
@jwt_required()
def mark_messages_read(chat_room_id):
    """Marcar mensagens como lidas"""
    try:
        current_user = get_jwt_identity()
        
        # Determinar tipo do usuário atual
        company = Company.query.filter_by(email=current_user).first()
        driver = Driver.query.filter_by(email=current_user).first()
        is_admin = current_user == 'admin@driverconnect.com'
        
        if company:
            current_user_id = company.id
        elif driver:
            current_user_id = driver.id
        elif is_admin:
            current_user_id = 1  # ID fixo para admin
        else:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Verificar permissão
        chat_room = ChatRoom.query.get(chat_room_id)
        if not chat_room:
            return jsonify({'success': False, 'message': 'Sala de chat não encontrada'}), 404
        
        # Marcar mensagens como lidas
        chat_room.mark_messages_as_read(current_user_id)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mensagens marcadas como lidas'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@chat_bp.route('/chat/support', methods=['POST'])
@jwt_required()
def create_support_chat():
    """Criar chat de suporte com admin"""
    try:
        current_user = get_jwt_identity()
        
        # Determinar tipo do usuário atual
        company = Company.query.filter_by(email=current_user).first()
        driver = Driver.query.filter_by(email=current_user).first()
        
        if company:
            current_user_type = 'company'
            current_user_id = company.id
        elif driver:
            current_user_type = 'driver'
            current_user_id = driver.id
        else:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Verificar se já existe uma sala de suporte
        existing_room = ChatRoom.query.filter(
            ((ChatRoom.participant1_id == current_user_id and ChatRoom.participant1_type == current_user_type and
              ChatRoom.participant2_type == 'admin') or
             (ChatRoom.participant2_id == current_user_id and ChatRoom.participant2_type == current_user_type and
              ChatRoom.participant1_type == 'admin'))
        ).first()
        
        if existing_room:
            return jsonify({
                'success': True,
                'message': 'Chat de suporte já existe',
                'chat_room': existing_room.to_dict()
            }), 200
        
        # Criar nova sala de suporte
        support_room = ChatRoom(
            participant1_id=current_user_id,
            participant1_type=current_user_type,
            participant2_id=1,  # ID fixo para admin
            participant2_type='admin'
        )
        
        db.session.add(support_room)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat de suporte criado com sucesso',
            'chat_room': support_room.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

