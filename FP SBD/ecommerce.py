import mysql.connector
import pymongo
from datetime import datetime
from bson import ObjectId

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Isi password MySQL kamu
            database='ecommerce',
            port=3306,
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            print("✅ Berhasil terhubung ke database MySQL.")
            return connection
    except mysql.connector.Error as e:
        print(f"❌ Gagal terhubung ke database: {e}")
        return None

# MongoDB Connection
def create_mongo_connection():
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["E-Commerce_FP"]  # Changed to match existing database name
        print("✅ Berhasil terhubung ke MongoDB.")
        return db
    except Exception as e:
        print(f"❌ Gagal terhubung ke MongoDB: {e}")
        return None

# REGISTER - Tambah User Baru
def register_user():
    name = input("Masukkan Nama: ")
    email = input("Masukkan Email: ")
    password = input("Masukkan Password: ")
    phone_number = input("Masukkan Nomor Telepon: ")
    address = input("Masukkan Alamat: ")
    
    while True:
        role = input("Pilih role (1: Customer, 2: Worker): ")
        if role in ['1', '2']:
            role = 'customer' if role == '1' else 'worker'
            break
        print("❌ Pilihan tidak valid! Pilih 1 atau 2.")

    try:
        connection = create_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            print("❌ Email sudah terdaftar. Gunakan email lain.")
            return

        query = """
            INSERT INTO users (name, email, password, phone_number, address, role) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, password, phone_number, address, role))
        connection.commit()

        print("✅ Registrasi berhasil! Silakan login.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# LOGIN - Autentikasi User
def login_user():
    email = input("Masukkan Email: ")
    password = input("Masukkan Password: ")

    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT user_id, name, email, phone_number, address, role 
            FROM users 
            WHERE email = %s AND password = %s
        """
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            print(f"\n✅ Login berhasil! Selamat datang, {user['name']}")
            print(f"Email: {user['email']}")
            print(f"No. Telepon: {user['phone_number']}")
            print(f"Alamat: {user['address']}")
            return user['user_id'], user['name'], user['role']
        else:
            print("❌ Email atau password salah!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

    return None, None, None

# Tampilkan Kategori
def tampilkan_kategori():
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get main categories
        cursor.execute("SELECT * FROM categories WHERE parent_id IS NULL")
        main_categories = cursor.fetchall()
        
        print("\n📑 Daftar Kategori:")
        for category in main_categories:
            print(f"ID: {category['category_id']}, Nama: {category['name']}")
            
            # Get subcategories
            cursor.execute("SELECT * FROM categories WHERE parent_id = %s", (category['category_id'],))
            subcategories = cursor.fetchall()
            
            for subcategory in subcategories:
                print(f"  ├─ ID: {subcategory['category_id']}, Nama: {subcategory['name']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# CREATE - Tambah Produk
def tambah_produk():
    try:
        # Show categories first
        print("\nKategori yang tersedia:")
        tampilkan_kategori()
        
        nama = input("\nMasukkan nama produk: ")
        deskripsi = input("Masukkan deskripsi produk: ")
        
        # Validate price input
        while True:
            try:
                harga = float(input("Masukkan harga produk: "))
                if harga <= 0:
                    print("❌ Harga harus lebih dari 0!")
                    continue
                break
            except ValueError:
                print("❌ Harga harus berupa angka!")
        
        # Validate stock input
        while True:
            try:
                stok = int(input("Masukkan stok produk: "))
                if stok < 0:
                    print("❌ Stok tidak boleh negatif!")
                    continue
                break
            except ValueError:
                print("❌ Stok harus berupa angka!")
        
        # Validate category input
        connection = create_connection()
        cursor = connection.cursor()
        
        while True:
            try:
                kategori_id = int(input("Masukkan kategori ID: "))
                
                # Check if category exists
                cursor.execute("SELECT * FROM categories WHERE category_id = %s", (kategori_id,))
                if not cursor.fetchone():
                    print("❌ Kategori tidak ditemukan! Silakan pilih ID kategori yang tersedia.")
                    continue
                break
            except ValueError:
                print("❌ Kategori ID harus berupa angka!")
        
        # Insert product
        query = """
            INSERT INTO product (name, description, price, stock, category_id, date_posted) 
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        values = (nama, deskripsi, harga, stok, kategori_id)
        
        cursor.execute(query, values)
        connection.commit()
        
        print("✅ Produk berhasil ditambahkan!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# READ - Tampilkan Semua Produk
def tampilkan_produk():
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get products from MySQL
        query = """
            SELECT product_id, name, price, stock, date_posted 
            FROM product 
            ORDER BY date_posted DESC
        """
        cursor.execute(query)
        products = cursor.fetchall()
        
        # Get ratings from MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        print("\n📦 Daftar Produk: ")
        for product in products:
            # Calculate average rating
            reviews = db.Review.find({"product_id": product['product_id']})  # Changed collection name
            total_rating = 0
            review_count = 0
            
            for review in reviews:
                total_rating += review['rating']
                review_count += 1
                
            avg_rating = total_rating / review_count if review_count > 0 else 0
            
            print(f"ID: {product['product_id']}")
            print(f"Nama: {product['name']}")
            print(f"Harga: Rp {product['price']:,.2f}")
            print(f"Stok: {product['stock']}")
            print(f"Tanggal Posting: {product['date_posted']}")
            print(f"Rating: {avg_rating:.1f} ⭐ ({review_count} review)")
            print("-" * 40)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# UPDATE - Edit Produk
def edit_produk():
    product_id = int(input("Masukkan ID produk yang ingin diupdate: "))
    nama = input("Masukkan nama baru produk: ")
    deskripsi = input("Masukkan deskripsi baru produk: ")
    harga = float(input("Masukkan harga baru produk: "))
    stok = int(input("Masukkan stok baru produk: "))
    kategori_id = int(input("Masukkan kategori ID baru: "))

    try:
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        UPDATE product
        SET name = %s, description = %s, price = %s, stock = %s, category_id = %s, date_posted = NOW()
        WHERE product_id = %s
        """
        values = (nama, deskripsi, harga, stok, kategori_id, product_id)

        cursor.execute(query, values)
        connection.commit()

        print("✅ Produk berhasil diupdate!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# DELETE - Hapus Produk
def hapus_produk():
    product_id = int(input("Masukkan ID produk yang ingin dihapus: "))

    try:
        connection = create_connection()
        cursor = connection.cursor()

        query = "DELETE FROM product WHERE product_id = %s"
        cursor.execute(query, (product_id,))
        connection.commit()

        print("✅ Produk berhasil dihapus!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Beli Produk
def beli_produk(user_id):
    tampilkan_produk()
    
    try:
        product_id = int(input("\nMasukkan ID produk yang ingin dibeli: "))
        jumlah = int(input("Masukkan jumlah yang ingin dibeli: "))
        
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check product availability
        cursor.execute("SELECT * FROM product WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            print("❌ Produk tidak ditemukan!")
            return
            
        if product['stock'] < jumlah:
            print("❌ Stok tidak mencukupi!")
            return
            
        total_harga = product['price'] * jumlah
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (user_id, product_id, quantity, total_price, order_date)
            VALUES (%s, %s, %s, %s, NOW())
        """, (user_id, product_id, jumlah, total_harga))
        
        # Update stock
        cursor.execute("""
            UPDATE product
            SET stock = stock - %s
            WHERE product_id = %s
        """, (jumlah, product_id))
        
        connection.commit()
        print(f"✅ Pembelian berhasil! Total harga: Rp {total_harga:,.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Lihat Riwayat Pembelian
def lihat_riwayat_pembelian(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT o.order_id, p.name, o.quantity, o.total_price, o.order_date
            FROM orders o
            JOIN product p ON o.product_id = p.product_id
            WHERE o.user_id = %s
            ORDER BY o.order_date DESC
        """
        cursor.execute(query, (user_id,))
        orders = cursor.fetchall()
        
        if not orders:
            print("Belum ada riwayat pembelian.")
            return
            
        print("\n📋 Riwayat Pembelian:")
        for order in orders:
            print(f"Order ID: {order['order_id']}")
            print(f"Produk: {order['name']}")
            print(f"Jumlah: {order['quantity']}")
            print(f"Total Harga: Rp {order['total_price']:,.2f}")
            print(f"Tanggal: {order['order_date']}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Tambah ke Trolley
def tambah_ke_trolley(user_id):
    tampilkan_produk()
    
    try:
        product_id = int(input("\nMasukkan ID produk yang ingin ditambah ke trolley: "))
        jumlah = int(input("Masukkan jumlah yang ingin ditambah: "))
        
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check product availability
        cursor.execute("SELECT * FROM product WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            print("❌ Produk tidak ditemukan!")
            return
            
        if product['stock'] < jumlah:
            print("❌ Stok tidak mencukupi!")
            return
        
        # Check if product already in trolley
        cursor.execute("""
            SELECT * FROM trolley 
            WHERE user_id = %s AND product_id = %s
        """, (user_id, product_id))
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Update quantity if product already in trolley
            cursor.execute("""
                UPDATE trolley 
                SET quantity = quantity + %s
                WHERE user_id = %s AND product_id = %s
            """, (jumlah, user_id, product_id))
        else:
            # Add new item to trolley
            cursor.execute("""
                INSERT INTO trolley (user_id, product_id, quantity, added_at)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, product_id, jumlah))
        
        connection.commit()
        print("✅ Produk berhasil ditambahkan ke trolley!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Lihat Isi Trolley
def lihat_trolley(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT t.trolley_id, p.name, p.price, t.quantity, (p.price * t.quantity) as subtotal, t.added_at
            FROM trolley t
            JOIN product p ON t.product_id = p.product_id
            WHERE t.user_id = %s
            ORDER BY t.added_at DESC
        """
        cursor.execute(query, (user_id,))
        items = cursor.fetchall()
        
        if not items:
            print("Trolley masih kosong.")
            return False
            
        print("\n🛒 Isi Trolley:")
        total = 0
        for item in items:
            print(f"ID Trolley: {item['trolley_id']}")
            print(f"Produk: {item['name']}")
            print(f"Harga: Rp {item['price']:,.2f}")
            print(f"Jumlah: {item['quantity']}")
            print(f"Subtotal: Rp {item['subtotal']:,.2f}")
            print(f"Ditambahkan pada: {item['added_at']}")
            print("-" * 40)
            total += item['subtotal']
            
        print(f"\nTotal: Rp {total:,.2f}")
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

# Ubah Jumlah di Trolley
def ubah_jumlah_trolley(user_id):
    if not lihat_trolley(user_id):
        return
        
    try:
        trolley_id = int(input("\nMasukkan ID Trolley yang ingin diubah: "))
        jumlah_baru = int(input("Masukkan jumlah baru: "))
        
        if jumlah_baru <= 0:
            print("❌ Jumlah harus lebih dari 0!")
            return
            
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check if trolley item exists and belongs to user
        cursor.execute("""
            SELECT t.*, p.stock 
            FROM trolley t
            JOIN product p ON t.product_id = p.product_id
            WHERE t.trolley_id = %s AND t.user_id = %s
        """, (trolley_id, user_id))
        item = cursor.fetchone()
        
        if not item:
            print("❌ Item trolley tidak ditemukan!")
            return
            
        if jumlah_baru > item['stock']:
            print("❌ Stok tidak mencukupi!")
            return
            
        cursor.execute("""
            UPDATE trolley 
            SET quantity = %s
            WHERE trolley_id = %s AND user_id = %s
        """, (jumlah_baru, trolley_id, user_id))
        
        connection.commit()
        print("✅ Jumlah berhasil diubah!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Hapus dari Trolley
def hapus_dari_trolley(user_id):
    if not lihat_trolley(user_id):
        return
        
    try:
        trolley_id = int(input("\nMasukkan ID Trolley yang ingin dihapus: "))
        
        connection = create_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            DELETE FROM trolley 
            WHERE trolley_id = %s AND user_id = %s
        """, (trolley_id, user_id))
        
        if cursor.rowcount > 0:
            connection.commit()
            print("✅ Item berhasil dihapus dari trolley!")
        else:
            print("❌ Item trolley tidak ditemukan!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Checkout Trolley
def checkout_trolley(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get all items in trolley
        cursor.execute("""
            SELECT t.*, p.price, p.stock
            FROM trolley t
            JOIN product p ON t.product_id = p.product_id
            WHERE t.user_id = %s
        """, (user_id,))
        items = cursor.fetchall()
        
        if not items:
            print("❌ Trolley kosong!")
            return
            
        # Verify stock for all items
        for item in items:
            if item['quantity'] > item['stock']:
                print(f"❌ Stok tidak mencukupi untuk produk dengan ID {item['product_id']}!")
                return
        
        # Create orders and update stock
        for item in items:
            total_price = item['price'] * item['quantity']
            
            # Create order
            cursor.execute("""
                INSERT INTO orders (user_id, product_id, quantity, total_price, order_date)
                VALUES (%s, %s, %s, %s, NOW())
            """, (user_id, item['product_id'], item['quantity'], total_price))
            
            # Update stock
            cursor.execute("""
                UPDATE product
                SET stock = stock - %s
                WHERE product_id = %s
            """, (item['quantity'], item['product_id']))
        
        # Clear trolley
        cursor.execute("DELETE FROM trolley WHERE user_id = %s", (user_id,))
        
        connection.commit()
        print("✅ Checkout berhasil! Pesanan Anda telah dibuat.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Lihat Profil User
def lihat_profil(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT name, email, phone_number, address, role 
            FROM users 
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        if user:
            print("\n👤 Profil Anda:")
            print(f"Nama: {user['name']}")
            print(f"Email: {user['email']}")
            print(f"No. Telepon: {user['phone_number']}")
            print(f"Alamat: {user['address']}")
            print(f"Role: {user['role']}")
        else:
            print("❌ User tidak ditemukan!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Edit Profil User
def edit_profil(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        # Tampilkan data profil saat ini
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        print("\nEdit Profil (kosongkan jika tidak ingin mengubah):")
        name = input(f"Nama [{user['name']}]: ") or user['name']
        phone_number = input(f"No. Telepon [{user['phone_number']}]: ") or user['phone_number']
        address = input(f"Alamat [{user['address']}]: ") or user['address']
        
        # Update profil
        query = """
            UPDATE users 
            SET name = %s, phone_number = %s, address = %s
            WHERE user_id = %s
        """
        cursor.execute(query, (name, phone_number, address, user_id))
        connection.commit()

        print("✅ Profil berhasil diupdate!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Menu Worker
def menu_worker(user_id):
    while True:
        print("\n===== Menu Worker =====")
        print("1. Tambah Produk")
        print("2. Tampilkan Produk")
        print("3. Edit Produk")
        print("4. Hapus Produk")
        print("5. Lihat Profil")
        print("6. Edit Profil")
        print("7. Logout")

        pilihan = input("Pilih menu (1-7): ")

        if pilihan == '1':
            tambah_produk()
        elif pilihan == '2':
            tampilkan_produk()
        elif pilihan == '3':
            edit_produk()
        elif pilihan == '4':
            hapus_produk()
        elif pilihan == '5':
            lihat_profil(user_id)
        elif pilihan == '6':
            edit_profil(user_id)
        elif pilihan == '7':
            print("🔒 Logout berhasil.\n")
            break
        else:
            print("❌ Pilihan tidak valid!")

# Menu Trolley
def menu_trolley(user_id):
    while True:
        print("\n===== Menu Trolley =====")
        print("1. Lihat Isi Trolley")
        print("2. Tambah ke Trolley")
        print("3. Ubah Jumlah")
        print("4. Hapus dari Trolley")
        print("5. Checkout")
        print("6. Kembali ke Menu Utama")

        pilihan = input("Pilih menu (1-6): ")

        if pilihan == '1':
            lihat_trolley(user_id)
        elif pilihan == '2':
            tampilkan_produk()
            tambah_ke_trolley(user_id)
        elif pilihan == '3':
            ubah_jumlah_trolley(user_id)
        elif pilihan == '4':
            hapus_dari_trolley(user_id)
        elif pilihan == '5':
            checkout_trolley(user_id)
        elif pilihan == '6':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Menu Produk
def menu_produk(user_id):
    while True:
        print("\n===== Menu Produk =====")
        print("1. Lihat Semua Produk")
        print("2. Cari Produk")
        print("3. Filter Produk")
        print("4. Lihat Wishlist")
        print("5. Tambah ke Wishlist")
        print("6. Kembali ke Menu Utama")

        pilihan = input("Pilih menu (1-6): ")

        if pilihan == '1':
            tampilkan_produk()
        elif pilihan == '2':
            keyword = input("Masukkan kata kunci pencarian: ")
            cari_produk(keyword)
        elif pilihan == '3':
            filter_produk()
        elif pilihan == '4':
            lihat_wishlist(user_id)
        elif pilihan == '5':
            tambah_ke_wishlist(user_id)
        elif pilihan == '6':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Menu Profil
def menu_profil(user_id):
    while True:
        print("\n===== Menu Profil =====")
        print("1. Lihat Profil")
        print("2. Edit Profil")
        print("3. Riwayat Pembelian")
        print("4. Menu Review")
        print("5. Kembali ke Menu Utama")

        pilihan = input("Pilih menu (1-5): ")

        if pilihan == '1':
            lihat_profil(user_id)
        elif pilihan == '2':
            edit_profil(user_id)
        elif pilihan == '3':
            lihat_riwayat_pembelian(user_id)
        elif pilihan == '4':
            menu_review(user_id)
        elif pilihan == '5':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Menu Customer
def menu_customer(user_id):
    while True:
        print("\n===== MENU UTAMA CUSTOMER =====")
        print("1. Menu Produk")
        print("2. Menu Trolley")
        print("3. Menu Profil")
        print("4. Promo & Diskon")
        print("5. Logout")

        pilihan = input("Pilih menu (1-5): ")

        if pilihan == '1':
            menu_produk(user_id)
        elif pilihan == '2':
            menu_trolley(user_id)
        elif pilihan == '3':
            menu_profil(user_id)
        elif pilihan == '4':
            lihat_promo()
        elif pilihan == '5':
            print("🔒 Logout berhasil.\n")
            break
        else:
            print("❌ Pilihan tidak valid!")

# Menu Utama (Login dan Register)
def main_menu():
    while True:
        print("\n===== MENU UTAMA =====")
        print("1. Login")
        print("2. Register")
        print("3. Keluar")

        pilihan = input("Pilih menu (1-3): ")

        if pilihan == '1':
            user_id, name, role = login_user()
            if user_id:
                if role == 'worker':
                    menu_worker(user_id)
                else:
                    menu_customer(user_id)
        elif pilihan == '2':
            register_user()
        elif pilihan == '3':
            print("🚪 Keluar dari program...")
            break
        else:
            print("❌ Pilihan tidak valid!")

# Placeholder functions for new features (implement these later)
def cari_produk(keyword):
    print("🔍 Fitur pencarian produk akan segera hadir!")

def filter_produk():
    print("🔍 Fitur filter produk akan segera hadir!")

def lihat_wishlist(user_id):
    print("💝 Fitur wishlist akan segera hadir!")

def tambah_ke_wishlist(user_id):
    print("💝 Fitur tambah ke wishlist akan segera hadir!")

def lihat_ulasan_saya(user_id):
    print("⭐ Fitur ulasan akan segera hadir!")

def lihat_promo():
    print("🏷️ Fitur promo & diskon akan segera hadir!")

# Tambah Review
def tambah_review(user_id, product_id):
    try:
        # Get product and user info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check if product exists
        cursor.execute("SELECT name FROM product WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            print("❌ Produk tidak ditemukan!")
            return
            
        # Check if user exists
        cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return
            
        # Check if user has bought the product
        cursor.execute("""
            SELECT * FROM orders 
            WHERE user_id = %s AND product_id = %s
        """, (user_id, product_id))
        if not cursor.fetchone():
            print("❌ Anda harus membeli produk ini terlebih dahulu untuk memberikan review!")
            return
            
        # Get review details
        rating = 0
        while rating < 1 or rating > 5:
            try:
                rating = int(input("Berikan rating (1-5): "))
                if rating < 1 or rating > 5:
                    print("❌ Rating harus antara 1-5!")
            except ValueError:
                print("❌ Rating harus berupa angka!")
                
        comment = input("Tulis review Anda: ")
        
        # Connect to MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        # Create review document
        review = {
            "user_id": user_id,
            "user_name": user["name"],
            "product_id": product_id,
            "product_name": product["name"],
            "rating": rating,
            "comment": comment,
            "created_at": datetime.now(),
            "likes": 0,
            "replies": []
        }
        
        # Insert review into the Review collection
        db.Review.insert_one(review)  # Changed to match existing collection name
        print("✅ Review berhasil ditambahkan!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Lihat Review Produk
def lihat_review_produk(product_id):
    try:
        # Get product info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT name FROM product WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            print("❌ Produk tidak ditemukan!")
            return
            
        # Get reviews from MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        reviews = db.Review.find({"product_id": product_id}).sort("created_at", -1)  # Changed collection name
        
        print(f"\n⭐ Review untuk {product['name']}:")
        review_count = 0
        total_rating = 0
        
        for review in reviews:
            review_count += 1
            total_rating += review["rating"]
            
            print(f"\nReview oleh {review['user_name']}")
            print(f"Rating: {'⭐' * review['rating']}")
            print(f"Komentar: {review['comment']}")
            print(f"Tanggal: {review['created_at'].strftime('%d-%m-%Y %H:%M')}")
            print(f"Likes: {review['likes']}")
            
            if review["replies"]:
                print("\nBalasan:")
                for reply in review["replies"]:
                    print(f"- {reply['user_name']}: {reply['comment']}")
            print("-" * 40)
            
        if review_count > 0:
            avg_rating = total_rating / review_count
            print(f"\nRating rata-rata: {avg_rating:.1f} ⭐ ({review_count} review)")
        else:
            print("\nBelum ada review untuk produk ini.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Lihat Review Saya
def lihat_review_saya(user_id):
    try:
        # Get user info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return
            
        # Get reviews from MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        reviews = db.Review.find({"user_id": user_id}).sort("created_at", -1)  # Changed collection name
        
        print("\n📝 Review Saya:")
        has_reviews = False
        
        for review in reviews:
            has_reviews = True
            print(f"\nProduk: {review['product_name']}")
            print(f"Rating: {'⭐' * review['rating']}")
            print(f"Komentar: {review['comment']}")
            print(f"Tanggal: {review['created_at'].strftime('%d-%m-%Y %H:%M')}")
            print(f"Likes: {review['likes']}")
            
            if review["replies"]:
                print("\nBalasan:")
                for reply in review["replies"]:
                    print(f"- {reply['user_name']}: {reply['comment']}")
            print("-" * 40)
            
        if not has_reviews:
            print("Anda belum memberikan review apapun.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Edit Review
def edit_review(user_id):
    try:
        # Get user's reviews from MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        reviews = list(db.Review.find({"user_id": user_id}).sort("created_at", -1))  # Changed collection name
        
        if not reviews:
            print("❌ Anda belum memiliki review yang bisa diedit!")
            return
            
        print("\nReview yang dapat diedit:")
        for i, review in enumerate(reviews, 1):
            print(f"{i}. Produk: {review['product_name']}")
            print(f"   Rating saat ini: {'⭐' * review['rating']}")
            print(f"   Komentar saat ini: {review['comment']}")
            print()
            
        try:
            choice = int(input("Pilih nomor review yang ingin diedit (0 untuk batal): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(reviews):
                print("❌ Pilihan tidak valid!")
                return
        except ValueError:
            print("❌ Pilihan harus berupa angka!")
            return
            
        selected_review = reviews[choice - 1]
        
        # Get new rating and comment
        rating = 0
        while rating < 1 or rating > 5:
            try:
                rating = int(input("Rating baru (1-5): "))
                if rating < 1 or rating > 5:
                    print("❌ Rating harus antara 1-5!")
            except ValueError:
                print("❌ Rating harus berupa angka!")
                
        comment = input("Komentar baru: ")
        
        # Update review
        db.Review.update_one(  # Changed collection name
            {"_id": selected_review["_id"]},
            {
                "$set": {
                    "rating": rating,
                    "comment": comment,
                    "updated_at": datetime.now()
                }
            }
        )
        
        print("✅ Review berhasil diupdate!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Hapus Review
def hapus_review(user_id):
    try:
        # Get user's reviews from MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        reviews = list(db.Review.find({"user_id": user_id}).sort("created_at", -1))  # Changed collection name
        
        if not reviews:
            print("❌ Anda belum memiliki review yang bisa dihapus!")
            return
            
        print("\nReview yang dapat dihapus:")
        for i, review in enumerate(reviews, 1):
            print(f"{i}. Produk: {review['product_name']}")
            print(f"   Rating: {'⭐' * review['rating']}")
            print(f"   Komentar: {review['comment']}")
            print()
            
        try:
            choice = int(input("Pilih nomor review yang ingin dihapus (0 untuk batal): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(reviews):
                print("❌ Pilihan tidak valid!")
                return
        except ValueError:
            print("❌ Pilihan harus berupa angka!")
            return
            
        selected_review = reviews[choice - 1]
        
        # Confirm deletion
        confirm = input("Anda yakin ingin menghapus review ini? (y/n): ")
        if confirm.lower() != 'y':
            print("Penghapusan dibatalkan.")
            return
            
        # Delete review
        db.Review.delete_one({"_id": selected_review["_id"]})  # Changed collection name
        print("✅ Review berhasil dihapus!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Menu Review
def menu_review(user_id):
    while True:
        print("\n===== Menu Review =====")
        print("1. Lihat Review Saya")
        print("2. Tambah Review")
        print("3. Edit Review")
        print("4. Hapus Review")
        print("5. Kembali ke Menu Profil")

        pilihan = input("Pilih menu (1-5): ")

        if pilihan == '1':
            lihat_review_saya(user_id)
        elif pilihan == '2':
            # Show products first
            tampilkan_produk()
            product_id = int(input("\nMasukkan ID produk yang ingin direview: "))
            tambah_review(user_id, product_id)
        elif pilihan == '3':
            edit_review(user_id)
        elif pilihan == '4':
            hapus_review(user_id)
        elif pilihan == '5':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Jalankan program
if __name__ == "__main__":
    main_menu()
