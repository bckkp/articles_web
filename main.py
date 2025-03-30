import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import psycopg2


load_dotenv()
app = Flask(__name__)
# Конфигурация базы данных
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}


def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


# Создаем таблицу статей, если она не существует
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


init_db()


@app.route('/articles', methods=['GET'])
def get_articles():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, created_at, updated_at FROM articles ORDER BY created_at DESC")
    articles = cur.fetchall()
    cur.close()
    conn.close()

    articles_list = []
    for article in articles:
        articles_list.append({
            'id': article[0],
            'title': article[1],
            'content': article[2],
            'created_at': article[3].isoformat(),
            'updated_at': article[4].isoformat()
        })

    return jsonify(articles_list)


@app.route('/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, created_at, updated_at FROM articles WHERE id = %s", (article_id,))
    article = cur.fetchone()
    cur.close()
    conn.close()

    if article is None:
        return jsonify({'error': 'Article not found'}), 404

    return jsonify({
        'id': article[0],
        'title': article[1],
        'content': article[2],
        'created_at': article[3].isoformat(),
        'updated_at': article[4].isoformat()
    })


@app.route('/articles', methods=['POST'])
def create_article():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO articles (title, content) VALUES (%s, %s) RETURNING id, title, content, created_at, updated_at",
        (title, content)
    )
    new_article = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        'id': new_article[0],
        'title': new_article[1],
        'content': new_article[2],
        'created_at': new_article[3].isoformat(),
        'updated_at': new_article[4].isoformat()
    }), 201


@app.route('/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE articles SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, title, content, created_at, updated_at",
        (title, content, article_id))
    updated_article = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if updated_article is None:
        return jsonify({'error': 'Article not found'}), 404

    return jsonify({
        'id': updated_article[0],
        'title': updated_article[1],
        'content': updated_article[2],
        'created_at': updated_article[3].isoformat(),
        'updated_at': updated_article[4].isoformat()
    })


@app.route('/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM articles WHERE id = %s RETURNING id", (article_id,))
    deleted_article = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if deleted_article is None:
        return jsonify({'error': 'Article not found'}), 404

    return jsonify({'message': 'Article deleted successfully'}), 200


if __name__ == '__main__':
    app.run(debug=True)
