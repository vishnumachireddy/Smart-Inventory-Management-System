#!/usr/bin/env python3
"""
Seed Demo Data Script for StockSense
Generates a realistic, reproducible synthetic dataset for small retail demonstrations.
Tailored for low-latency Neon Serverless PostgreSQL batch execution.
"""

import sys
import os
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import numpy as np

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal, Base, create_db_engine
from app.core.security import get_password_hash
from app.models import (
    User,
    Category,
    Supplier,
    Product,
    InventoryBatch,
    StockMovement,
    Sale,
    SaleItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
    Alert,
    NotificationSettings,
    DailyInventorySnapshot,
    AppSetting,
)
from app.services.inventory_alert_service import InventoryAlertService


def seed_all():
    print("=" * 70)
    print("StockSense - High-Performance Neon Seed Script")
    print("=" * 70)

    # Set deterministic random seed
    random.seed(42)
    np.random.seed(42)

    db_eng = create_db_engine()
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_eng)
    db = Session()

    try:
        print("[1/7] Provisioning Default Demo Users...")
        owner = db.query(User).filter(User.email == "owner@stocksense.com").first()
        if not owner:
            owner = User(
                email="owner@stocksense.com",
                hashed_password=get_password_hash("Owner@123"),
                full_name="Rajesh Sharma (Owner)",
                role="shop_owner",
                is_active=True
            )
            db.add(owner)
            print("  Created demo owner: owner@stocksense.com / Owner@123")
        else:
            print("  Demo owner exists.")

        staff = db.query(User).filter(User.email == "staff@stocksense.com").first()
        if not staff:
            staff = User(
                email="staff@stocksense.com",
                hashed_password=get_password_hash("Staff@123"),
                full_name="Pooja Verma (Staff)",
                role="staff",
                is_active=True
            )
            db.add(staff)
            print("  Created demo staff: staff@stocksense.com / Staff@123")
        else:
            print("  Demo staff exists.")

        db.commit()
        owner = db.query(User).filter(User.email == "owner@stocksense.com").first()
        staff = db.query(User).filter(User.email == "staff@stocksense.com").first()

        print("[2/7] Checking Categories & Suppliers...")
        categories_data = [
            ("Dairy & Eggs", "Fresh milk, cheese, butter, yogurt, and farm eggs"),
            ("Bakery & Breads", "Artisan breads, sandwich loaves, buns, and cookies"),
            ("Beverages", "Juices, soft drinks, teas, packaged water, and coffee"),
            ("Snacks & Confectionery", "Chips, crisps, biscuits, chocolates, and nuts"),
            ("Staples & Grains", "Rice, wheat flour, lentils, cooking oils, and sugar"),
            ("Personal Care", "Soaps, shampoos, toothpaste, skin care, and sanitizers"),
            ("Household & Cleaning", "Detergents, surface cleaners, dishwash liquids, and wipes"),
        ]

        cat_map = {}
        for name, desc in categories_data:
            cat = db.query(Category).filter(Category.name == name).first()
            if not cat:
                cat = Category(name=name, description=desc)
                db.add(cat)
                db.flush()
            cat_map[name] = cat.id

        suppliers_data = [
            ("Apex Dairy & Cold Storage", "Manish Mehra", "apex@dairy.in", "+91 98111 22334", "Plot 12, Okhla Phase II, New Delhi", 2, 28.5355, 77.2731),
            ("Golden Harvest Foods", "Suman Lata", "sales@goldenharvest.com", "+91 98222 33445", "Sector 18, Gurugram, Haryana", 4, 28.4595, 77.0266),
            ("PureBeverages Supply Co.", "Vikas Oberoi", "orders@purebev.in", "+91 98333 44556", "Site 4 Industrial Area, Sahibabad, UP", 3, 28.6712, 77.3481),
            ("Swastik FMCG Distributors", "Anand Singhania", "contact@swastikdist.in", "+91 98444 55667", "Azadpur Mandi, Delhi", 5, 28.7041, 77.1025),
            ("CleanHome Care Products", "Ritu Sethi", "support@cleancare.in", "+91 98555 66778", "Udyog Vihar Phase IV, Gurugram", 6, 28.4986, 77.0878),
        ]

        sup_map = {}
        for s_data in suppliers_data:
            sup = db.query(Supplier).filter(Supplier.name == s_data[0]).first()
            if not sup:
                sup = Supplier(
                    name=s_data[0],
                    contact_name=s_data[1],
                    email=s_data[2],
                    phone=s_data[3],
                    address=s_data[4],
                    lead_time_days=s_data[5],
                    latitude=s_data[6],
                    longitude=s_data[7],
                )
                db.add(sup)
                db.flush()
            sup_map[s_data[0]] = sup.id

        db.commit()

        print("[3/7] Provisioning Catalog Products...")
        products_spec = [
            # Dairy
            ("Amul Taaza Homogenised Toned Milk 1L", "DAI-001", "8901262010014", "Dairy & Eggs", "Apex Dairy & Cold Storage", "pack", 68.00, 75.00, 20),
            ("Mother Dairy Cow Milk 500ml", "DAI-002", "8901262010021", "Dairy & Eggs", "Apex Dairy & Cold Storage", "pack", 30.00, 34.00, 25),
            ("Amul Butter Pasteurised 500g", "DAI-003", "8901262010038", "Dairy & Eggs", "Apex Dairy & Cold Storage", "pack", 240.00, 275.00, 15),
            ("Britannia Cheese Slices 200g (10 Slices)", "DAI-004", "8901262010045", "Dairy & Eggs", "Apex Dairy & Cold Storage", "pack", 125.00, 145.00, 12),
            ("Farm Fresh White Eggs (Pack of 6)", "DAI-005", "8901262010052", "Dairy & Eggs", "Apex Dairy & Cold Storage", "pack", 42.00, 52.00, 30),
            ("Epigamia Greek Yogurt Natural 90g", "DAI-006", "8901262010069", "Dairy & Eggs", "Apex Dairy & Cold Storage", "cup", 45.00, 55.00, 15),

            # Bakery
            ("Harvest Gold White Sandwich Bread 400g", "BAK-001", "8901262020013", "Bakery & Breads", "Golden Harvest Foods", "pack", 32.00, 40.00, 20),
            ("English Oven 100% Whole Wheat Bread 400g", "BAK-002", "8901262020020", "Bakery & Breads", "Golden Harvest Foods", "pack", 42.00, 50.00, 18),
            ("Britannia Little Hearts Biscuits 75g", "BAK-003", "8901262020037", "Bakery & Breads", "Golden Harvest Foods", "pack", 16.00, 20.00, 30),
            ("Sunfeast Dark Fantasy Choco Fills 300g", "BAK-004", "8901262020044", "Bakery & Breads", "Golden Harvest Foods", "pack", 110.00, 140.00, 15),
            ("Oreo Vanilla Creme Biscuits 120g", "BAK-005", "8901262020051", "Bakery & Breads", "Golden Harvest Foods", "pack", 28.00, 35.00, 25),

            # Beverages
            ("Tropicana 100% Orange Juice 1L", "BEV-001", "8901262030012", "Beverages", "PureBeverages Supply Co.", "pack", 115.00, 140.00, 15),
            ("Real Fruit Power Mixed Fruit Juice 1L", "BEV-002", "8901262030029", "Beverages", "PureBeverages Supply Co.", "pack", 100.00, 125.00, 20),
            ("Coca-Cola Original 750ml PET Bottle", "BEV-003", "8901262030036", "Beverages", "PureBeverages Supply Co.", "bottle", 32.00, 40.00, 25),
            ("Red Bull Energy Drink Can 250ml", "BEV-004", "8901262030043", "Beverages", "PureBeverages Supply Co.", "can", 98.00, 125.00, 20),
            ("Bisleri Packaged Mineral Water 1L", "BEV-005", "8901262030050", "Beverages", "PureBeverages Supply Co.", "bottle", 14.00, 20.00, 40),
            ("Tata Tea Premium Leaf Tea 500g", "BEV-006", "8901262030067", "Beverages", "PureBeverages Supply Co.", "pack", 210.00, 260.00, 15),

            # Snacks
            ("Lay's India's Magic Masala Chips 50g", "SNK-001", "8901262040011", "Snacks & Confectionery", "Swastik FMCG Distributors", "pack", 16.00, 20.00, 35),
            ("Kurkure Masala Munch 85g", "SNK-002", "8901262040028", "Snacks & Confectionery", "Swastik FMCG Distributors", "pack", 16.00, 20.00, 30),
            ("Haldiram's Bhujia Sev 400g", "SNK-003", "8901262040035", "Snacks & Confectionery", "Swastik FMCG Distributors", "pack", 95.00, 120.00, 20),
            ("Cadbury Dairy Milk Silk Chocolate 150g", "SNK-004", "8901262040042", "Snacks & Confectionery", "Swastik FMCG Distributors", "pack", 145.00, 175.00, 20),
            ("Act II Golden Sizzle Butter Popcorn 150g", "SNK-005", "8901262040059", "Snacks & Confectionery", "Swastik FMCG Distributors", "pack", 38.00, 50.00, 25),

            # Staples
            ("Fortune Sunlite Refined Sunflower Oil 1L", "STP-001", "8901262050010", "Staples & Grains", "Golden Harvest Foods", "pouch", 130.00, 155.00, 20),
            ("Aashirvaad Superior MP Sharbati Atta 5kg", "STP-002", "8901262050027", "Staples & Grains", "Golden Harvest Foods", "bag", 240.00, 290.00, 15),
            ("India Gate Basmati Rice Feast Rozzana 5kg", "STP-003", "8901262050034", "Staples & Grains", "Golden Harvest Foods", "bag", 410.00, 495.00, 12),
            ("Tata Salt Vacuum Evaporated Iodized Salt 1kg", "STP-004", "8901262050041", "Staples & Grains", "Golden Harvest Foods", "pack", 22.00, 28.00, 40),
            ("Tata Sampann Unpolished Toor Dal 1kg", "STP-005", "8901262050058", "Staples & Grains", "Golden Harvest Foods", "pack", 155.00, 185.00, 15),

            # Personal Care
            ("Dettol Original Germ Protection Bathing Soap 125g", "PER-001", "8901262060019", "Personal Care", "Swastik FMCG Distributors", "pcs", 45.00, 56.00, 25),
            ("Colgate Total Antibacterial Toothpaste 150g", "PER-002", "8901262060026", "Personal Care", "Swastik FMCG Distributors", "pack", 115.00, 140.00, 20),
            ("Head & Shoulders Cool Menthol Anti-Dandruff 180ml", "PER-003", "8901262060033", "Personal Care", "Swastik FMCG Distributors", "bottle", 160.00, 195.00, 15),
            ("Nivea Soft Light Moisturizer Cream 100ml", "PER-004", "8901262060040", "Personal Care", "Swastik FMCG Distributors", "jar", 170.00, 210.00, 15),

            # Household
            ("Vim Lemon Dishwash Gel 500ml", "HOU-001", "8901262070018", "Household & Cleaning", "CleanHome Care Products", "bottle", 105.00, 130.00, 20),
            ("Surf Excel Quick Wash Detergent Powder 1kg", "HOU-002", "8901262070025", "Household & Cleaning", "CleanHome Care Products", "pack", 185.00, 220.00, 15),
            ("Lizol Disinfectant Surface Cleaner Citrus 500ml", "HOU-003", "8901262070032", "Household & Cleaning", "CleanHome Care Products", "bottle", 88.00, 110.00, 20),
        ]

        created_products = []
        for p_data in products_spec:
            p = db.query(Product).filter(Product.sku == p_data[1]).first()
            if not p:
                p = Product(
                    name=p_data[0],
                    sku=p_data[1],
                    barcode=p_data[2],
                    category_id=cat_map[p_data[3]],
                    supplier_id=sup_map[p_data[4]],
                    unit=p_data[5],
                    purchase_cost=Decimal(str(p_data[6])),
                    selling_price=Decimal(str(p_data[7])),
                    reorder_threshold=p_data[8],
                    is_active=True
                )
                db.add(p)
                db.flush()
            created_products.append(p)
        db.commit()
        print(f"  Verified {len(created_products)} catalog products.")

        print("[4/7] Generating Batch Inventory...")
        today = date.today()
        existing_batches = db.query(InventoryBatch).all()
        
        if not existing_batches:
            batches_to_add = []
            movements_to_add = []

            for idx, prod in enumerate(created_products):
                # Batch 1: Primary Healthy Stock
                b1_received = today - timedelta(days=random.randint(25, 45))
                b1_expiry = today + timedelta(days=random.randint(60, 240)) if prod.category_id != cat_map["Staples & Grains"] else None
                qty1 = random.randint(30, 80)
                batch1 = InventoryBatch(
                    product_id=prod.id,
                    supplier_id=prod.supplier_id,
                    batch_number=f"BATCH-26A-{idx+1:03d}",
                    quantity_received=qty1,
                    current_quantity=qty1,
                    received_date=b1_received,
                    expiry_date=b1_expiry,
                    unit_cost=prod.purchase_cost,
                    status="active"
                )
                batches_to_add.append(batch1)

                # Batch 2: Near-Expiry within 7 days for demo alerts
                if idx in (0, 1, 4, 6, 11):
                    near_exp_date = today + timedelta(days=random.randint(2, 6))
                    near_qty = random.randint(8, 16)
                    batch_near = InventoryBatch(
                        product_id=prod.id,
                        supplier_id=prod.supplier_id,
                        batch_number=f"BATCH-NEAR-{idx+1:03d}",
                        quantity_received=near_qty,
                        current_quantity=near_qty,
                        received_date=today - timedelta(days=20),
                        expiry_date=near_exp_date,
                        unit_cost=prod.purchase_cost,
                        status="active"
                    )
                    batches_to_add.append(batch_near)

                # Batch 3: Already Expired for 2 items
                if idx in (2, 7):
                    exp_date = today - timedelta(days=random.randint(2, 5))
                    exp_qty = random.randint(4, 8)
                    batch_exp = InventoryBatch(
                        product_id=prod.id,
                        supplier_id=prod.supplier_id,
                        batch_number=f"BATCH-EXPD-{idx+1:03d}",
                        quantity_received=exp_qty,
                        current_quantity=exp_qty,
                        received_date=today - timedelta(days=35),
                        expiry_date=exp_date,
                        unit_cost=prod.purchase_cost,
                        status="expired"
                    )
                    batches_to_add.append(batch_exp)

            db.add_all(batches_to_add)
            db.flush()

            for b in batches_to_add:
                movements_to_add.append(StockMovement(
                    product_id=b.product_id,
                    batch_id=b.id,
                    movement_type="purchase_receipt",
                    quantity=b.quantity_received,
                    reference_id=f"INIT-{b.batch_number}",
                    reason="Initial Stock Receipt",
                    user_id=owner.id,
                    created_at=datetime.combine(b.received_date, datetime.min.time(), tzinfo=timezone.utc)
                ))

            db.add_all(movements_to_add)
            db.commit()
            print(f"  Created {len(batches_to_add)} batches and {len(movements_to_add)} stock movements.")
        else:
            print(f"  Existing batches: {len(existing_batches)}.")

        # Check sales
        existing_sales_count = db.query(Sale).count()
        if existing_sales_count < 100:
            print("[5/7] Simulating Realistic Historical POS Sales...")
            # Pre-load batches for fast in-memory FEFO simulation
            all_batches = db.query(InventoryBatch).all()
            batch_map = {}
            for b in all_batches:
                if b.product_id not in batch_map:
                    batch_map[b.product_id] = []
                batch_map[b.product_id].append(b)

            sales_count_added = 0
            movements_to_insert = []

            for day_offset in range(14, 0, -1):
                sale_date = today - timedelta(days=day_offset)
                dow = sale_date.weekday()
                num_sales = 3 if dow >= 5 else 2

                for s_idx in range(num_sales):
                    sale_time = datetime.combine(sale_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(
                        hours=random.randint(9, 20), minutes=random.randint(0, 59)
                    )
                    sale_num = f"SAL-{sale_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

                    selected_prods = random.sample(created_products, k=random.randint(1, 3))
                    subtotal = Decimal("0.00")
                    total_cost = Decimal("0.00")
                    current_sale_items = []

                    for p in selected_prods:
                        p_batches = [
                            b for b in batch_map.get(p.id, [])
                            if b.current_quantity > 0 and b.status == "active"
                        ]
                        p_batches.sort(key=lambda b: (b.expiry_date is None, b.expiry_date or date.max, b.received_date, b.id))

                        if not p_batches:
                            continue

                        req_qty = random.randint(1, 3)
                        avail = sum(b.current_quantity for b in p_batches)
                        if avail < req_qty:
                            req_qty = avail
                        if req_qty <= 0:
                            continue

                        rem = req_qty
                        for b in p_batches:
                            if rem <= 0:
                                break
                            deduct = min(b.current_quantity, rem)
                            b.current_quantity -= deduct
                            rem -= deduct

                            l_subtotal = Decimal(deduct) * p.selling_price
                            l_cost = Decimal(deduct) * b.unit_cost
                            l_profit = l_subtotal - l_cost

                            subtotal += l_subtotal
                            total_cost += l_cost

                            current_sale_items.append((p.id, b.id, deduct, p.selling_price, b.unit_cost, l_subtotal, l_cost, l_profit))
                            movements_to_insert.append(StockMovement(
                                product_id=p.id,
                                batch_id=b.id,
                                movement_type="sale",
                                quantity=-deduct,
                                reference_id=sale_num,
                                reason="POS Sale Fulfillment",
                                user_id=staff.id,
                                created_at=sale_time
                            ))

                    if current_sale_items:
                        discount = Decimal("0.00")
                        if subtotal > 500 and random.random() < 0.2:
                            discount = Decimal(str(round(float(subtotal) * 0.05, 2)))
                        total_amt = max(Decimal("0.00"), subtotal - discount)
                        gross_profit = total_amt - total_cost

                        sale_obj = Sale(
                            sale_number=sale_num,
                            subtotal=subtotal,
                            discount_amount=discount,
                            total_amount=total_amt,
                            total_cost=total_cost,
                            gross_profit=gross_profit,
                            payment_method=random.choice(["cash", "upi", "card"]),
                            status="completed",
                            user_id=staff.id,
                            created_at=sale_time,
                            items=[
                                SaleItem(
                                    product_id=it[0],
                                    batch_id=it[1],
                                    quantity=it[2],
                                    unit_price=it[3],
                                    unit_cost=it[4],
                                    line_subtotal=it[5],
                                    line_cost=it[6],
                                    line_profit=it[7]
                                )
                                for it in current_sale_items
                            ]
                        )
                        db.add(sale_obj)
                        sales_count_added += 1

            db.add_all(movements_to_insert)
            db.commit()
            print(f"  Committed {sales_count_added} sales transactions and {len(movements_to_insert)} movements.")
        else:
            print(f"  Existing sales: {existing_sales_count}.")

        print("[6/7] Initializing Notification Settings & Snapshots...")
        notif = db.query(NotificationSettings).filter(NotificationSettings.shop_id == "default_shop").first()
        if not notif:
            notif = NotificationSettings(
                user_id=owner.id,
                shop_id="default_shop",
                recipient_emails="owner@stocksense.com, manager@stocksense.com",
                enabled=True,
                report_frequency="daily",
                scheduled_time="08:00",
                timezone="Asia/Kolkata",
                categories="near_expiry,low_stock,out_of_stock,sales_summary",
                include_empty_reports=False
            )
            db.add(notif)
            db.commit()
            print("  Created default notification settings.")

        # Ensure rich alert categories for demonstration (out-of-stock, low-stock, near-expiry)
        for p_idx in [0, 5]:
            p = created_products[p_idx]
            db.query(InventoryBatch).filter(InventoryBatch.product_id == p.id).update({"current_quantity": 0})
        for p_idx in [1, 2]:
            p = created_products[p_idx]
            batches = db.query(InventoryBatch).filter(InventoryBatch.product_id == p.id).all()
            if batches:
                batches[0].current_quantity = 4
                for b_rem in batches[1:]:
                    b_rem.current_quantity = 0
        db.commit()

        # Reconcile alerts with new InventoryAlertService
        print("[7/7] Reconciling Smart Inventory Alerts...")
        from app.services.inventory_alert_service import InventoryAlertService
        summary = InventoryAlertService.reconcile_and_snapshot(db)
        db.commit()
        print(f"  Alerts reconciled: near_expiry={summary['summary']['near_expiry_count']}, low_stock={summary['summary']['low_stock_count']}, out_of_stock={summary['summary']['out_of_stock_count']}")

        print("=" * 70)
        print("StockSense Demonstration Dataset Successfully Seeded into Neon PostgreSQL!")
        print("=" * 70)
        print("Demo Credentials:")
        print("  Shop Owner: owner@stocksense.com / Owner@123")
        print("  Staff:      staff@stocksense.com / Staff@123")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
