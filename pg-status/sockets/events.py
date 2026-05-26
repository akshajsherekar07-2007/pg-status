"""
Socket.IO event handlers.
"""
import logging
# pyrefly: ignore [missing-import]
from flask import request
# pyrefly: ignore [missing-import]
from flask_login import current_user
from flask_socketio import join_room, leave_room
from extensions import socketio

logger = logging.getLogger(__name__)


def register_socket_events():
    """Register all Socket.IO event handlers."""

    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            logger.info(f'Socket connected: user={current_user.id}, sid={request.sid}')
        else:
            logger.info(f'Socket connected: anonymous, sid={request.sid}')

    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')
            logger.info(f'Socket disconnected: user={current_user.id}')

    @socketio.on('join_property')
    def handle_join_property(data):
        property_id = data.get('property_id')
        if property_id:
            room_name = f'property_{property_id}'
            join_room(room_name)
            logger.info(f'Joined property room: {room_name}, sid={request.sid}')

    @socketio.on('leave_property')
    def handle_leave_property(data):
        property_id = data.get('property_id')
        if property_id:
            room_name = f'property_{property_id}'
            leave_room(room_name)
            logger.info(f'Left property room: {room_name}, sid={request.sid}')

    @socketio.on('ping_status')
    def handle_ping():
        """Health check ping."""
        socketio.emit('pong_status', {'status': 'connected'}, room=request.sid)
