# add_admin_railway.py
import psycopg2

# ✅ RAILWAY DATABASE_URL (Railway se copy karke yahan paste karo)
DATABASE_URL="postgresql://postgres:Mohit%4018@db.lrkakuepzkohhrlwaytp.supabase.co:5432/postgres"

try:
    print("🔗 Connecting to Railway database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("✅ Connected!")
    
    # 1. Add is_admin column
    print("\n📝 Adding is_admin column...")
    cursor.execute("""
        ALTER TABLE customers 
        ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL
    """)
    print("✅ Column added (or already exists)")
    
    # 2. Make sahumohit643@gmail.com admin
    print("\n👑 Creating admin user...")
    cursor.execute("""
        UPDATE customers 
        SET is_admin = TRUE 
        WHERE email = 'sahumohit643@gmail.com'
    """)
    rows_updated = cursor.rowcount
    
    if rows_updated > 0:
        print(f"✅ Admin created ({rows_updated} row updated)")
    else:
        print("⚠️  User not found in database")
        print("   Please login with Google first at: https://thepureanddesi.com")
    
    # 3. Verify admin user
    print("\n🔍 Verifying admin user...")
    cursor.execute("""
        SELECT id, email, full_name, phone, is_admin, created_at 
        FROM customers 
        WHERE email = 'sahumohit643@gmail.com'
    """)
    admin = cursor.fetchone()
    
    if admin:
        print(f"\n✅ ADMIN USER FOUND:")
        print(f"   ID: {admin[0]}")
        print(f"   Email: {admin[1]}")
        print(f"   Name: {admin[2]}")
        print(f"   Phone: {admin[3]}")
        print(f"   Is Admin: {admin[4]}")
        print(f"   Created: {admin[5]}")
    else:
        print("\n⚠️  No user found with email: sahumohit643@gmail.com")
    
    # Commit changes
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ MIGRATION COMPLETE!")
    
except psycopg2.Error as e:
    print(f"\n❌ Database Error: {e}")
    print(f"   Error Code: {e.pgcode}")
    print(f"   Details: {e.pgerror}")
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()