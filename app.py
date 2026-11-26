import os

import pymysql
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_connection():
    """Buat koneksi baru ke MySQL. Konfigurasi dibaca dari environment variable."""
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "peminjaman_buku"),
        cursorclass=pymysql.cursors.DictCursor,
    )


STATUS_VALID = ("dipinjam", "dikembalikan")


def validate_loan(data, partial=False):
    """Kembalikan (data_bersih, pesan_error). Kalau partial=True, field boleh sebagian."""
    if not isinstance(data, dict):
        return None, "Body harus berupa JSON object"
    fields = ("judul_buku", "peminjam", "tanggal_pinjam", "status")
    clean = {k: data[k] for k in fields if k in data}
    if not partial:
        for k in ("judul_buku", "peminjam", "tanggal_pinjam"):
            if not clean.get(k):
                return None, f"Field '{k}' wajib diisi"
        clean.setdefault("status", "dipinjam")
    elif not clean:
        return None, "Tidak ada field yang diubah"
    if "status" in clean and clean["status"] not in STATUS_VALID:
        return None, "Status harus 'dipinjam' atau 'dikembalikan'"
    return clean, None


def serialize(row):
    """Ubah tanggal jadi string supaya bisa dijadikan JSON."""
    row["tanggal_pinjam"] = row["tanggal_pinjam"].isoformat()
    return row


@app.route("/health", methods=["GET"])
def health():
    """Cek cepat bahwa aplikasi hidup dan bisa menjangkau database."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify({"status": "ok"})
    finally:
        conn.close()


@app.route("/loans", methods=["POST"])
def create_loan():
    data, error = validate_loan(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO loans (judul_buku, peminjam, tanggal_pinjam, status) "
                "VALUES (%s, %s, %s, %s)",
                (data["judul_buku"], data["peminjam"], data["tanggal_pinjam"], data["status"]),
            )
            new_id = cur.lastrowid
        conn.commit()
        return jsonify({"id": new_id, **data}), 201
    finally:
        conn.close()


@app.route("/loans", methods=["GET"])
def list_loans():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM loans ORDER BY id")
            rows = cur.fetchall()
        return jsonify([serialize(r) for r in rows])
    finally:
        conn.close()


@app.route("/loans/<int:loan_id>", methods=["PUT"])
def update_loan(loan_id):
    data, error = validate_loan(request.get_json(silent=True), partial=True)
    if error:
        return jsonify({"error": error}), 400
    assignments = ", ".join(f"{k} = %s" for k in data)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE loans SET {assignments} WHERE id = %s", (*data.values(), loan_id))
            cur.execute("SELECT * FROM loans WHERE id = %s", (loan_id,))
            row = cur.fetchone()
        if row is None:
            return jsonify({"error": "Data peminjaman tidak ditemukan"}), 404
        conn.commit()
        return jsonify(serialize(row))
    finally:
        conn.close()


@app.route("/loans/<int:loan_id>", methods=["DELETE"])
def delete_loan(loan_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            affected = cur.execute("DELETE FROM loans WHERE id = %s", (loan_id,))
        conn.commit()
        if affected == 0:
            return jsonify({"error": "Data peminjaman tidak ditemukan"}), 404
        return jsonify({"message": "Data peminjaman dihapus"})
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
