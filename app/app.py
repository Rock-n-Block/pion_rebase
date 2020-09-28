from flask import jsonify

from app import app
from app.models import RebaseHistory


@app.route('/statistic/', methods=['GET'])
def hello_world():
    rebase_history = RebaseHistory.query.order_by(RebaseHistory.date.desc()).all()
    return jsonify(data=[rebase.serialize() for rebase in rebase_history])
