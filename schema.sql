-- Skema database peminjaman buku (MySQL)
CREATE DATABASE IF NOT EXISTS peminjaman_buku;
USE peminjaman_buku;

CREATE TABLE IF NOT EXISTS loans (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    judul_buku     VARCHAR(150) NOT NULL,
    peminjam       VARCHAR(100) NOT NULL,
    tanggal_pinjam DATE         NOT NULL,
    status         VARCHAR(20)  NOT NULL DEFAULT 'dipinjam'
);
