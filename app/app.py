import math

from flask import jsonify, request

from app import app
from app.models import RebaseHistory

PAGE_SIZE = 8


@app.route('/statistic/', methods=['GET'])
def hello_world():
    page = int(request.args.get('page', 1))
    rebase_history = RebaseHistory.query.order_by(RebaseHistory.date.desc()).offset((page - 1) * PAGE_SIZE).limit(
        PAGE_SIZE).all()
    return jsonify(data=[rebase.serialize() for rebase in rebase_history],
                   pages=math.ceil(RebaseHistory.query.count() / PAGE_SIZE))
