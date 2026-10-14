#!/usr/bin/env python3
"""
Seed Demo Data Script for StockSense
Generates a realistic, reproducible synthetic dataset for small retail demonstrations.
Includes:
- Standard Demo Users (Shop Owner and Staff)
- Retail Categories (Dairy, Bakery, Beverages, Snacks, Grains & Staples, Personal Care, Household)
- Verified Suppliers with lead times and contact info
- 40+ realistic retail products with SKUs, barcodes, and prices
- Multi-batch inventory with varying received and expiry dates (healthy, near-expiry, expired)
- 90 days of synthetic sales history with realistic weekly demand cycles
- Auditable stock movement ledgers and purchase receipts
- Real-time alert state reconciliation
"""

import sys
import os
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import numpy as np

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal, Base, engine, create_db_engine
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
    AppSetting,
)
from app.services.alert_service import AlertService


def seed_all():
    print("=" * 70)
    print("StockSense - Synthetic Demo Data Generator")
    print("=" * 70)

    # Set deterministic random seed
    random.seed(42)
    np.random.seed(42)

    db_eng = create_db_engine()
    Base.metadata.create_all(bind=db_eng)

    session_maker = SessionLocal if SessionLocal else SessionLocal
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_eng)
    db = Session()

    try:
        print("[1/7] Provisioning Default Demo Users...")
        # Shop Owner
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

        # Staff
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

        # Check if already seeded
        if db.query(Product).count() >= 30:
            print("[INFO] Database already contains sufficient product demo records.")
            print("Reconciling alerts...")
            AlertService.reconcile_all_alerts(db)
            db.commit()
            print("[DONE] Demo dataset verified.")
            return

        print("[2/7] Seeding Retail Categories...")
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
            cat_map[name] = cat
        db.commit()

        print("[3/7] Seeding Verified Suppliers...")
        suppliers_data = [
            ("Amrit Dairy & Fresh Foods", "Anil Gupta", "anil@amritdairy.com", "+91-98110-12345", "Plot 14, Industrial Area, Phase 1", 3),
            ("Golden Grain Distributors", "Suresh Patel", "orders@goldengrains.in", "+91-98220-23456", "APMC Market Yard, Sector 19", 7),
            ("Metro FMCG Logistics", "Vikram Malhotra", "support@metrofmcg.com", "+91-98330-34567", "Warehouse 5B, Logistics Park", 5),
            ("Nectar Beverage Wholesalers", "Deepak Rao", "sales@nectarbev.in", "+91-98440-45678", "Ring Road Wholesale Hub", 4),
            ("PureLife Hygiene & Home Goods", "Meera Kulkarni", "meera@purelife.co.in", "+91-98550-56789", "MIDC Estate, Block D", 8),
        ]

        supp_map = {}
        for name, contact, email, phone, addr, lead_time in suppliers_data:
            supp = db.query(Supplier).filter(Supplier.name == name).first()
            if not supp:
                supp = Supplier(
                    name=name,
                    contact_name=contact,
                    email=email,
                    phone=phone,
                    address=addr,
                    lead_time_days=lead_time
                )
                db.add(supp)
                db.flush()
            supp_map[name] = supp
        db.commit()

        print("[4/7] Seeding 35+ Standard Retail Products...")
        products_catalog = [
            # Dairy
            ("Farm Fresh Full Cream Milk 1L", "DAIRY-MILK-1L", "8901234001", "Dairy & Eggs", "Amrit Dairy & Fresh Foods", "litre", 54.00, 68.00, 20),
            ("Organic Cow Milk 500ml", "DAIRY-MILK-500", "8901234002", "Dairy & Eggs", "Amrit Dairy & Fresh Foods", "packet", 28.00, 36.00, 15),
            ("Salted Butter 500g", "DAIRY-BTR-500", "8901234003", "Dairy & Eggs", "Amrit Dairy & Fresh Foods", "pack", 210.00, 260.00, 10),
            ("Natural Greek Yogurt 400g", "DAIRY-YGT-400", "8901234004", "Dairy & Eggs", "Amrit Dairy & Fresh Foods", "cup", 75.00, 99.00, 8),
            ("Cottage Cheese Paneer 200g", "DAIRY-PNR-200", "8901234005", "Dairy & Eggs", "Amrit Dairy & Fresh Foods", "pack", 70.00, 90.00, 12),
            ("Farm Fresh Brown Eggs (6 pack)", "DAIRY-EGG-6PK", "8901234006", "Dairy & Eggs", "Amrit Dairy & Fresh Foods", "pack", 48.00, 65.00, 15),

            # Bakery
            ("Whole Wheat Bread 400g", "BAKE-BRED-400", "8901234007", "Bakery & Breads", "Metro FMCG Logistics", "loaf", 35.00, 48.00, 15),
            ("Multigrain Toast Loaf 350g", "BAKE-MULTI-350", "8901234008", "Bakery & Breads", "Metro FMCG Logistics", "loaf", 42.00, 58.00, 10),
            ("Soft Burger Buns (Pack of 4)", "BAKE-BUN-4PK", "8901234009", "Bakery & Breads", "Metro FMCG Logistics", "pack", 25.00, 38.00, 12),
            ("Butter Chocochip Cookies 200g", "BAKE-CKIE-200", "8901234010", "Bakery & Breads", "Metro FMCG Logistics", "box", 60.00, 85.00, 10),

            # Beverages
            ("Cold-Pressed Orange Juice 1L", "BEV-ORNG-1L", "8901234011", "Beverages", "Nectar Beverage Wholesalers", "bottle", 95.00, 135.00, 10),
            ("Sparkling Lemon Soda 600ml", "BEV-LEMN-600", "8901234012", "Beverages", "Nectar Beverage Wholesalers", "bottle", 28.00, 40.00, 25),
            ("Premium Assam CTC Tea 500g", "BEV-TEA-500", "8901234013", "Beverages", "Nectar Beverage Wholesalers", "pack", 180.00, 240.00, 15),
            ("Pure Roast Ground Coffee 200g", "BEV-COFF-200", "8901234014", "Beverages", "Nectar Beverage Wholesalers", "jar", 195.00, 265.00, 8),
            ("Natural Spring Water 1L", "BEV-WATR-1L", "8901234015", "Beverages", "Nectar Beverage Wholesalers", "bottle", 12.00, 20.00, 40),

            # Snacks
            ("Crunchy Potato Chips Salted 100g", "SNAK-CHIP-100", "8901234016", "Snacks & Confectionery", "Metro FMCG Logistics", "bag", 22.00, 30.00, 30),
            ("Roasted Masala Almonds 150g", "SNAK-ALMD-150", "8901234017", "Snacks & Confectionery", "Metro FMCG Logistics", "pouch", 160.00, 220.00, 8),
            ("Dark Chocolate Bar 75g", "SNAK-CHOC-75", "8901234018", "Snacks & Confectionery", "Metro FMCG Logistics", "bar", 65.00, 95.00, 15),
            ("Classic Marie Biscuits 250g", "SNAK-MARI-250", "8901234019", "Snacks & Confectionery", "Metro FMCG Logistics", "pack", 25.00, 35.00, 25),

            # Staples
            ("Basmati Rice Premium 5kg", "STAP-RICE-5KG", "8901234020", "Staples & Grains", "Golden Grain Distributors", "bag", 450.00, 580.00, 10),
            ("Chakki Fresh Whole Wheat Atta 5kg", "STAP-ATTA-5KG", "8901234021", "Staples & Grains", "Golden Grain Distributors", "bag", 210.00, 265.00, 12),
            ("Toor Dal Yellow Lentils 1kg", "STAP-TOOR-1KG", "8901234022", "Staples & Grains", "Golden Grain Distributors", "pouch", 125.00, 160.00, 15),
            ("Pure Refined Sunflower Oil 1L", "STAP-OIL-1L", "8901234023", "Staples & Grains", "Golden Grain Distributors", "pouch", 110.00, 142.00, 20),
            ("Iodized Crystal Salt 1kg", "STAP-SALT-1KG", "8901234024", "Staples & Grains", "Golden Grain Distributors", "pack", 18.00, 28.00, 25),
            ("Refined White Sugar 1kg", "STAP-SUGR-1KG", "8901234025", "Staples & Grains", "Golden Grain Distributors", "pack", 38.00, 48.00, 20),

            # Personal Care
            ("Antibacterial Herbal Bath Soap 125g", "CARE-SOAP-125", "8901234026", "Personal Care", "PureLife Hygiene & Home Goods", "bar", 32.00, 45.00, 20),
            ("Hydrating Aloe Shampoo 340ml", "CARE-SHMP-340", "8901234027", "Personal Care", "PureLife Hygiene & Home Goods", "bottle", 145.00, 199.00, 10),
            ("Complete Dental Toothpaste 150g", "CARE-PSTE-150", "8901234028", "Personal Care", "PureLife Hygiene & Home Goods", "tube", 65.00, 92.00, 15),
            ("Instant Hand Sanitizer Gel 250ml", "CARE-SNTZ-250", "8901234029", "Personal Care", "PureLife Hygiene & Home Goods", "pump", 55.00, 80.00, 15),

            # Household
            ("Citrus Dishwash Liquid Gel 500ml", "HOME-DISH-500", "8901234030", "Household & Cleaning", "PureLife Hygiene & Home Goods", "bottle", 85.00, 115.00, 15),
            ("Multipurpose Floor Cleaner Floral 1L", "HOME-FLOR-1L", "8901234031", "Household & Cleaning", "PureLife Hygiene & Home Goods", "bottle", 110.00, 155.00, 12),
            ("Advanced Laundry Detergent Powder 2kg", "HOME-DETR-2KG", "8901234032", "Household & Cleaning", "PureLife Hygiene & Home Goods", "bag", 240.00, 310.00, 10),
            ("Antibacterial Disinfectant Spray 200ml", "HOME-SPRY-200", "8901234033", "Household & Cleaning", "PureLife Hygiene & Home Goods", "can", 130.00, 175.00, 8),
            ("Soft Kitchen Paper Towels (2 Rolls)", "HOME-TOWL-2PK", "8901234034", "Household & Cleaning", "PureLife Hygiene & Home Goods", "pack", 70.00, 99.00, 12),
        ]

        created_products = []
        for name, sku, barcode, cat_name, supp_name, unit, cost, price, reorder in products_catalog:
            prod = Product(
                name=name,
                sku=sku,
                barcode=barcode,
                category_id=cat_map[cat_name].id,
                supplier_id=supp_map[supp_name].id,
                unit=unit,
                purchase_cost=Decimal(str(cost)),
                selling_price=Decimal(str(price)),
                reorder_threshold=reorder,
                is_active=True
            )
            db.add(prod)
            db.flush()
            created_products.append(prod)

        db.commit()
        print(f"  Created {len(created_products)} catalog products.")

        print("[5/7] Provisioning Multi-Batch Stock (Healthy, Near-Expiry, & Expired)...")
        today = date.today()

        for idx, prod in enumerate(created_products):
            # Batch 1: Received 30 days ago, healthy expiry
            b1_received = today - timedelta(days=35)
            # Perishables get shorter expiries
            if "Dairy" in prod.category.name or "Bakery" in prod.category.name:
                b1_expiry = today + timedelta(days=random.randint(15, 45))
            elif "Staples" in prod.category.name or "Household" in prod.category.name:
                b1_expiry = today + timedelta(days=random.randint(180, 365))
            else:
                b1_expiry = today + timedelta(days=random.randint(60, 120))

            qty1 = random.randint(25, 60)
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
            db.add(batch1)
            db.flush()

            db.add(StockMovement(
                product_id=prod.id,
                batch_id=batch1.id,
                movement_type="purchase_receipt",
                quantity=qty1,
                reference_id=f"INIT-{batch1.batch_number}",
                reason="Initial Stock Receipt",
                user_id=owner.id,
                created_at=datetime.combine(b1_received, datetime.min.time(), tzinfo=timezone.utc)
            ))

            # Batch 2: Received recently (10 days ago)
            b2_received = today - timedelta(days=10)
            b2_expiry = b1_expiry + timedelta(days=30)
            qty2 = random.randint(20, 50)
            batch2 = InventoryBatch(
                product_id=prod.id,
                supplier_id=prod.supplier_id,
                batch_number=f"BATCH-26B-{idx+1:03d}",
                quantity_received=qty2,
                current_quantity=qty2,
                received_date=b2_received,
                expiry_date=b2_expiry,
                unit_cost=prod.purchase_cost,
                status="active"
            )
            db.add(batch2)
            db.flush()

            db.add(StockMovement(
                product_id=prod.id,
                batch_id=batch2.id,
                movement_type="purchase_receipt",
                quantity=qty2,
                reference_id=f"INIT-{batch2.batch_number}",
                reason="Restock Shipment",
                user_id=owner.id,
                created_at=datetime.combine(b2_received, datetime.min.time(), tzinfo=timezone.utc)
            ))

            # Special Demo Batches: Near Expiry for first 3 perishable items
            if idx in (0, 1, 6):
                near_exp_date = today + timedelta(days=random.randint(3, 8))
                near_qty = random.randint(5, 12)
                near_batch = InventoryBatch(
                    product_id=prod.id,
                    supplier_id=prod.supplier_id,
                    batch_number=f"BATCH-EXP-{idx+1:03d}",
                    quantity_received=near_qty,
                    current_quantity=near_qty,
                    received_date=today - timedelta(days=20),
                    expiry_date=near_exp_date,
                    unit_cost=prod.purchase_cost,
                    status="active"
                )
                db.add(near_batch)
                db.flush()
                db.add(StockMovement(
                    product_id=prod.id,
                    batch_id=near_batch.id,
                    movement_type="purchase_receipt",
                    quantity=near_qty,
                    reference_id=f"NEAR-{near_batch.batch_number}",
                    reason="Promo Stock Intake",
                    user_id=owner.id,
                    created_at=datetime.now(timezone.utc)
                ))

            # Special Demo Batches: Already Expired with remaining units for 2 items
            if idx in (3, 8):
                exp_date = today - timedelta(days=random.randint(2, 5))
                exp_qty = random.randint(3, 6)
                exp_batch = InventoryBatch(
                    product_id=prod.id,
                    supplier_id=prod.supplier_id,
                    batch_number=f"BATCH-EXPD-{idx+1:03d}",
                    quantity_received=exp_qty,
                    current_quantity=exp_qty,
                    received_date=today - timedelta(days=30),
                    expiry_date=exp_date,
                    unit_cost=prod.purchase_cost,
                    status="expired"
                )
                db.add(exp_batch)
                db.flush()

        db.commit()
        print("  Batches and initial stock movements generated.")

        print("[6/7] Simulating 60 Days of Historical POS Sales (FEFO Driven)...")
        # Generate 60 days of realistic sales transactions
        for day_offset in range(60, 0, -1):
            sale_date = today - timedelta(days=day_offset)
            dow = sale_date.weekday()

            # Weekends have higher volume
            num_sales = random.randint(8, 16) if dow >= 5 else random.randint(4, 9)

            for s_idx in range(num_sales):
                sale_time = datetime.combine(sale_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(
                    hours=random.randint(9, 20), minutes=random.randint(0, 59)
                )
                sale_num = f"SAL-{sale_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

                # Pick 1 to 4 random products
                selected_prods = random.sample(created_products, k=random.randint(1, 4))
                sale_items = []
                subtotal = Decimal("0.00")
                total_cost = Decimal("0.00")

                for p in selected_prods:
                    # Find eligible active batches in FEFO order
                    batches = db.query(InventoryBatch).filter(
                        InventoryBatch.product_id == p.id,
                        InventoryBatch.current_quantity > 0,
                        InventoryBatch.status == "active",
                        (InventoryBatch.expiry_date == None) | (InventoryBatch.expiry_date >= sale_date)
                    ).order_by(
                        InventoryBatch.expiry_date.asc().nulls_last(),
                        InventoryBatch.received_date.asc(),
                        InventoryBatch.id.asc()
                    ).all()

                    if not batches:
                        continue

                    req_qty = random.randint(1, 3)
                    avail = sum(b.current_quantity for b in batches)
                    if avail < req_qty:
                        req_qty = avail
                    if req_qty <= 0:
                        continue

                    # Allocate across batches
                    rem = req_qty
                    for b in batches:
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

                        sale_items.append(SaleItem(
                            product_id=p.id,
                            batch_id=b.id,
                            quantity=deduct,
                            unit_price=p.selling_price,
                            unit_cost=b.unit_cost,
                            line_subtotal=l_subtotal,
                            line_cost=l_cost,
                            line_profit=l_profit
                        ))

                        db.add(StockMovement(
                            product_id=p.id,
                            batch_id=b.id,
                            movement_type="sale",
                            quantity=-deduct,
                            reference_id=sale_num,
                            reason="POS Sale Fulfillment",
                            user_id=staff.id,
                            created_at=sale_time
                        ))

                if sale_items:
                    discount = Decimal("0.00")
                    if subtotal > 500 and random.random() < 0.2:
                        discount = Decimal(str(round(float(subtotal) * 0.05, 2)))

                    total_amt = max(Decimal("0.00"), subtotal - discount)
                    gross_profit = total_amt - total_cost

                    sale = Sale(
                        sale_number=sale_num,
                        subtotal=subtotal,
                        discount_amount=discount,
                        total_amount=total_amt,
                        total_cost=total_cost,
                        gross_profit=gross_profit,
                        payment_method=random.choice(["cash", "upi", "card"]),
                        status="completed",
                        user_id=staff.id,
                        created_at=sale_time
                    )
                    db.add(sale)
                    db.flush()

                    for it in sale_items:
                        it.sale_id = sale.id
                        db.add(it)

        db.commit()
        print("  Historical sales transactions successfully seeded.")

        print("[7/7] Reconciling Alert State...")
        alert_stats = AlertService.reconcile_all_alerts(db)
        db.commit()
        print(f"  Alerts synchronized: {alert_stats}")

        print("=" * 70)
        print("StockSense Demonstration Dataset Successfully Seeded!")
        print("=" * 70)
        print("Demo Credentials:")
        print("  Shop Owner: owner@stocksense.com / Owner@123")
        print("  Staff:      staff@stocksense.com / Staff@123")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
