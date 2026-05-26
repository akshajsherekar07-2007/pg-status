"""
API routes — RESTful endpoints for AJAX operations.
Standardized response format: {success, data} or {success, error, code}
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import limiter
from models.property import Property
from models.bed import Bed
from models.floor import Floor
from models.room import Room

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')


def api_response(success=True, data=None, error=None, code=200):
    """Standardized API response."""
    resp = {'success': success}
    if data is not None:
        resp['data'] = data
    if error:
        resp['error'] = error
        resp['code'] = code
    return jsonify(resp), code if not success else 200


# --- HOLDS ---

@api_bp.route('/holds/request', methods=['POST'])
@login_required
@limiter.limit("10/hour")
def request_hold():
    if current_user.role != 'student':
        return api_response(
            False, error='Only students can request holds.', code=403)

    data = request.get_json()
    if not data:
        return api_response(False, error='Invalid request body.', code=400)

    bed_id = data.get('bed_id')
    hold_days = data.get('hold_days')

    if not bed_id or not hold_days:
        return api_response(
            False, error='bed_id and hold_days are required.', code=400)

    from services.hold_service import request_hold as do_request
    result = do_request(current_user.id, bed_id, int(hold_days))

    if result['success']:
        return api_response(True, data=result['data'])
    return api_response(
        False, error=result['error'], code=result.get('code', 400))


@api_bp.route('/holds/<int:hold_id>/respond', methods=['POST'])
@login_required
def respond_hold(hold_id):
    if current_user.role != 'owner':
        return api_response(
            False, error='Only owners can respond to holds.', code=403)

    data = request.get_json()
    if not data:
        return api_response(False, error='Invalid request body.', code=400)

    action = data.get('action')  # 'accept' or 'reject'

    if action == 'accept':
        from services.hold_service import accept_hold
        result = accept_hold(hold_id, current_user.id)
    elif action == 'reject':
        reason = data.get('reason', '')
        from services.hold_service import reject_hold
        result = reject_hold(hold_id, current_user.id, reason)
    else:
        return api_response(
            False, error='action must be "accept" or "reject".', code=400)

    if result['success']:
        return api_response(True, data=result['data'])
    return api_response(
        False, error=result['error'], code=result.get('code', 400))


@api_bp.route('/holds/<int:hold_id>/cancel', methods=['POST'])
@login_required
def cancel_hold(hold_id):
    if current_user.role != 'student':
        return api_response(
            False, error='Only students can cancel holds.', code=403)

    from services.hold_service import cancel_hold as do_cancel
    result = do_cancel(hold_id, current_user.id)

    if result['success']:
        return api_response(True, data=result['data'])
    return api_response(
        False, error=result['error'], code=result.get('code', 400))


# --- BED STATUS ---

@api_bp.route('/beds/<int:bed_id>/status', methods=['POST'])
@login_required
def change_bed_status(bed_id):
    if current_user.role != 'owner':
        return api_response(
            False, error='Only owners can change bed status.', code=403)

    # Verify ownership
    bed = Bed.query.get(bed_id)
    if not bed:
        return api_response(False, error='Bed not found.', code=404)

    prop = bed.room.floor.property
    if prop.owner_id != current_user.id:
        return api_response(False, error='Unauthorized.', code=403)

    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ('green', 'yellow', 'red'):
        return api_response(False, error='Invalid status.', code=400)

    from services.status_service import change_bed_status as do_change
    result = do_change(bed_id, new_status, current_user.id, 'manual')

    if result['success']:
        return api_response(True, data=result['data'])
    return api_response(
        False, error=result['error'], code=result.get('code', 400))


@api_bp.route('/beds/<int:bed_id>/override', methods=['POST'])
@login_required
def override_bed(bed_id):
    if current_user.role != 'owner':
        return api_response(
            False, error='Only owners can override holds.', code=403)

    bed = Bed.query.get(bed_id)
    if not bed:
        return api_response(False, error='Bed not found.', code=404)

    prop = bed.room.floor.property
    if prop.owner_id != current_user.id:
        return api_response(False, error='Unauthorized.', code=403)

    active_hold = bed.get_active_hold()
    if not active_hold:
        return api_response(
            False, error='No active hold to override.', code=409)

    from services.hold_service import override_hold
    result = override_hold(active_hold.id, current_user.id)

    if result['success']:
        return api_response(True, data=result['data'])
    return api_response(
        False, error=result['error'], code=result.get('code', 400))


# --- POLLING FALLBACK ---

@api_bp.route('/beds/<int:property_id>/status', methods=['GET'])
@login_required
def get_bed_statuses(property_id):
    """Polling fallback for WebSocket failures."""
    prop = Property.query.get(property_id)
    if not prop:
        return api_response(False, error='Property not found.', code=404)

    beds_data = []
    for floor in prop.floors:
        for room in floor.rooms:
            for bed in room.beds:
                beds_data.append(bed.to_dict())

    return api_response(True, data=beds_data)


# --- NOTIFICATIONS ---

@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    from services.notification_service import get_notifications as get_notifs, get_unread_count
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    notifs = get_notifs(current_user.id, limit, offset)
    unread = get_unread_count(current_user.id)

    return api_response(
        True, data={'notifications': notifs, 'unread_count': unread})


@api_bp.route('/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    data = request.get_json()
    if data and data.get('notification_id'):
        from services.notification_service import mark_read
        mark_read(data['notification_id'], current_user.id)
    else:
        from services.notification_service import mark_all_read
        mark_all_read(current_user.id)

    return api_response(True, data={'status': 'read'})


# --- UPLOAD ---

@api_bp.route('/upload/<entity_type>/<int:entity_id>', methods=['POST'])
@login_required
@limiter.limit("20/hour")
def upload_file(entity_type, entity_id):
    if current_user.role != 'owner':
        return api_response(
            False, error='Only owners can upload files.', code=403)

    if entity_type not in ('property', 'floor', 'room', 'bed'):
        return api_response(False, error='Invalid entity type.', code=400)

    file = request.files.get('file')
    if not file:
        return api_response(False, error='No file provided.', code=400)

    # Determine property_id for ownership check
    if entity_type == 'property':
        prop = Property.query.get(entity_id)
        if not prop or prop.owner_id != current_user.id:
            return api_response(False, error='Unauthorized.', code=403)
        property_id = prop.id
    elif entity_type == 'floor':
        floor = Floor.query.get(entity_id)
        if not floor or floor.property.owner_id != current_user.id:
            return api_response(False, error='Unauthorized.', code=403)
        property_id = floor.property_id
    elif entity_type == 'room':
        room = Room.query.get(entity_id)
        if not room or room.floor.property.owner_id != current_user.id:
            return api_response(False, error='Unauthorized.', code=403)
        property_id = room.floor.property_id
    elif entity_type == 'bed':
        bed = Bed.query.get(entity_id)
        if not bed or bed.room.floor.property.owner_id != current_user.id:
            return api_response(False, error='Unauthorized.', code=403)
        property_id = bed.room.floor.property_id

    from flask import current_app
    from services.upload_service import save_upload
    result = save_upload(file, property_id, entity_type, entity_id,
                         current_app.config['UPLOAD_FOLDER'])

    if result['success']:
        return api_response(True, data=result['data'])
    return api_response(
        False, error=result['error'], code=result.get('code', 400))


@api_bp.route('/media/<int:media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id):
    from models.media import PropertyMedia
    media = PropertyMedia.query.get(media_id)
    if not media:
        return api_response(False, error='Media not found.', code=404)

    prop = Property.query.get(media.property_id)
    if not prop or prop.owner_id != current_user.id:
        return api_response(False, error='Unauthorized.', code=403)

    from flask import current_app
    from services.upload_service import delete_media as do_delete
    result = do_delete(media_id, current_app.config['UPLOAD_FOLDER'])

    if result['success']:
        return api_response(True, data=result['data'])
    return api_response(
        False, error=result['error'], code=result.get('code', 400))


# --- PROPERTIES (for AJAX browse) ---

@api_bp.route('/properties/browse', methods=['GET'])
@login_required
def browse_properties():
    properties = Property.query.filter_by(is_active=True).all()
    return api_response(True, data=[p.to_dict() for p in properties])
