import os
import pymssql
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_connection():
    return pymssql.connect(
        server=os.getenv('SQLSERVER_HOST'),
        database=os.getenv('SQLSERVER_DB'),
        user=os.getenv('SQLSERVER_USER'),
        password=os.getenv('SQLSERVER_PASSWORD')
    )

@app.route('/stock/<sku>', methods=['GET'])
def get_stock(sku):
    try:
        parts = sku.split('-')
        referencia = parts[0]
        estado = parts[1]
        color = parts[2]
        
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT COUNT(s.SERIE) AS STOCK, MAX(s.VALOR) AS PRECIO
        FROM MTSERIES s WITH (NOLOCK)
        INNER JOIN XMYCT_TECNICO_SERIES ts WITH (NOLOCK) ON s.SERIE = ts.XSERIE
        WHERE s.EXISTE = 1
        AND s.BODEGA IN ('BM', 'TM', 'TB', 'BB', 'BCAL', 'BNQS')
        AND s.CODIGO LIKE ? + '%'
        AND ts.XESTADO = ?
        AND ts.XCOLOR = ?
        """
        
        cursor.execute(query, (referencia, estado, color))
        row = cursor.fetchone()
        
        result = {
            'STOCK': row[0],
            'PRECIO': float(row[1]) if row[1] else 0
        }
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
