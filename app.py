import json
import os
from flask import Flask, jsonify
from flask_cors import CORS
import redis
from db import db
import mysql.connector

app = Flask(__name__)
cors = CORS(app, resources={f"*": {"origins": "*"}})

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = os.environ.get('REDIS_PORT', '6379')
red = redis.Redis(host=redis_host, port=redis_port)

local_db = os.environ.get('LOCAL_DB', 'false') in ['True', 'true']
db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'root')
db_passwd = os.environ.get('DB_PASSWORD', 'myAwesomePassword')
db_name = os.environ.get('DATABASE', 'mydb')


conn = None
if not local_db:
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, passwd=db_passwd, database=db_name)
    except:
        print("Unable to connect to MySQl")


def get_from_db(table):
    if local_db:
        return db.get(table)

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    return cursor.fetchall()


@app.route('/api/posts', methods=['GET'], strict_slashes=False)
def posts():
    body = {}
    key = "posts"
    try:
        value = red.get(key)
        if not value:
            posts = get_from_db(key)
            red.set(key, str(json.dumps(posts)))

            body['source'] = 'database'
            body['data'] = posts
        else:
            body['source'] = 'redis'
            body['data'] = json.loads(value.decode('ascii'))

        print("Body:")
        print(body)
        return jsonify(body), 200
    except Exception as error: 
        print(error)
        body['data'] = error
        return str(body), 200

@app.route('/api/clear-cache', methods=['GET'], strict_slashes=False)
def clear_cache():
    red.delete("users")
    red.delete("posts")
    red.delete("threads")

    return "", 200


if __name__ == '__main__':
    app.run()