
import sqlite3
from datetime import datetime

DB_NAME = "smart_retail.db"


def koneksi():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = koneksi()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_produk TEXT NOT NULL,
            harga_modal INTEGER NOT NULL,
            harga_jual INTEGER NOT NULL,
            stok INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL,
            total_bayar INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS detail_transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_transaksi INTEGER NOT NULL,
            id_produk INTEGER NOT NULL,
            jumlah INTEGER NOT NULL,
            subtotal INTEGER NOT NULL
        )
    """)

    # Akun login
    cur.execute("""
        INSERT OR IGNORE INTO users(username, password, role)
        VALUES (?, ?, ?)
    """, ("admin", "kelompok 8", "admin"))

    cur.execute("""
        INSERT OR IGNORE INTO users(username, password, role)
        VALUES (?, ?, ?)
    """, ("kasir", "kelompok 8", "kasir"))

    conn.commit()
    conn.close()


def rupiah(angka):
    return "Rp" + f"{angka:,}".replace(",", ".")


def login():
    print("\n========== LOGIN SMART-RETAIL ==========")
    username = input("Username : ")
    password = input("Password : ")

    conn = koneksi()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, role FROM users WHERE username=? AND password=?",
        (username, password)
    )
    user = cur.fetchone()
    conn.close()

    if user:
        print(f"\nLogin berhasil. Selamat datang, {user[0]}!")
        return user

    print("\nUsername atau password salah.")
    return None


def lihat_produk():
    conn = koneksi()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nama_produk, harga_modal, harga_jual, stok
        FROM produk ORDER BY id
    """)
    data = cur.fetchall()
    conn.close()

    print("\n========== DAFTAR PRODUK ==========")

    if not data:
        print("Belum ada produk.")
        return

    print(f"{'ID':<5}{'Nama Produk':<22}{'Modal':<15}{'Harga Jual':<15}{'Stok'}")
    print("-" * 72)

    for p in data:
        print(
            f"{p[0]:<5}{p[1]:<22}"
            f"{rupiah(p[2]):<15}{rupiah(p[3]):<15}{p[4]}"
        )


def tambah_produk():
    print("\n========== TAMBAH PRODUK ==========")

    nama = input("Nama produk : ")

    try:
        modal = int(input("Harga modal : "))
        jual = int(input("Harga jual  : "))
        stok = int(input("Stok        : "))

        if modal < 0 or jual < 0 or stok < 0:
            raise ValueError

    except ValueError:
        print("Input angka tidak valid.")
        return

    conn = koneksi()
    conn.execute("""
        INSERT INTO produk(nama_produk, harga_modal, harga_jual, stok)
        VALUES (?, ?, ?, ?)
    """, (nama, modal, jual, stok))
    conn.commit()
    conn.close()

    print("Produk berhasil ditambahkan.")


def update_produk():
    lihat_produk()

    try:
        pid = int(input("\nID produk yang ingin diubah: "))
    except ValueError:
        print("ID tidak valid.")
        return

    conn = koneksi()
    cur = conn.cursor()
    cur.execute("SELECT * FROM produk WHERE id=?", (pid,))
    produk = cur.fetchone()

    if not produk:
        print("Produk tidak ditemukan.")
        conn.close()
        return

    nama = input(f"Nama [{produk[1]}]: ") or produk[1]

    try:
        harga_input = input(f"Harga jual [{produk[3]}]: ")
        stok_input = input(f"Stok [{produk[4]}]: ")

        harga = int(harga_input) if harga_input else produk[3]
        stok = int(stok_input) if stok_input else produk[4]

        if harga < 0 or stok < 0:
            raise ValueError

    except ValueError:
        print("Input tidak valid.")
        conn.close()
        return

    cur.execute("""
        UPDATE produk
        SET nama_produk=?, harga_jual=?, stok=?
        WHERE id=?
    """, (nama, harga, stok, pid))

    conn.commit()
    conn.close()

    print("Produk berhasil diperbarui.")


def hapus_produk():
    lihat_produk()

    try:
        pid = int(input("\nID produk yang ingin dihapus: "))
    except ValueError:
        print("ID tidak valid.")
        return

    konfirmasi = input("Yakin hapus produk? (Y/T): ").upper()

    if konfirmasi != "Y":
        print("Penghapusan dibatalkan.")
        return

    conn = koneksi()
    cur = conn.cursor()
    cur.execute("DELETE FROM produk WHERE id=?", (pid,))
    berhasil = cur.rowcount > 0
    conn.commit()
    conn.close()

    if berhasil:
        print("Produk berhasil dihapus.")
    else:
        print("Produk tidak ditemukan.")


def cari_produk():
    kata = input("\nMasukkan nama atau ID produk: ")

    conn = koneksi()
    cur = conn.cursor()

    if kata.isdigit():
        cur.execute("""
            SELECT id, nama_produk, harga_jual, stok
            FROM produk WHERE id=?
        """, (int(kata),))
    else:
        cur.execute("""
            SELECT id, nama_produk, harga_jual, stok
            FROM produk WHERE nama_produk LIKE ?
        """, ("%" + kata + "%",))

    data = cur.fetchall()
    conn.close()

    print("\n========== HASIL PENCARIAN ==========")

    if not data:
        print("Produk tidak ditemukan.")
        return

    for p in data:
        print(
            f"ID: {p[0]} | {p[1]} | "
            f"Harga: {rupiah(p[2])} | Stok: {p[3]}"
        )


def transaksi_penjualan():
    keranjang = []

    while True:
        lihat_produk()

        try:
            pid = int(input("\nID barang (0 = selesai): "))
        except ValueError:
            print("ID harus berupa angka.")
            continue

        if pid == 0:
            break

        try:
            jumlah = int(input("Jumlah beli: "))

            if jumlah <= 0:
                raise ValueError

        except ValueError:
            print("Jumlah tidak valid.")
            continue

        conn = koneksi()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nama_produk, harga_jual, stok
            FROM produk WHERE id=?
        """, (pid,))
        produk = cur.fetchone()
        conn.close()

        if not produk:
            print("Produk tidak ditemukan.")
            continue

        jumlah_sebelumnya = sum(
            item["jumlah"] for item in keranjang
            if item["id"] == pid
        )

        if jumlah + jumlah_sebelumnya > produk[3]:
            print(f"Stok tidak mencukupi. Stok tersedia: {produk[3]}")
            continue

        item_lama = next(
            (item for item in keranjang if item["id"] == pid),
            None
        )

        if item_lama:
            item_lama["jumlah"] += jumlah
            item_lama["subtotal"] = (
                item_lama["jumlah"] * produk[2]
            )
        else:
            keranjang.append({
                "id": produk[0],
                "nama": produk[1],
                "harga": produk[2],
                "jumlah": jumlah,
                "subtotal": jumlah * produk[2]
            })

        lagi = input("Tambah barang lain? (Y/T): ").upper()

        if lagi != "Y":
            break

    if not keranjang:
        print("Keranjang kosong.")
        return

    total = sum(item["subtotal"] for item in keranjang)

    print("\n========== STRUK SMART-RETAIL ==========")

    for item in keranjang:
        print(
            f"{item['nama']} | {item['jumlah']} x "
            f"{rupiah(item['harga'])} = {rupiah(item['subtotal'])}"
        )

    print("----------------------------------------")
    print("TOTAL:", rupiah(total))

    try:
        bayar = int(input("Uang bayar: "))

        if bayar < total:
            print("Uang pembayaran kurang.")
            return

    except ValueError:
        print("Pembayaran tidak valid.")
        return

    kembalian = bayar - total

    conn = koneksi()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO transaksi(tanggal, total_bayar)
        VALUES (?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total
    ))

    id_transaksi = cur.lastrowid

    for item in keranjang:
        cur.execute("""
            INSERT INTO detail_transaksi
            (id_transaksi, id_produk, jumlah, subtotal)
            VALUES (?, ?, ?, ?)
        """, (
            id_transaksi,
            item["id"],
            item["jumlah"],
            item["subtotal"]
        ))

        cur.execute("""
            UPDATE produk
            SET stok = stok - ?
            WHERE id=?
        """, (item["jumlah"], item["id"]))

    conn.commit()
    conn.close()

    print("Kembalian:", rupiah(kembalian))
    print("Transaksi berhasil disimpan.")


def riwayat_transaksi():
    conn = koneksi()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, tanggal, total_bayar
        FROM transaksi
        ORDER BY id DESC
    """)

    data = cur.fetchall()
    conn.close()

    print("\n========== RIWAYAT TRANSAKSI ==========")

    if not data:
        print("Belum ada transaksi.")
        return

    for t in data:
        print(
            f"ID: {t[0]} | Tanggal: {t[1]} | "
            f"Total: {rupiah(t[2])}"
        )


def laporan_penjualan():
    conn = koneksi()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*), COALESCE(SUM(total_bayar), 0)
        FROM transaksi
    """)

    jumlah_transaksi, pendapatan = cur.fetchone()

    print("\n========== LAPORAN PENJUALAN ==========")
    print("Jumlah transaksi :", jumlah_transaksi)
    print("Total pendapatan :", rupiah(pendapatan))

    cur.execute("""
        SELECT p.nama_produk, SUM(d.jumlah) AS jumlah
        FROM detail_transaksi d
        JOIN produk p ON p.id = d.id_produk
        GROUP BY d.id_produk
        ORDER BY jumlah DESC
        LIMIT 1
    """)

    terlaris = cur.fetchone()

    if terlaris:
        print(
            f"Produk terlaris   : {terlaris[0]} "
            f"({terlaris[1]} pcs)"
        )
    else:
        print("Produk terlaris   : Belum ada data")

    cur.execute("""
        SELECT nama_produk, stok
        FROM produk
        WHERE stok < 10
        ORDER BY stok
    """)

    stok_menipis = cur.fetchall()

    print("\nProduk dengan stok < 10:")

    if stok_menipis:
        for p in stok_menipis:
            print(f"- {p[0]} : {p[1]} pcs")
    else:
        print("Tidak ada.")

    conn.close()


def menu_kelola_produk():
    while True:
        print("\n========== KELOLA PRODUK ==========")
        print("1. Tambah Produk")
        print("2. Lihat Produk")
        print("3. Update Produk")
        print("4. Hapus Produk")
        print("5. Kembali")

        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            tambah_produk()
        elif pilihan == "2":
            lihat_produk()
        elif pilihan == "3":
            update_produk()
        elif pilihan == "4":
            hapus_produk()
        elif pilihan == "5":
            break
        else:
            print("Pilihan tidak tersedia.")


def menu_admin():
    while True:
        print("\n========== MENU ADMIN ==========")
        print("1. Kelola Produk")
        print("2. Transaksi Penjualan")
        print("3. Cari Produk")
        print("4. Laporan Penjualan")
        print("5. Riwayat Transaksi")
        print("6. Logout")

        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            menu_kelola_produk()
        elif pilihan == "2":
            transaksi_penjualan()
        elif pilihan == "3":
            cari_produk()
        elif pilihan == "4":
            laporan_penjualan()
        elif pilihan == "5":
            riwayat_transaksi()
        elif pilihan == "6":
            break
        else:
            print("Pilihan tidak tersedia.")


def menu_kasir():
    while True:
        print("\n========== MENU KASIR ==========")
        print("1. Transaksi Penjualan")
        print("2. Lihat Produk")
        print("3. Cari Produk")
        print("4. Logout")

        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            transaksi_penjualan()
        elif pilihan == "2":
            lihat_produk()
        elif pilihan == "3":
            cari_produk()
        elif pilihan == "4":
            break
        else:
            print("Pilihan tidak tersedia.")


def main():
    init_db()

    print("\n========================================")
    print("       SMART-RETAIL TOKO MAJU JAYA")
    print("========================================")

    while True:
        user = login()

        if not user:
            ulang = input("Coba login lagi? (Y/T): ").upper()

            if ulang != "Y":
                break

            continue

        if user[1] == "admin":
            menu_admin()
        else:
            menu_kasir()

        lagi = input("\nLogin kembali? (Y/T): ").upper()

        if lagi != "Y":
            print("Terima kasih telah menggunakan Smart-Retail.")
            break


if __name__ == "__main__":
    main()
