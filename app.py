import os
import pyodbc
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('SQLSERVER_HOST')};"
        f"DATABASE={os.getenv('SQLSERVER_DB')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

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

@app.route('/stock', methods=['GET'])
def get_all_stock():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT s.CODIGO, ts.XESTADO, ts.XCOLOR, COUNT(s.SERIE) AS STOCK, MAX(s.VALOR) AS PRECIO
        FROM MTSERIES s WITH (NOLOCK)
        INNER JOIN XMYCT_TECNICO_SERIES ts WITH (NOLOCK) ON s.SERIE = ts.XSERIE
        WHERE s.EXISTE = 1
        AND s.BODEGA IN ('BM', 'TM', 'TB', 'BB', 'BCAL', 'BNQS')
        GROUP BY s.CODIGO, ts.XESTADO, ts.XCOLOR
        ORDER BY s.CODIGO
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        result = [
            {'CODIGO': r[0], 'ESTADO': r[1], 'COLOR': r[2], 'STOCK': r[3], 'PRECIO': float(r[4]) if r[4] else 0}
            for r in rows
        ]

        cursor.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
