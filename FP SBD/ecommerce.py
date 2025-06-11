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
    # Select role first
    while True:
        role = input("Pilih role (1: Customer, 2: Seller): ")
        if role in ['1', '2']:
            role = 'customer' if role == '1' else 'seller'
            break
        print("❌ Pilihan tidak valid! Pilih 1 atau 2.")

    # Common information for both roles
    name = input("Masukkan Nama: ")
    
    # Username validation
    while True:
        username = input("Masukkan Username: ")
        if not username.strip():
            print("❌ Username tidak boleh kosong!")
            continue
            
        try:
            connection = create_connection()
            cursor = connection.cursor()
            
            # Check if username already exists
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                print("❌ Username sudah digunakan. Pilih username lain.")
                continue
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            if 'connection' in locals():
                cursor.close()
                connection.close()
            continue
    
    # Email validation
    while True:
        email = input("Masukkan Email: ")
        if not email.strip():
            print("❌ Email tidak boleh kosong!")
            continue
            
        if "@" not in email:
            print("❌ Email tidak sesuai format!")
            continue
            
        try:
            connection = create_connection()
            cursor = connection.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                print("❌ Email sudah terdaftar. Gunakan email lain.")
                continue
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            if 'connection' in locals():
                cursor.close()
                connection.close()
            continue
    
    password = input("Masukkan Password: ")
    
    # Phone number validation
    while True:
        phone_number = input("Masukkan Nomor Telepon: ")
        if not phone_number.strip():
            print("❌ Nomor telepon tidak boleh kosong!")
            continue
            
        if not phone_number.isdigit():
            print("❌ Nomor telepon hanya boleh berisi angka!")
            continue
            
        break

    try:
        connection = create_connection()
        cursor = connection.cursor()

        if role == 'customer':
            # Get customer address
            address = input("Masukkan Alamat: ")
            
            # Insert into customer table first
            cursor.execute("""
                INSERT INTO customer (name, email, address) 
                VALUES (%s, %s, %s)
            """, (name, email, address))
            connection.commit()
            
            # Get the customer_id
            customer_id = cursor.lastrowid
            
            # Insert into users table with customer_id
            cursor.execute("""
                INSERT INTO users (role, name, username, phone_number, email, password, customer_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (role, name, username, phone_number, email, password, customer_id))
            
        else:  # seller
            # Get store information
            store_name = input("Masukkan Nama Toko: ")
            store_address = input("Masukkan Alamat Toko: ")
            
            # Insert into seller table first
            cursor.execute("""
                INSERT INTO seller (store_name, store_address) 
                VALUES (%s, %s)
            """, (store_name, store_address))
            connection.commit()

            # Get the seller_id
            seller_id = cursor.lastrowid
            
            # Insert into users table with seller_id
            cursor.execute("""
                INSERT INTO users (role, name, username, phone_number, email, password, seller_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (role, name, username, phone_number, email, password, seller_id))
        
        connection.commit()
        print("✅ Registrasi berhasil! Silakan login.")

    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# LOGIN - Autentikasi User
def login_user():
    print("\nPilih metode login:")
    print("1. Login dengan Email")
    print("2. Login dengan Username")
    
    while True:
        login_method = input("Pilih metode (1/2): ")
        if login_method in ['1', '2']:
            break
        print("❌ Pilihan tidak valid!")
    
    if login_method == '1':
        identifier = input("Masukkan Email: ")
        identifier_field = "email"
    else:
        identifier = input("Masukkan Username: ")
        identifier_field = "username"
        
    password = input("Masukkan Password: ")

    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        # Get user from users table
        query = f"""
            SELECT u.user_id, u.name, u.email, u.username, u.phone_number, u.role,
                   COALESCE(c.address, s.store_address) as address,
                   c.customer_id, s.seller_id
            FROM users u
            LEFT JOIN customer c ON u.customer_id = c.customer_id
            LEFT JOIN seller s ON u.seller_id = s.seller_id
            WHERE u.{identifier_field} = %s AND u.password = %s
        """
        cursor.execute(query, (identifier, password))
        user = cursor.fetchone()

        if user:
            print(f"\n✅ Login berhasil! Selamat datang, {user['name']}")
            print(f"Email: {user['email']}")
            print(f"Username: {user['username']}")
            print(f"No. Telepon: {user['phone_number']}")
            print(f"Alamat: {user['address']}")
            
            # Return customer_id or seller_id based on role
            user_id = user['customer_id'] if user['role'] == 'customer' else user['seller_id']
            return user_id, user['name'], user['role']
        else:
            if login_method == '1':
                print("❌ Email atau password salah!")
            else:
                print("❌ Username atau password salah!")

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
        
        # Get all categories
        cursor.execute("SELECT * FROM categories ORDER BY categories_name")
        categories = cursor.fetchall()
        
        print("\n📑 Daftar Kategori:")
        for category in categories:
            print(f"ID: {category['category_id']}, Nama: {category['categories_name']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# CREATE - Tambah Produk
def tambah_produk(seller_id):
    try:
        # Check if there are any categories available first
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as category_count FROM categories")
        result = cursor.fetchone()
        
        if result['category_count'] == 0:
            print("\n❌ Tidak dapat menambahkan produk karena belum ada kategori!")
            print("ℹ️ Silakan tambahkan kategori terlebih dahulu melalui Menu Kategori.")
            return
            
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
            INSERT INTO products (name, description, price, stock, category_id, seller_id, date_posted) 
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        values = (nama, deskripsi, harga, stok, kategori_id, seller_id)
        
        cursor.execute(query, values)
        connection.commit()
        
        print("✅ Produk berhasil ditambahkan!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
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
            SELECT p.*, c.categories_name as category_name, s.store_name as seller_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            JOIN seller s ON p.seller_id = s.seller_id
            ORDER BY p.date_posted DESC
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
            reviews = db.Review.find({"product_id": product['product_id']})
            total_rating = 0
            review_count = 0
            
            for review in reviews:
                total_rating += review['rating']
                review_count += 1
                
            avg_rating = total_rating / review_count if review_count > 0 else 0
            
            print(f"\nID: {product['product_id']}")
            print(f"Nama: {product['name']}")
            print(f"Deskripsi: {product['description']}")
            print(f"Kategori: {product['category_name']}")
            print(f"Toko: {product['seller_name']}")
            print(f"Harga: Rp {product['price']:,.2f}")
            print(f"Stok: {product['stock']}")
            print(f"Tanggal Posting: {product['date_posted']}")
            print(f"Rating: {avg_rating:.1f} ⭐ ({review_count} review)")
            print("-" * 50)  # Made the separator line longer for better readability

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# UPDATE - Edit Produk
def edit_produk(seller_id):
    try:
        product_id = int(input("Masukkan ID produk yang ingin diupdate: "))
        
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check if product exists and belongs to seller
        cursor.execute("""
            SELECT * FROM products 
            WHERE product_id = %s AND seller_id = %s
        """, (product_id, seller_id))
        
        product = cursor.fetchone()
        if not product:
            print("❌ Produk tidak ditemukan atau Anda tidak memiliki akses!")
            return
            
        # Show current product details
        print("\n📦 Detail Produk Saat Ini:")
        print(f"1. Nama: {product['name']}")
        print(f"2. Deskripsi: {product['description']}")
        print(f"3. Harga: Rp {product['price']:,.2f}")
        print(f"4. Stok: {product['stock']}")
        print(f"5. Kategori ID: {product['category_id']}")
        print("6. Kembali")
        
        # Initialize update data
        update_fields = []
        update_values = []
        
        while True:
            try:
                pilihan = input("\nPilih nomor field yang ingin diubah (6 untuk selesai): ")
                
                if pilihan == "6":
                    if not update_fields:
                        print("❌ Tidak ada perubahan yang dilakukan.")
                        return
                    break
                    
                if pilihan not in ["1", "2", "3", "4", "5"]:
                    print("❌ Pilihan tidak valid!")
                    continue
                    
                if pilihan == "1":
                    nama_baru = input("Masukkan nama baru: ")
                    if nama_baru.strip():
                        update_fields.append("name = %s")
                        update_values.append(nama_baru)
                        
                elif pilihan == "2":
                    deskripsi_baru = input("Masukkan deskripsi baru: ")
                    if deskripsi_baru.strip():
                        update_fields.append("description = %s")
                        update_values.append(deskripsi_baru)
                        
                elif pilihan == "3":
                    try:
                        harga_baru = float(input("Masukkan harga baru: "))
                        if harga_baru <= 0:
                            print("❌ Harga harus lebih dari 0!")
                            continue
                        update_fields.append("price = %s")
                        update_values.append(harga_baru)
                    except ValueError:
                        print("❌ Harga harus berupa angka!")
                        continue
                        
                elif pilihan == "4":
                    try:
                        stok_baru = int(input("Masukkan stok baru: "))
                        if stok_baru < 0:
                            print("❌ Stok tidak boleh negatif!")
                            continue
                        update_fields.append("stock = %s")
                        update_values.append(stok_baru)
                    except ValueError:
                        print("❌ Stok harus berupa angka!")
                        continue
                        
                elif pilihan == "5":
                    # Show available categories first
                    print("\nKategori yang tersedia:")
                    tampilkan_kategori()
                    
                    try:
                        kategori_baru = int(input("\nMasukkan kategori ID baru: "))
                        # Verify if category exists
                        cursor.execute("SELECT * FROM categories WHERE category_id = %s", (kategori_baru,))
                        if not cursor.fetchone():
                            print("❌ Kategori tidak ditemukan!")
                            continue
                        update_fields.append("category_id = %s")
                        update_values.append(kategori_baru)
                    except ValueError:
                        print("❌ Kategori ID harus berupa angka!")
                        continue
                
                print("✅ Field berhasil ditambahkan untuk diupdate!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        # Add date_posted to update fields
        update_fields.append("date_posted = NOW()")
        
        # Construct and execute update query
        query = f"""
            UPDATE products
            SET {', '.join(update_fields)}
            WHERE product_id = %s AND seller_id = %s
        """
        
        # Add product_id and seller_id to values
        update_values.extend([product_id, seller_id])
        
        cursor.execute(query, tuple(update_values))
        connection.commit()
        print("✅ Produk berhasil diupdate!")

    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# DELETE - Hapus Produk
def hapus_produk(seller_id):
    try:
        product_id = int(input("Masukkan ID produk yang ingin dihapus: "))
        
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        # Check if product exists and belongs to seller
        cursor.execute("""
            SELECT * FROM products 
            WHERE product_id = %s AND seller_id = %s
        """, (product_id, seller_id))
        
        product = cursor.fetchone()
        if not product:
            print("❌ Produk tidak ditemukan atau Anda tidak memiliki akses!")
            return

        # Delete the product
        cursor.execute("""
            DELETE FROM products 
            WHERE product_id = %s AND seller_id = %s
        """, (product_id, seller_id))
        
        connection.commit()
        print("✅ Produk berhasil dihapus!")

    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        if 'connection' in locals():
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
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
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
            INSERT INTO orders (user_id, total_price, order_date)
            VALUES (%s, %s, NOW())
        """, (user_id, total_harga))
        
        order_id = cursor.lastrowid
        
        # Create order detail
        cursor.execute("""
            INSERT INTO order_details (order_id, product_id, quantity, price_per_unit)
            VALUES (%s, %s, %s, %s)
        """, (order_id, product_id, jumlah, product['price']))
        
        # Create payment record with success status
        cursor.execute("""
            INSERT INTO payment (payment_status, payment_date, payment_method, order_id)
            VALUES ('success', NOW(), 'Transfer Bank', %s)
        """, (order_id,))
        
        # Update stock
        cursor.execute("""
            UPDATE products
            SET stock = stock - %s
            WHERE product_id = %s
        """, (jumlah, product_id))
        
        connection.commit()
        print(f"✅ Pembelian berhasil! Total harga: Rp {total_harga:,.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Lihat Riwayat Pembelian
def lihat_riwayat_pembelian(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get orders with payment info
        query = """
            SELECT o.order_id, o.total_price, o.order_date, o.promo,
                   p.payment_method, p.payment_status, p.payment_date
            FROM orders o
            LEFT JOIN payment p ON o.order_id = p.order_id
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
            print(f"\nOrder ID: {order['order_id']}")
            print(f"Total: Rp {order['total_price']:,.2f}")
            if order['promo']:
                print(f"Promo: {order['promo']}")
            print(f"Tanggal Order: {order['order_date']}")
            print(f"Metode Pembayaran: {order['payment_method'] if order['payment_method'] else 'Belum dipilih'}")
            print(f"Status Pembayaran: {order['payment_status'] if order['payment_status'] else 'Menunggu pembayaran'}")
            if order['payment_date']:
                print(f"Tanggal Pembayaran: {order['payment_date']}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Tambah ke Trolley
def tambah_ke_trolley(customer_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        tampilkan_produk()
        product_id = int(input("\nMasukkan ID produk yang ingin ditambah ke trolley: "))
        jumlah = int(input("Masukkan jumlah yang ingin ditambah: "))
        
        # Check product availability
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
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
        """, (customer_id, product_id))
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Update quantity if product already in trolley
            cursor.execute("""
                UPDATE trolley 
                SET quantity = quantity + %s
                WHERE user_id = %s AND product_id = %s
            """, (jumlah, customer_id, product_id))
        else:
            # Add new item to trolley
            cursor.execute("""
                INSERT INTO trolley (user_id, product_id, quantity, added_at)
                VALUES (%s, %s, %s, NOW())
            """, (customer_id, product_id, jumlah))
        
        connection.commit()
        print("✅ Produk berhasil ditambahkan ke trolley!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Lihat Isi Trolley
def lihat_trolley(customer_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT t.trolley_id, p.name, p.price, t.quantity, (p.price * t.quantity) as subtotal, t.added_at
            FROM trolley t
            JOIN products p ON t.product_id = p.product_id
            WHERE t.user_id = %s
            ORDER BY t.added_at DESC
        """
        cursor.execute(query, (customer_id,))
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
def ubah_jumlah_trolley(customer_id):
    if not lihat_trolley(customer_id):
        return
        
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        trolley_id = int(input("\nMasukkan ID Trolley yang ingin diubah: "))
        jumlah_baru = int(input("Masukkan jumlah baru: "))
        
        if jumlah_baru <= 0:
            print("❌ Jumlah harus lebih dari 0!")
            return
            
        # Check if trolley item exists and belongs to user
        cursor.execute("""
            SELECT t.*, p.stock 
            FROM trolley t
            JOIN products p ON t.product_id = p.product_id
            WHERE t.trolley_id = %s AND t.user_id = %s
        """, (trolley_id, customer_id))
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
        """, (jumlah_baru, trolley_id, customer_id))
        
        connection.commit()
        print("✅ Jumlah berhasil diubah!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Hapus dari Trolley
def hapus_dari_trolley(customer_id):
    if not lihat_trolley(customer_id):
        return
        
    try:
        connection = create_connection()
        cursor = connection.cursor()
        
        trolley_id = int(input("\nMasukkan ID Trolley yang ingin dihapus: "))
        
        cursor.execute("""
            DELETE FROM trolley 
            WHERE trolley_id = %s AND user_id = %s
        """, (trolley_id, customer_id))
        
        if cursor.rowcount > 0:
            connection.commit()
            print("✅ Item berhasil dihapus dari trolley!")
        else:
            print("❌ Item trolley tidak ditemukan!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Checkout Trolley
def checkout_trolley(user_id):
    connection = None
    cursor = None
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get all items in trolley
        cursor.execute("""
            SELECT t.*, p.price, p.stock, p.name
            FROM trolley t
            JOIN products p ON t.product_id = p.product_id
            WHERE t.user_id = %s
        """, (user_id,))
        items = cursor.fetchall()
        
        if not items:
            print("❌ Trolley kosong!")
            return
            
        # Verify stock for all items
        for item in items:
            if item['quantity'] > item['stock']:
                print(f"❌ Stok tidak mencukupi untuk produk {item['name']}!")
                return
        
        # Calculate total price
        total_price = sum(item['price'] * item['quantity'] for item in items)
        
        # Show order summary
        print("\n📋 Ringkasan Pesanan:")
        for item in items:
            print(f"- {item['name']} ({item['quantity']} x Rp {item['price']:,.2f})")
        print(f"\nTotal Harga: Rp {total_price:,.2f}")
        
        # Select payment method
        print("\nPilih metode pembayaran:")
        print("1. Transfer Bank")
        print("2. E-Wallet")
        print("3. COD (Cash On Delivery)")
        
        while True:
            try:
                payment_choice = int(input("\nMasukkan pilihan (1-3): "))
                if payment_choice < 1 or payment_choice > 3:
                    print("❌ Pilihan tidak valid!")
                    continue
                break
            except ValueError:
                print("❌ Pilihan harus berupa angka!")
        
        # Map payment choice to method
        payment_methods = {
            1: "Transfer Bank",
            2: "E-Wallet",
            3: "COD"
        }
        payment_method = payment_methods[payment_choice]
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (user_id, total_price, order_date)
            VALUES (%s, %s, NOW())
        """, (user_id, total_price))
        
        order_id = cursor.lastrowid
        
        # Create payment record with success status
        cursor.execute("""
            INSERT INTO payment (order_id, payment_method, payment_status, payment_date)
            VALUES (%s, %s, 'success', NOW())
        """, (order_id, payment_method))
        
        # Update stock for each item
        for item in items:
            cursor.execute("""
                UPDATE products
                SET stock = stock - %s
                WHERE product_id = %s
            """, (item['quantity'], item['product_id']))
            
        # Clear the user's trolley
        cursor.execute("DELETE FROM trolley WHERE user_id = %s", (user_id,))
        
        connection.commit()
        print(f"\n✅ Checkout berhasil! Pembayaran dengan {payment_method} telah dikonfirmasi.")
        print(f"Total pembayaran: Rp {total_price:,.2f}")
        print("Terima kasih telah berbelanja!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Lihat Profil User
def lihat_profil(user_id, role):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        if role == 'customer':
            query = """
                SELECT u.name, u.email, u.phone_number, c.address,
                       u.role
                FROM users u
                JOIN customer c ON u.customer_id = c.customer_id
                WHERE c.customer_id = %s
            """
        else:  # seller
            query = """
                SELECT u.name, u.email, u.phone_number,
                       s.store_name, s.store_address,
                       u.role
                FROM users u
                JOIN seller s ON u.seller_id = s.seller_id
                WHERE s.seller_id = %s
            """
            
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        if user:
            print("\n👤 Profil Anda:")
            print(f"Nama: {user['name']}")
            print(f"Email: {user['email']}")
            print(f"No. Telepon: {user['phone_number']}")
            print(f"Role: {user['role']}")
            
            if role == 'customer':
                print(f"Alamat: {user['address']}")
            else:  # seller
                print("\n🏪 Informasi Toko:")
                print(f"Nama Toko: {user['store_name']}")
                print(f"Alamat Toko: {user['store_address']}")
        else:
            print("❌ User tidak ditemukan!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

# Edit Profil User
def edit_profil(user_id, role):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        # Get current user data
        if role == 'customer':
            query = """
                SELECT u.*, c.address
                FROM users u
                JOIN customer c ON u.customer_id = c.customer_id
                WHERE c.customer_id = %s
            """
        else:  # seller
            query = """
                SELECT u.*, s.store_name, s.store_address
                FROM users u
                JOIN seller s ON u.seller_id = s.seller_id
                WHERE s.seller_id = %s
            """
            
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        if not user:
            print("❌ User tidak ditemukan!")
            return

        print("\nEdit Profil (kosongkan jika tidak ingin mengubah):")
        name = input(f"Nama [{user['name']}]: ") or user['name']
        phone_number = input(f"No. Telepon [{user['phone_number']}]: ") or user['phone_number']
        
        # Update users table
        cursor.execute("""
            UPDATE users 
            SET name = %s, phone_number = %s
            WHERE user_id = %s
        """, (name, phone_number, user['user_id']))
        
        if role == 'customer':
            address = input(f"Alamat [{user['address']}]: ") or user['address']
            
            # Update customer table
            cursor.execute("""
                UPDATE customer 
                SET address = %s
                WHERE customer_id = %s
            """, (address, user_id))
        else:  # seller
            print("\nInformasi Toko:")
            store_name = input(f"Nama Toko [{user['store_name']}]: ") or user['store_name']
            store_address = input(f"Alamat Toko [{user['store_address']}]: ") or user['store_address']
            
            # Update seller table
            cursor.execute("""
                UPDATE seller 
                SET store_name = %s, store_address = %s
                WHERE seller_id = %s
            """, (store_name, store_address, user_id))
            
        connection.commit()
        print("✅ Profil berhasil diupdate!")

    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Tambah Kategori
def tambah_kategori():
    try:
        print("\nKategori yang ada:")
        tampilkan_kategori()
        
        nama_kategori = input("\nMasukkan nama kategori baru: ")
        
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check if category name already exists
        cursor.execute("SELECT * FROM categories WHERE categories_name = %s", (nama_kategori,))
        if cursor.fetchone():
            print("❌ Kategori dengan nama tersebut sudah ada!")
            return
            
        # Find the lowest available ID by checking for gaps
        cursor.execute("""
            SELECT t1.category_id + 1 AS missing_id
            FROM categories t1
            LEFT JOIN categories t2 ON t1.category_id + 1 = t2.category_id
            WHERE t2.category_id IS NULL
            AND t1.category_id + 1 <= (SELECT MAX(category_id) FROM categories)
            ORDER BY t1.category_id LIMIT 1
        """)
        gap = cursor.fetchone()
        
        if gap:
            # Use the found gap
            next_id = gap['missing_id']
            # Set auto_increment to the gap value
            cursor.execute("ALTER TABLE categories AUTO_INCREMENT = %s", (next_id,))
        else:
            # If no gaps, get the next auto_increment value
            cursor.execute("SELECT MAX(category_id) + 1 as next_id FROM categories")
            result = cursor.fetchone()
            next_id = result['next_id'] if result['next_id'] else 1
            cursor.execute("ALTER TABLE categories AUTO_INCREMENT = %s", (next_id,))
            
        # Insert new category
        cursor.execute("""
            INSERT INTO categories (categories_name)
            VALUES (%s)
        """, (nama_kategori,))
        
        connection.commit()
        print(f"✅ Kategori berhasil ditambahkan dengan ID: {next_id}!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Menu Produk Seller
def menu_produk_seller(seller_id):
    while True:
        print("\n===== Menu Produk =====")
        print("1. Tambah Produk")
        print("2. Tampilkan Produk")
        print("3. Edit Produk")
        print("4. Hapus Produk")
        print("5. Kembali")

        pilihan = input("Pilih menu (1-5): ")

        if pilihan == '1':
            tambah_produk(seller_id)
        elif pilihan == '2':
            tampilkan_produk()
        elif pilihan == '3':
            edit_produk(seller_id)
        elif pilihan == '4':
            hapus_produk(seller_id)
        elif pilihan == '5':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Hapus Kategori
def hapus_kategori():
    try:
        print("\nKategori yang ada:")
        tampilkan_kategori()
        
        kategori_id = int(input("\nMasukkan ID kategori yang ingin dihapus: "))
        
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check if category exists
        cursor.execute("SELECT * FROM categories WHERE category_id = %s", (kategori_id,))
        category = cursor.fetchone()
        if not category:
            print("❌ Kategori tidak ditemukan!")
            return
            
        # Check if category is being used by any products
        cursor.execute("SELECT COUNT(*) as count FROM products WHERE category_id = %s", (kategori_id,))
        product_count = cursor.fetchone()['count']
        
        if product_count > 0:
            print(f"❌ Kategori tidak dapat dihapus karena sedang digunakan oleh {product_count} produk!")
            return
            
        # Confirm deletion
        confirm = input(f"Anda yakin ingin menghapus kategori '{category['categories_name']}'? (y/n): ")
        if confirm.lower() != 'y':
            print("Penghapusan dibatalkan.")
            return
            
        # Delete category
        cursor.execute("DELETE FROM categories WHERE category_id = %s", (kategori_id,))
        connection.commit()
        
        print("✅ Kategori berhasil dihapus!")
        
    except ValueError:
        print("❌ ID Kategori harus berupa angka!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Menu Kategori
def menu_kategori():
    while True:
        print("\n===== Menu Kategori =====")
        print("1. Lihat Kategori")
        print("2. Tambah Kategori")
        print("3. Hapus Kategori")
        print("4. Kembali")

        pilihan = input("Pilih menu (1-4): ")

        if pilihan == '1':
            tampilkan_kategori()
        elif pilihan == '2':
            tambah_kategori()
        elif pilihan == '3':
            hapus_kategori()
        elif pilihan == '4':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Menu Profil Seller
def menu_profil_seller(seller_id):
    while True:
        print("\n===== Menu Profil =====")
        print("1. Lihat Profil")
        print("2. Edit Profil")
        print("3. Lihat & Balas Review")
        print("4. Kembali")

        pilihan = input("Pilih menu (1-4): ")

        if pilihan == '1':
            lihat_profil(seller_id, 'seller')
        elif pilihan == '2':
            edit_profil(seller_id, 'seller')
        elif pilihan == '3':
            menu_review_seller(seller_id)
        elif pilihan == '4':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Update Status Pembayaran
def update_payment_status(seller_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get orders with pending payments for products sold by this seller
        query = """
            SELECT DISTINCT o.order_id, o.total_price, o.order_date, 
                   p.payment_id, p.payment_method, p.payment_status,
                   u.name as customer_name
            FROM orders o
            JOIN payment p ON o.order_id = p.order_id
            JOIN users u ON o.user_id = u.user_id
            JOIN products pr ON pr.seller_id = %s
            WHERE p.payment_status = 'pending'
            ORDER BY o.order_date DESC
        """
        cursor.execute(query, (seller_id,))
        orders = cursor.fetchall()
        
        if not orders:
            print("❌ Tidak ada pembayaran yang perlu diupdate!")
            return
            
        print("\n📋 Daftar Pesanan dengan Pembayaran Pending:")
        for order in orders:
            print(f"\nPayment ID: {order['payment_id']}")
            print(f"Order ID: {order['order_id']}")
            print(f"Customer: {order['customer_name']}")
            print(f"Total: Rp {order['total_price']:,.2f}")
            print(f"Tanggal Order: {order['order_date']}")
            print(f"Metode Pembayaran: {order['payment_method']}")
            print(f"Status: {order['payment_status']}")
            print("-" * 40)
            
        payment_id = int(input("\nMasukkan Payment ID yang ingin diupdate: "))
        
        # Verify payment exists and belongs to an order with this seller's products
        cursor.execute("""
            SELECT p.* 
            FROM payment p
            JOIN orders o ON p.order_id = o.order_id
            JOIN products pr ON pr.seller_id = %s
            WHERE p.payment_id = %s
        """, (seller_id, payment_id))
        
        payment = cursor.fetchone()
        if not payment:
            print("❌ Payment ID tidak valid atau bukan untuk produk Anda!")
            return
            
        print("\nPilih status baru:")
        print("1. Paid (Sudah Dibayar)")
        print("2. Failed (Gagal)")
        print("3. Cancelled (Dibatalkan)")
        
        status_choice = input("Pilih status (1-3): ")
        
        status_map = {
            '1': 'paid',
            '2': 'failed',
            '3': 'cancelled'
        }
        
        if status_choice not in status_map:
            print("❌ Pilihan tidak valid!")
            return
            
        new_status = status_map[status_choice]
        
        # Update payment status
        cursor.execute("""
            UPDATE payment 
            SET payment_status = %s 
            WHERE payment_id = %s
        """, (new_status, payment_id))
        
        connection.commit()
        print("✅ Status pembayaran berhasil diupdate!")
        
    except ValueError:
        print("❌ Payment ID harus berupa angka!")
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Menu Payment
def menu_payment(seller_id):
    while True:
        print("\n===== Menu Payment =====")
        print("1. Update Status Pembayaran")
        print("2. Kembali")

        pilihan = input("Pilih menu (1-2): ")

        if pilihan == '1':
            update_payment_status(seller_id)
        elif pilihan == '2':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Menu Review Seller
def menu_review_seller(seller_id):
    while True:
        print("\n===== Menu Review =====")
        print("1. Lihat Semua Review Produk")
        print("2. Balas Review")
        print("3. Kembali")

        pilihan = input("Pilih menu (1-3): ")

        if pilihan == '1':
            lihat_review_produk_seller(seller_id)
        elif pilihan == '2':
            balas_review(seller_id)
        elif pilihan == '3':
            break
        else:
            print("❌ Pilihan tidak valid!")

def lihat_review_produk_seller(seller_id):
    connection = None
    cursor = None
    try:
        # Get seller info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get seller's products
        cursor.execute("""
            SELECT product_id, name 
            FROM products 
            WHERE seller_id = %s
        """, (seller_id,))
        products = cursor.fetchall()
        
        if not products:
            print("❌ Anda belum memiliki produk!")
            return
            
        # Get MongoDB connection
        db = create_mongo_connection()
        if not db:
            return
            
        # Get all reviews for seller's products
        product_ids = [p['product_id'] for p in products]
        reviews = list(db.Review.find({"product_id": {"$in": product_ids}}).sort("created_at", -1))
        
        if not reviews:
            print("❌ Belum ada review untuk produk Anda!")
            return
            
        # Show all reviews
        print("\n📝 Daftar Review Produk Anda:")
        for i, review in enumerate(reviews, 1):
            print(f"\n{i}. Produk: {review['product_name']}")
            print(f"   Dari: {review['user_name']}")
            print(f"   Rating: {'⭐' * review['rating']}")
            print(f"   Komentar: {review['comment']}")
            print(f"   Tanggal: {review['created_at'].strftime('%d-%m-%Y %H:%M')}")
            
            if review.get('replies'):
                print("   Balasan:")
                for reply in review['replies']:
                    print(f"   - {reply['user_name']}: {reply['comment']}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Menu Seller
def menu_seller(user_id):
    while True:
        print("\n===== MENU UTAMA SELLER =====")
        print("1. Menu Produk")
        print("2. Menu Kategori")
        print("3. Menu Profil")
        print("4. Menu Review")
        print("5. Menu Promo")
        print("6. Logout")

        pilihan = input("Pilih menu (1-6): ")

        if pilihan == '1':
            menu_produk_seller(user_id)
        elif pilihan == '2':
            menu_kategori()
        elif pilihan == '3':
            menu_profil_seller(user_id)
        elif pilihan == '4':
            menu_review_seller(user_id)
        elif pilihan == '5':
            menu_promo_seller(user_id)
        elif pilihan == '6':
            print("🔒 Logout berhasil.\n")
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
                if role == 'seller':
                    menu_seller(user_id)
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
def tambah_review(user_id):
    connection = None
    cursor = None
    try:
        # Get product and user info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get user details including customer_id
        cursor.execute("""
            SELECT u.*, c.customer_id 
            FROM users u
            LEFT JOIN customer c ON u.customer_id = c.customer_id
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return
            
        # Show products and get product ID
        tampilkan_produk()
        
        try:
            product_id = int(input("\nMasukkan ID produk yang ingin direview: "))
        except ValueError:
            print("❌ ID produk harus berupa angka!")
            return
            
        # Check if product exists
        cursor.execute("""
            SELECT p.*, s.store_name 
            FROM products p
            JOIN seller s ON p.seller_id = s.seller_id 
            WHERE p.product_id = %s
        """, (product_id,))
        product = cursor.fetchone()
        if not product:
            print("❌ Produk tidak ditemukan!")
            return
            
        # Check if user has any orders
        cursor.execute("""
            SELECT o.* 
            FROM orders o
            WHERE o.user_id = %s
        """, (user_id,))
        orders = cursor.fetchall()  # Make sure to fetch all results
        if not orders:
            print("❌ Anda harus membeli produk terlebih dahulu untuk memberikan review!")
            return
            
        # Check if user has already reviewed this product
        db = create_mongo_connection()
        if not db:
            return
            
        existing_review = db.Review.find_one({
            "user_id": user_id,
            "product_id": product_id
        })
        
        if existing_review:
            print("❌ Anda sudah memberikan review untuk produk ini!")
            return
            
        # Get review details
        rating = 0
        while rating < 1 or rating > 5:
            try:
                rating = int(input("\nBerikan rating (1-5): "))
                if rating < 1 or rating > 5:
                    print("❌ Rating harus antara 1-5!")
            except ValueError:
                print("❌ Rating harus berupa angka!")
                
        comment = input("Tulis review Anda: ")
        
        # Create review document
        review = {
            "user_id": user_id,  # Store the actual user_id
            "user_name": user["name"],
            "product_id": product_id,
            "product_name": product["name"],
            "rating": rating,
            "comment": comment,
            "created_at": datetime.now(),
            "replies": [],
            "qna": []
        }
        
        # Insert review into the Review collection
        db.Review.insert_one(review)
        
        # Show confirmation and review summary
        print("\n✅ Review berhasil ditambahkan!")
        print("\nReview Anda:")
        print(f"Produk: {product['name']}")
        print(f"Rating: {'⭐' * rating}")
        print(f"Komentar: {comment}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Lihat Review Saya
def lihat_review_saya(user_id):
    connection = None
    cursor = None
    try:
        # Get user info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get user details including customer_id
        cursor.execute("""
            SELECT u.*, c.customer_id 
            FROM users u
            LEFT JOIN customer c ON u.customer_id = c.customer_id
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return
            
        # Get reviews from MongoDB using user_id
        db = create_mongo_connection()
        if not db:
            return
            
        reviews = db.Review.find({"user_id": user_id}).sort("created_at", -1)
        reviews = list(reviews)  # Convert cursor to list to check if empty
        
        if not reviews:
            print("\nAnda belum memberikan review apapun.")
            return
        
        print("\n📝 Review Saya:")
        for review in reviews:
            print(f"\nProduk: {review['product_name']}")
            print(f"Rating: {'⭐' * review['rating']}")
            print(f"Komentar: {review['comment']}")
            print(f"Tanggal: {review['created_at'].strftime('%d-%m-%Y %H:%M')}")
            
            if review.get("replies"):
                print("\nBalasan:")
                for reply in review["replies"]:
                    print(f"- {reply['user_name']}: {reply['comment']}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Edit Review
def edit_review(user_id):
    connection = None
    cursor = None
    try:
        # Get user info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.*, c.customer_id 
            FROM users u
            LEFT JOIN customer c ON u.customer_id = c.customer_id
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return
            
        # Get user's reviews from MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        reviews = list(db.Review.find({"user_id": user_id}).sort("created_at", -1))
        
        if not reviews:
            print("❌ Anda belum memiliki review yang bisa diedit!")
            return
            
        print("\nReview yang dapat diedit:")
        for i, review in enumerate(reviews, 1):
            print(f"\n{i}. Produk: {review['product_name']}")
            print(f"   Rating saat ini: {'⭐' * review['rating']}")
            print(f"   Komentar saat ini: {review['comment']}")
            print(f"   Tanggal: {review['created_at'].strftime('%d-%m-%Y %H:%M')}")
            
        try:
            choice = int(input("\nPilih nomor review yang ingin diedit (0 untuk batal): "))
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
                rating = int(input("\nRating baru (1-5): "))
                if rating < 1 or rating > 5:
                    print("❌ Rating harus antara 1-5!")
            except ValueError:
                print("❌ Rating harus berupa angka!")
                
        comment = input("Komentar baru: ")
        
        # Update review
        result = db.Review.update_one(
            {
                "_id": selected_review["_id"],
                "user_id": user_id  # Make sure we only update user's own review
            },
            {
                "$set": {
                    "rating": rating,
                    "comment": comment,
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            print("\n✅ Review berhasil diupdate!")
            print("\nReview setelah diupdate:")
            print(f"Produk: {selected_review['product_name']}")
            print(f"Rating: {'⭐' * rating}")
            print(f"Komentar: {comment}")
        else:
            print("❌ Gagal mengupdate review!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Hapus Review
def hapus_review(user_id):
    connection = None
    cursor = None
    try:
        # Get user info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.*, c.customer_id 
            FROM users u
            LEFT JOIN customer c ON u.customer_id = c.customer_id
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return
            
        # Get user's reviews from MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        reviews = list(db.Review.find({"user_id": user_id}).sort("created_at", -1))
        
        if not reviews:
            print("❌ Anda belum memiliki review yang bisa dihapus!")
            return
            
        print("\nReview yang dapat dihapus:")
        for i, review in enumerate(reviews, 1):
            print(f"\n{i}. Produk: {review['product_name']}")
            print(f"   Rating: {'⭐' * review['rating']}")
            print(f"   Komentar: {review['comment']}")
            print(f"   Tanggal: {review['created_at'].strftime('%d-%m-%Y %H:%M')}")
            
        try:
            choice = int(input("\nPilih nomor review yang ingin dihapus (0 untuk batal): "))
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
        confirm = input("\nAnda yakin ingin menghapus review ini? (y/n): ")
        if confirm.lower() != 'y':
            print("Penghapusan dibatalkan.")
            return
            
        # Delete review
        result = db.Review.delete_one({
            "_id": selected_review["_id"],
            "user_id": user_id  # Make sure we only delete user's own review
        })
        
        if result.deleted_count > 0:
            print("\n✅ Review berhasil dihapus!")
        else:
            print("❌ Gagal menghapus review!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

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
            tambah_review(user_id)
        elif pilihan == '3':
            edit_review(user_id)
        elif pilihan == '4':
            hapus_review(user_id)
        elif pilihan == '5':
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
            lihat_profil(user_id, 'customer')
        elif pilihan == '2':
            edit_profil(user_id, 'customer')
        elif pilihan == '3':
            lihat_riwayat_pembelian(user_id)
        elif pilihan == '4':
            menu_review(user_id)
        elif pilihan == '5':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Menu Produk
def menu_produk(user_id):
    while True:
        print("\n===== Menu Produk =====")
        print("1. Lihat Semua Produk")
        print("2. Cari Produk")
        print("3. Menu Wishlist")
        print("4. Kembali ke Menu Utama")

        pilihan = input("Pilih menu (1-4): ")

        if pilihan == '1':
            tampilkan_produk()
        elif pilihan == '2':
            cari_produk()
        elif pilihan == '3':
            menu_wishlist(user_id)
        elif pilihan == '4':
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

# Cari Produk
def cari_produk():
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        print("\n===== Cari Produk =====")
        print("1. Cari berdasarkan Nama")
        print("2. Cari berdasarkan Kategori")
        print("3. Kembali")
        
        pilihan = input("Pilih metode pencarian (1-3): ")
        
        if pilihan == "3":
            return
            
        if pilihan == "1":
            keyword = input("\nMasukkan nama produk yang dicari: ")
            # Using LIKE with wildcards for partial matches
            query = """
                SELECT p.*, c.categories_name as category_name, s.store_name as seller_name
                FROM products p
                JOIN categories c ON p.category_id = c.category_id
                JOIN seller s ON p.seller_id = s.seller_id
                WHERE p.name LIKE %s
                ORDER BY p.date_posted DESC
            """
            cursor.execute(query, (f"%{keyword}%",))
            
        elif pilihan == "2":
            print("\nKategori yang tersedia:")
            tampilkan_kategori()
            
            try:
                kategori_id = int(input("\nMasukkan ID kategori: "))
                query = """
                    SELECT p.*, c.categories_name as category_name, s.store_name as seller_name
                    FROM products p
                    JOIN categories c ON p.category_id = c.category_id
                    JOIN seller s ON p.seller_id = s.seller_id
                    WHERE p.category_id = %s
                    ORDER BY p.date_posted DESC
                """
                cursor.execute(query, (kategori_id,))
            except ValueError:
                print("❌ ID Kategori harus berupa angka!")
                return
        else:
            print("❌ Pilihan tidak valid!")
            return
            
        products = cursor.fetchall()
        
        if not products:
            print("❌ Tidak ada produk yang ditemukan!")
            return
            
        # Get ratings from MongoDB
        db = create_mongo_connection()
        if not db:
            return
            
        print("\n📦 Hasil Pencarian: ")
        for product in products:
            # Calculate average rating
            reviews = db.Review.find({"product_id": product['product_id']})
            total_rating = 0
            review_count = 0
            
            for review in reviews:
                total_rating += review['rating']
                review_count += 1
                
            avg_rating = total_rating / review_count if review_count > 0 else 0
            
            print(f"\nID: {product['product_id']}")
            print(f"Nama: {product['name']}")
            print(f"Deskripsi: {product['description']}")
            print(f"Kategori: {product['category_name']}")
            print(f"Toko: {product['seller_name']}")
            print(f"Harga: Rp {product['price']:,.2f}")
            print(f"Stok: {product['stock']}")
            print(f"Tanggal Posting: {product['date_posted']}")
            print(f"Rating: {avg_rating:.1f} ⭐ ({review_count} review)")
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Tambah ke Wishlist
def tambah_ke_wishlist(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get user_id for the customer
        cursor.execute("SELECT user_id FROM users WHERE customer_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return
            
        # Show available products
        tampilkan_produk()
        
        product_id = int(input("\nMasukkan ID produk yang ingin ditambah ke wishlist: "))
        
        # Check if product exists
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            print("❌ Produk tidak ditemukan!")
            return
            
        # Check if product already in wishlist
        cursor.execute("""
            SELECT * FROM wishlist 
            WHERE user_id = %s AND product_id = %s
        """, (user['user_id'], product_id))
        
        if cursor.fetchone():
            print("❌ Produk sudah ada dalam wishlist!")
            return
            
        # Add to wishlist
        cursor.execute("""
            INSERT INTO wishlist (user_id, product_id)
            VALUES (%s, %s)
        """, (user['user_id'], product_id))
        
        connection.commit()
        print("✅ Produk berhasil ditambahkan ke wishlist!")
        
    except ValueError:
        print("❌ ID Produk harus berupa angka!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Lihat Wishlist
def lihat_wishlist(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get user_id for the customer
        cursor.execute("SELECT user_id FROM users WHERE customer_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return False
        
        # Get wishlist items with product details
        query = """
            SELECT w.wishlist_id, p.*, c.categories_name as category_name, 
                   s.store_name as seller_name
            FROM wishlist w
            JOIN products p ON w.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            JOIN seller s ON p.seller_id = s.seller_id
            WHERE w.user_id = %s
            ORDER BY w.wishlist_id DESC
        """
        cursor.execute(query, (user['user_id'],))
        items = cursor.fetchall()
        
        if not items:
            print("Wishlist masih kosong.")
            return False
            
        # Get ratings from MongoDB
        db = create_mongo_connection()
        if not db:
            return False
            
        print("\n💝 Wishlist Anda:")
        for item in items:
            # Calculate average rating
            reviews = db.Review.find({"product_id": item['product_id']})
            total_rating = 0
            review_count = 0
            
            for review in reviews:
                total_rating += review['rating']
                review_count += 1
                
            avg_rating = total_rating / review_count if review_count > 0 else 0
            
            print(f"\nID Wishlist: {item['wishlist_id']}")
            print(f"Produk: {item['name']}")
            print(f"Deskripsi: {item['description']}")
            print(f"Kategori: {item['category_name']}")
            print(f"Toko: {item['seller_name']}")
            print(f"Harga: Rp {item['price']:,.2f}")
            print(f"Stok: {item['stock']}")
            print(f"Rating: {avg_rating:.1f} ⭐ ({review_count} review)")
            print("-" * 50)
            
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Hapus dari Wishlist
def hapus_dari_wishlist(user_id):
    if not lihat_wishlist(user_id):
        return
        
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get user_id for the customer
        cursor.execute("SELECT user_id FROM users WHERE customer_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ User tidak ditemukan!")
            return
            
        wishlist_id = int(input("\nMasukkan ID Wishlist yang ingin dihapus: "))
        
        # Delete from wishlist
        cursor.execute("""
            DELETE FROM wishlist 
            WHERE wishlist_id = %s AND user_id = %s
        """, (wishlist_id, user['user_id']))
        
        if cursor.rowcount > 0:
            connection.commit()
            print("✅ Item berhasil dihapus dari wishlist!")
        else:
            print("❌ Item wishlist tidak ditemukan!")
        
    except ValueError:
        print("❌ ID Wishlist harus berupa angka!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Menu Wishlist
def menu_wishlist(user_id):
    while True:
        print("\n===== Menu Wishlist =====")
        print("1. Lihat Wishlist")
        print("2. Tambah ke Wishlist")
        print("3. Hapus dari Wishlist")
        print("4. Kembali")

        pilihan = input("Pilih menu (1-4): ")

        if pilihan == '1':
            lihat_wishlist(user_id)
        elif pilihan == '2':
            tambah_ke_wishlist(user_id)
        elif pilihan == '3':
            hapus_dari_wishlist(user_id)
        elif pilihan == '4':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Balas Review (untuk seller)
def balas_review(seller_id):
    connection = None
    cursor = None
    try:
        # Get seller info from MySQL
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get seller's store name
        cursor.execute("""
            SELECT s.*, u.name as seller_name
            FROM seller s
            JOIN users u ON u.seller_id = s.seller_id
            WHERE s.seller_id = %s
        """, (seller_id,))
        seller = cursor.fetchone()
        if not seller:
            print("❌ Seller tidak ditemukan!")
            return
            
        # Get seller's products
        cursor.execute("""
            SELECT product_id, name 
            FROM products 
            WHERE seller_id = %s
        """, (seller_id,))
        products = cursor.fetchall()
        
        if not products:
            print("❌ Anda belum memiliki produk!")
            return
            
        # Get MongoDB connection
        db = create_mongo_connection()
        if not db:
            return
            
        # Get all reviews for seller's products
        product_ids = [p['product_id'] for p in products]
        reviews = list(db.Review.find({"product_id": {"$in": product_ids}}).sort("created_at", -1))
        
        if not reviews:
            print("❌ Belum ada review untuk produk Anda!")
            return
            
        # Show all reviews
        print("\n📝 Daftar Review Produk Anda:")
        for i, review in enumerate(reviews, 1):
            print(f"\n{i}. Produk: {review['product_name']}")
            print(f"   Dari: {review['user_name']}")
            print(f"   Rating: {'⭐' * review['rating']}")
            print(f"   Komentar: {review['comment']}")
            print(f"   Tanggal: {review['created_at'].strftime('%d-%m-%Y %H:%M')}")
            
            if review.get('replies'):
                print("   Balasan:")
                for reply in review['replies']:
                    print(f"   - {reply['user_name']}: {reply['comment']}")
            print("-" * 40)
            
        # Select review to reply
        try:
            choice = int(input("\nPilih nomor review yang ingin dibalas (0 untuk batal): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(reviews):
                print("❌ Pilihan tidak valid!")
                return
        except ValueError:
            print("❌ Pilihan harus berupa angka!")
            return
            
        selected_review = reviews[choice - 1]
        
        # Check if seller has already replied
        seller_replies = [r for r in selected_review.get('replies', []) 
                         if r['user_name'] == seller['store_name']]
        if seller_replies:
            print("\nAnda sudah membalas review ini:")
            for reply in seller_replies:
                print(f"- {reply['comment']}")
            
            edit = input("\nIngin mengedit balasan? (y/n): ")
            if edit.lower() != 'y':
                return
        
        # Get reply
        reply = input("\nTulis balasan Anda: ")
        if not reply.strip():
            print("❌ Balasan tidak boleh kosong!")
            return
            
        # Add reply to review
        new_reply = {
            "user_name": seller['store_name'],
            "comment": reply,
            "created_at": datetime.now()
        }
        
        if seller_replies:
            # Update existing reply
            db.Review.update_one(
                {
                    "_id": selected_review["_id"],
                    "replies.user_name": seller['store_name']
                },
                {
                    "$set": {
                        "replies.$.comment": reply,
                        "replies.$.created_at": datetime.now()
                    }
                }
            )
        else:
            # Add new reply
            db.Review.update_one(
                {"_id": selected_review["_id"]},
                {"$push": {"replies": new_reply}}
            )
        
        print("\n✅ Balasan berhasil ditambahkan!")
        print("\nReview dengan balasan:")
        print(f"Produk: {selected_review['product_name']}")
        print(f"Dari: {selected_review['user_name']}")
        print(f"Rating: {'⭐' * selected_review['rating']}")
        print(f"Komentar: {selected_review['comment']}")
        print(f"Balasan Anda: {reply}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Tambah Promo/Diskon
def tambah_promo(seller_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get seller's products
        cursor.execute("""
            SELECT product_id, name, price 
            FROM products 
            WHERE seller_id = %s
        """, (seller_id,))
        products = cursor.fetchall()
        
        if not products:
            print("❌ Anda belum memiliki produk!")
            return
            
        print("\n📦 Daftar Produk Anda:")
        for product in products:
            print(f"ID: {product['product_id']} - {product['name']} (Rp {product['price']:,.2f})")
            
        try:
            product_id = int(input("\nMasukkan ID produk untuk diskon: "))
            # Verify product belongs to seller
            product = next((p for p in products if p['product_id'] == product_id), None)
            if not product:
                print("❌ Produk tidak ditemukan atau bukan milik Anda!")
                return
        except ValueError:
            print("❌ ID produk harus berupa angka!")
            return
                
        while True:
            try:
                discount = float(input("Masukkan persentase diskon (1-100): "))
                if 0 < discount <= 100:
                    break
                print("❌ Persentase harus antara 1-100!")
            except ValueError:
                print("❌ Masukkan angka yang valid!")
                    
        # Set validity period
        print("\nMasa Berlaku Diskon:")
        start_date = input("Tanggal mulai (YYYY-MM-DD): ")
        end_date = input("Tanggal berakhir (YYYY-MM-DD): ")
        
        # Insert discount
        cursor.execute("""
            INSERT INTO discounts (product_id, discount_percentage, start_date, end_date)
            VALUES (%s, %s, %s, %s)
        """, (product_id, discount, start_date, end_date))
        
        connection.commit()
        print("\n✅ Diskon berhasil ditambahkan!")
        print(f"Produk: {product['name']}")
        print(f"Diskon: {discount}%")
        print(f"Periode: {start_date} s/d {end_date}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Lihat Promo/Diskon (Seller)
def lihat_promo_seller(seller_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get seller's active discounts
        cursor.execute("""
            SELECT d.*, p.name as product_name, p.price as original_price
            FROM discounts d
            JOIN products p ON d.product_id = p.product_id
            WHERE p.seller_id = %s AND d.end_date >= CURDATE()
            ORDER BY d.start_date
        """, (seller_id,))
        discounts = cursor.fetchall()
        
        if not discounts:
            print("❌ Tidak ada diskon aktif!")
            return
            
        print("\n🏷️ Daftar Diskon Aktif:")
        for discount in discounts:
            print(f"\nProduk: {discount['product_name']}")
            print(f"Diskon: {discount['discount_percentage']}%")
            print(f"Periode: {discount['start_date']} s/d {discount['end_date']}")
            
            # Calculate discounted price
            final_price = discount['original_price'] * (1 - discount['discount_percentage']/100)
            print(f"Harga Asli: Rp {discount['original_price']:,.2f}")
            print(f"Harga Setelah Diskon: Rp {final_price:,.2f}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Hapus Promo/Diskon
def hapus_promo(seller_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get seller's active discounts
        cursor.execute("""
            SELECT d.discount_id, d.discount_percentage, p.name as product_name
            FROM discounts d
            JOIN products p ON d.product_id = p.product_id
            WHERE p.seller_id = %s AND d.end_date >= CURDATE()
            ORDER BY d.start_date
        """, (seller_id,))
        discounts = cursor.fetchall()
        
        if not discounts:
            print("❌ Tidak ada diskon aktif yang bisa dihapus!")
            return
            
        print("\n🏷️ Daftar Diskon Aktif:")
        for discount in discounts:
            print(f"ID: {discount['discount_id']} - {discount['product_name']} (Diskon {discount['discount_percentage']}%)")
            
        try:
            discount_id = int(input("\nMasukkan ID diskon yang ingin dihapus: "))
            
            # Verify discount belongs to seller's product
            cursor.execute("""
                SELECT d.* 
                FROM discounts d
                JOIN products p ON d.product_id = p.product_id
                WHERE d.discount_id = %s AND p.seller_id = %s
            """, (discount_id, seller_id))
            
            if not cursor.fetchone():
                print("❌ Diskon tidak ditemukan atau bukan milik Anda!")
                return
                
            # Delete discount
            cursor.execute("DELETE FROM discounts WHERE discount_id = %s", (discount_id,))
            connection.commit()
            
            print("✅ Diskon berhasil dihapus!")
            
        except ValueError:
            print("❌ ID diskon harus berupa angka!")
            return
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Menu Promo (Seller)
def menu_promo_seller(seller_id):
    while True:
        print("\n===== Menu Promo & Diskon =====")
        print("1. Lihat Diskon Aktif")
        print("2. Tambah Diskon")
        print("3. Hapus Diskon")
        print("4. Kembali")

        pilihan = input("Pilih menu (1-4): ")

        if pilihan == '1':
            lihat_promo_seller(seller_id)
        elif pilihan == '2':
            tambah_promo(seller_id)
        elif pilihan == '3':
            hapus_promo(seller_id)
        elif pilihan == '4':
            break
        else:
            print("❌ Pilihan tidak valid!")

# Lihat Promo (Customer)
def lihat_promo():
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get all active discounts
        cursor.execute("""
            SELECT d.*, p.name as product_name, p.price as original_price,
                   s.store_name
            FROM discounts d
            JOIN products p ON d.product_id = p.product_id
            JOIN seller s ON p.seller_id = s.seller_id
            WHERE d.end_date >= CURDATE()
            ORDER BY d.start_date
        """)
        discounts = cursor.fetchall()
        
        if not discounts:
            print("❌ Tidak ada diskon aktif saat ini!")
            return
            
        print("\n🏷️ Daftar Diskon Aktif:")
        for discount in discounts:
            print(f"\nProduk: {discount['product_name']}")
            print(f"Toko: {discount['store_name']}")
            print(f"Diskon: {discount['discount_percentage']}%")
            print(f"Periode: {discount['start_date']} s/d {discount['end_date']}")
            
            # Calculate discounted price
            final_price = discount['original_price'] * (1 - discount['discount_percentage']/100)
            print(f"Harga Asli: Rp {discount['original_price']:,.2f}")
            print(f"Harga Setelah Diskon: Rp {final_price:,.2f}")
            print(f"Hemat: Rp {(discount['original_price'] - final_price):,.2f}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Update checkout_trolley to include discounts
def checkout_trolley(user_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get items in trolley with product details and active discounts
        cursor.execute("""
            SELECT t.*, p.name, p.price, p.stock, s.store_name,
                   d.discount_id, d.discount_percentage
            FROM trolley t
            JOIN products p ON t.product_id = p.product_id
            JOIN seller s ON p.seller_id = s.seller_id
            LEFT JOIN discounts d ON p.product_id = d.product_id 
                AND CURDATE() BETWEEN d.start_date AND d.end_date
            WHERE t.user_id = %s
        """, (user_id,))
        items = cursor.fetchall()
        
        if not items:
            print("❌ Trolley kosong!")
            return
            
        # Group items by seller
        sellers = {}
        for item in items:
            if item['store_name'] not in sellers:
                sellers[item['store_name']] = []
            sellers[item['store_name']].append(item)
            
        # Display items and calculate total
        print("\n🛒 Checkout Trolley:")
        total_price = 0
        total_discount = 0
        
        for store_name, store_items in sellers.items():
            print(f"\n📍 Toko: {store_name}")
            store_total = 0
            
            for item in store_items:
                # Check stock
                if item['quantity'] > item['stock']:
                    print(f"❌ Stok {item['name']} tidak mencukupi!")
                    return
                    
                # Calculate price with discount if available
                item_price = item['price'] * item['quantity']
                discounted_price = item_price
                
                if item['discount_id']:
                    discount = item_price * (item['discount_percentage'] / 100)
                    discounted_price = item_price - discount
                    
                    print(f"\n{item['name']} ({item['quantity']}x)")
                    print(f"Harga Asli: Rp {item_price:,.2f}")
                    print(f"Diskon: {item['discount_percentage']}%")
                    print(f"Harga Setelah Diskon: Rp {discounted_price:,.2f}")
                    print(f"Hemat: Rp {(item_price - discounted_price):,.2f}")
                else:
                    print(f"\n{item['name']} ({item['quantity']}x)")
                    print(f"Harga: Rp {item_price:,.2f}")
                
                store_total += discounted_price
                total_discount += (item_price - discounted_price)
                
            print(f"\nSubtotal {store_name}: Rp {store_total:,.2f}")
            total_price += store_total
            
        print("\n💰 Total Belanja:")
        print(f"Total Harga: Rp {(total_price + total_discount):,.2f}")
        print(f"Total Diskon: Rp {total_discount:,.2f}")
        print(f"Total Pembayaran: Rp {total_price:,.2f}")
        
        # Confirm order
        confirm = input("\nLanjutkan checkout? (y/n): ")
        if confirm.lower() != 'y':
            return
            
        # Process payment
        payment_method = None
        while payment_method not in ['1', '2', '3']:
            print("\nMetode Pembayaran:")
            print("1. Transfer Bank")
            print("2. E-Wallet")
            print("3. COD (Cash On Delivery)")
            payment_method = input("Pilih metode pembayaran (1-3): ")
            
        payment_methods = {
            '1': 'Transfer Bank',
            '2': 'E-Wallet',
            '3': 'COD'
        }
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (user_id, total_price, order_date)
            VALUES (%s, %s, NOW())
        """, (user_id, total_price))
        order_id = cursor.lastrowid
        
        # Create payment record
        cursor.execute("""
            INSERT INTO payment (order_id, payment_method, payment_status, payment_date)
            VALUES (%s, %s, 'success', NOW())
        """, (order_id, payment_methods[payment_method]))
        
        # Update product stock and clear trolley
        for item in items:
            # Update stock
            cursor.execute("""
                UPDATE products 
                SET stock = stock - %s 
                WHERE product_id = %s
            """, (item['quantity'], item['product_id']))
            
            # Clear item from trolley
            cursor.execute("""
                DELETE FROM trolley 
                WHERE trolley_id = %s
            """, (item['trolley_id'],))
            
        connection.commit()
        print("\n✅ Pesanan berhasil dibuat!")
        print(f"Order ID: {order_id}")
        print(f"Total Pembayaran: Rp {total_price:,.2f}")
        print(f"Metode Pembayaran: {payment_methods[payment_method]}")
        print("Status: Pembayaran Berhasil")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

# Menu Seller
def menu_seller(user_id):
    while True:
        print("\n===== MENU UTAMA SELLER =====")
        print("1. Menu Produk")
        print("2. Menu Kategori")
        print("3. Menu Profil")
        print("4. Menu Review")
        print("5. Menu Promo")
        print("6. Logout")

        pilihan = input("Pilih menu (1-6): ")

        if pilihan == '1':
            menu_produk_seller(user_id)
        elif pilihan == '2':
            menu_kategori()
        elif pilihan == '3':
            menu_profil_seller(user_id)
        elif pilihan == '4':
            menu_review_seller(user_id)
        elif pilihan == '5':
            menu_promo_seller(user_id)
        elif pilihan == '6':
            print("🔒 Logout berhasil.\n")
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
                if role == 'seller':
                    menu_seller(user_id)
                else:
                    menu_customer(user_id)
        elif pilihan == '2':
            register_user()
        elif pilihan == '3':
            print("🚪 Keluar dari program...")
            break
        else:
            print("❌ Pilihan tidak valid!")

# Jalankan program
if __name__ == "__main__":
    main_menu()
