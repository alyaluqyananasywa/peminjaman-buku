# Deployment

Dokumen ini mencatat langkah deployment yang benar-benar dikerjakan di AWS Academy Sandbox
(region us-east-1). Track A: EC2 + RDS MySQL, dengan perluasan Docker (Track B, sebagian).

Catatan lingkungan: IAM bersifat read-only, jadi EC2 memakai role bawaan **LabRole** lewat
**LabInstanceProfile**. Sesi berlangsung 3 jam dan semua resource dihapus saat sesi berakhir.

## 1. Jaringan
- VPC: default VPC (`vpc-03b90be9fec2cb24f`).
- Security group `peminjaman-ec2-sg`: inbound HTTP 80 dari 0.0.0.0/0. Port 22 tidak dibuka karena
  akses ke server lewat Session Manager.
- Security group `peminjaman-rds-sg`: inbound MySQL/Aurora 3306 dengan source `peminjaman-ec2-sg`.

## 2. Database (RDS MySQL)
- MySQL 8.4.11, template Dev/Test, Single-AZ, instance `db.t3.micro`, gp2 20 GiB.
- Identifier `peminjaman-db`, master user `admin`, initial database `peminjaman_buku`.
- Public access: No. Security group: `peminjaman-rds-sg`. Enhanced Monitoring dimatikan
  (tidak didukung sandbox), Database Insights mode Standard.
- Status Available ditunjukkan di halaman Summary, endpoint ada di tab Connectivity & security.

## 3. Server aplikasi (EC2)
- Amazon Linux 2023, `t3.micro`, security group `peminjaman-ec2-sg`, public IP otomatis.
- IAM instance profile: `LabInstanceProfile`. Masuk lewat Connect > Session Manager.

## 4. Tes koneksi EC2 ke RDS
```bash
sudo dnf install -y mariadb105
mysql -h <endpoint-rds> -u admin -p -e "CREATE DATABASE IF NOT EXISTS peminjaman_buku; USE peminjaman_buku; CREATE TABLE IF NOT EXISTS loans (...); SHOW TABLES;"
```
Perintah `CREATE TABLE` berisi isi `schema.sql`. Hasilnya menampilkan tabel `loans`, jadi koneksi
dari EC2 ke RDS berhasil.

## 5. Menjalankan aplikasi di EC2
Repo tidak di-clone. `requirements.txt` dan `app.py` dibuat langsung di server dengan `cat > file <<'EOF'`
lewat terminal Session Manager, lalu diverifikasi dengan `sha256sum` dan `python3 -m py_compile app.py`.
```bash
sudo dnf install -y python3-pip
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
export DB_HOST=<endpoint-rds> DB_USER=admin DB_NAME=peminjaman_buku PORT=80
read -s -p "DB password: " DB_PASSWORD; export DB_PASSWORD
nohup sudo -E venv/bin/python app.py > app.log 2>&1 &
```
Aplikasi memakai server bawaan Flask, yang cukup untuk tahap awal ini. Untuk penggunaan sebenarnya
perlu server produksi seperti gunicorn.

## 6. Tes endpoint
```bash
curl localhost/health
curl -X POST localhost/loans -H "Content-Type: application/json" -d '{"judul_buku":"Laskar Pelangi","peminjam":"Dina","tanggal_pinjam":"2026-11-26"}'
curl localhost/loans
curl -X PUT localhost/loans/1 -H "Content-Type: application/json" -d '{"status":"dikembalikan"}'
curl -X DELETE localhost/loans/1
```
Dari browser, `http://<ip-publik-ec2>/health` mengembalikan `{"status":"ok"}`.

## 7. Perluasan Docker (Track B, sebagian)
```bash
sudo pkill -f "app.py"
sudo dnf install -y docker && sudo systemctl enable --now docker
sudo docker build -t peminjaman-api:v1 .
sudo docker run -d --name peminjaman-api -p 80:80 -e DB_HOST -e DB_USER -e DB_PASSWORD -e DB_NAME peminjaman-api:v1
```
Image berhasil dibuild dan container berjalan dengan koneksi ke RDS yang sama. Tes `health` dan keempat
operasi `/loans` berhasil dari container.

Push ke ECR belum berhasil: `aws ecr create-repository` dari EC2 ditolak (`AccessDeniedException`,
LabRole tidak memiliki izin `ecr:CreateRepository`), sehingga image belum tersimpan di ECR.

## 8. Setelah selesai
Sesi sandbox berakhir dan semua resource dihapus otomatis.
