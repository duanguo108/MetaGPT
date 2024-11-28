from flask import Flask, request, jsonify

from synnex.xidea.topic_summary import topic_summary
import asyncio

app = Flask(__name__)


@app.route('/metagpt/summary',methods=['POST'])
def summary():
    if request.is_json:
        content = request.get_json()
        result = asyncio.run(topic_summary(content["description"]))
        return result.content, 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400





if __name__ == '__main__':
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)