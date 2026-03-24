import os
import pyodbc
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Diccionario color completo -> abreviación BD
COLOR_MAP = {
    'AMARILLO': 'AM', 'AMARILLA': 'AM',
    'AZUL': 'AZ',
    'BLANCO': 'BL', 'BLANCA': 'BL',
    'DORADO': 'DO', 'DORADA': 'DO', 'ORO': 'DO',
    'GRIS': 'GR',
    'LILA': 'LI', 'LILA': 'LI',
    'MORADO': 'MO', 'MORADA': 'MO', 'PURPURA': 'MO',
    'NATURAL': 'NA',
    'NEGRO': 'NG', 'NEGRA': 'NG',
    'NARANJA': 'OR', 'ORANGE': 'OR',
    'ROJO': 'RO', 'ROJA': 'RO',
    'ROSADO': 'RS', 'ROSA': 'RS',
    'TITANIO DESERT': 'TTD', 'DESERT': 'TTD',
    'TITANIO NATURAL': 'TTN', 'TITANIO': 'TTN',
    'VERDE': 'VE',
}

# Diccionario estado completo -> abreviación BD
ESTADO_MAP = {
    'A': 'A', 'ACTIVO': 'A', 'EXCELENTE': 'A',
    'AA': 'AA', 'COMO NUEVO': 'AA',
    'B': 'B', 'BUENO': 'B', 'USADO': 'B',
    'B1': 'B1',
    'C': 'C', 'REGULAR': 'C',
    'NU': 'NU', 'NUEVO': 'NU', 'N': 'NU',
}

def traducir_color(color):
    c = color.strip().upper()
    return COLOR_MAP.get(c, c)  # si no encuentra, devuelve el mismo valor

def traducir_estado(estado):
    e = estado.strip().upper()
    return ESTADO_MAP.get(e, e)

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
        referencia = parts[0].strip()
        estado = traducir_estado(parts[1])
        color = traducir_color(parts[2])

        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT COUNT(s.SERIE) AS STOCK, MAX(s.VALOR) AS PRECIO
        FROM MTSERIES s WITH (NOLOCK)
        INNER JOIN XMYCT_TECNICO_SERIES ts WITH (NOLOCK) ON s.SERIE = ts.XSERIE
        WHERE s.EXISTE = 1
        AND s.BODEGA IN ('BM', 'TM', 'TB', 'BB', 'BCAL', 'BNQS')
        AND RTRIM(s.CODIGO) LIKE ? + '%'
        AND RTRIM(ts.XESTADO) = ?
        AND RTRIM(ts.XCOLOR) = ?
        """

        cursor.execute(query, (referencia, estado, color))
        row = cursor.fetchone()

        result = {
            'SKU': sku,
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
        SELECT RTRIM(s.CODIGO), RTRIM(ts.XESTADO), RTRIM(ts.XCOLOR), COUNT(s.SERIE) AS STOCK, MAX(s.VALOR) AS PRECIO
        FROM MTSERIES s WITH (NOLOCK)
        INNER JOIN XMYCT_TECNICO_SERIES ts WITH (NOLOCK) ON s.SERIE = ts.XSERIE
        WHERE s.EXISTE = 1
        AND s.BODEGA IN ('BM', 'TM', 'TB', 'BB', 'BCAL', 'BNQS')
        GROUP BY RTRIM(s.CODIGO), RTRIM(ts.XESTADO), RTRIM(ts.XCOLOR)
        ORDER BY RTRIM(s.CODIGO)
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
