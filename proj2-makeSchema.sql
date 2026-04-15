-- proj2-makeSchema.sql
-- CS 4332 - Database Systems | Spring 2026
-- Caden
--
-- Creates all tables for the grocery store database.
-- Run this before loading any data.


-- Drop everything first so we can re-run this script cleanly
DROP TABLE IF EXISTS "RestockDetail"       CASCADE;
DROP TABLE IF EXISTS "RestockOrder"        CASCADE;
DROP TABLE IF EXISTS "SaleItem"            CASCADE;
DROP TABLE IF EXISTS "CustomerTransaction" CASCADE;
DROP TABLE IF EXISTS "Inventory"           CASCADE;
DROP TABLE IF EXISTS "StoreHours"          CASCADE;
DROP TABLE IF EXISTS "Employee"            CASCADE;
DROP TABLE IF EXISTS "Product"             CASCADE;
DROP TABLE IF EXISTS "Category"            CASCADE;
DROP TABLE IF EXISTS "Supplier"            CASCADE;
DROP TABLE IF EXISTS "Customer"            CASCADE;
DROP TABLE IF EXISTS "Store"               CASCADE;


-- A physical store location. StoreNumber is the human-facing
-- number (like "Store #12"). Hours is a freeform text summary;
-- the actual day-by-day schedule lives in StoreHours.
CREATE TABLE "Store" (
    "StoreID"     SERIAL        PRIMARY KEY,
    "StoreNumber" INT           NOT NULL UNIQUE DEFAULT 0,
    "Street"      VARCHAR(100)  NOT NULL,
    "City"        VARCHAR(100)  NOT NULL,
    "State"       CHAR(2)       NOT NULL,
    "ZIP"         VARCHAR(10)   NOT NULL,
    "Hours"       VARCHAR(500)
);


-- Companies that supply products to our stores.
-- Contact is open-ended (could be a phone, email, name, etc.)
CREATE TABLE "Supplier" (
    "SupplierID" SERIAL        PRIMARY KEY,
    "Name"       VARCHAR(100)  NOT NULL,
    "Contact"    VARCHAR(500)  NOT NULL
);


-- Product categories. The predefined set is:
-- Produce, Meat, Dairy, Frozen, Bakery, Pantry, Cleaning, Beverages
-- Name is unique so we can't accidentally add duplicates.
CREATE TABLE "Category" (
    "CategoryID" SERIAL        PRIMARY KEY,
    "Name"       VARCHAR(100)  NOT NULL UNIQUE
);


-- Customers with loyalty accounts. CID is assigned externally
-- so it can match an existing membership system. Guests (no
-- account) are handled by leaving CID null on transactions.
CREATE TABLE "Customer" (
    "CID"       INT           PRIMARY KEY,
    "FirstName" VARCHAR(100)  NOT NULL,
    "LastName"  VARCHAR(100)  NOT NULL,
    "Phone"     VARCHAR(20),
    "Email"     VARCHAR(254)  UNIQUE
);


-- Each employee works at one store. Role is a freeform title
-- like "Cashier" or "Store Manager".
CREATE TABLE "Employee" (
    "EID"       INT           PRIMARY KEY,
    "FirstName" VARCHAR(100)  NOT NULL,
    "LastName"  VARCHAR(100)  NOT NULL,
    "Role"      VARCHAR(50)   NOT NULL,
    "Phone"     VARCHAR(20),
    "StoreID"   INT           NOT NULL,
    CONSTRAINT fk_employee_store
        FOREIGN KEY ("StoreID") REFERENCES "Store" ("StoreID")
);


-- Products we sell or restock. SKU is a unique identifier per
-- product. Price can't go below zero.
CREATE TABLE "Product" (
    "ProductID"  INT            PRIMARY KEY,
    "Name"       VARCHAR(100)   NOT NULL,
    "Brand"      VARCHAR(100)   NOT NULL,
    "Price"      DECIMAL(10, 2) NOT NULL CHECK ("Price" >= 0),
    "SupplierID" INT            NOT NULL,
    "CategoryID" INT            NOT NULL,
    "SKU"        VARCHAR(50)    NOT NULL UNIQUE,
    CONSTRAINT fk_product_supplier
        FOREIGN KEY ("SupplierID") REFERENCES "Supplier" ("SupplierID"),
    CONSTRAINT fk_product_category
        FOREIGN KEY ("CategoryID") REFERENCES "Category" ("CategoryID")
);


-- Day-by-day store hours. DayOfWeek goes 0 (Sunday) through
-- 6 (Saturday). One row per store per day.
CREATE TABLE "StoreHours" (
    "StoreID"    INT   NOT NULL,
    "DayOfWeek"  INT   NOT NULL CHECK ("DayOfWeek" BETWEEN 0 AND 6),
    "OpenTime"   TIME  NOT NULL,
    "CloseTime"  TIME  NOT NULL,
    CONSTRAINT pk_storehours
        PRIMARY KEY ("StoreID", "DayOfWeek"),
    CONSTRAINT fk_storehours_store
        FOREIGN KEY ("StoreID") REFERENCES "Store" ("StoreID")
);


-- How much of each product a store currently has on hand.
-- One row per (store, product) pair. Quantity can't go negative.
CREATE TABLE "Inventory" (
    "StoreID"   INT  NOT NULL,
    "ProductID" INT  NOT NULL,
    "Quantity"  INT  NOT NULL DEFAULT 0 CHECK ("Quantity" >= 0),
    CONSTRAINT pk_inventory
        PRIMARY KEY ("StoreID", "ProductID"),
    CONSTRAINT fk_inventory_store
        FOREIGN KEY ("StoreID")   REFERENCES "Store"   ("StoreID"),
    CONSTRAINT fk_inventory_product
        FOREIGN KEY ("ProductID") REFERENCES "Product" ("ProductID")
);


-- One record per checkout event. CID is nullable so we can
-- record guest transactions without a loyalty account.
CREATE TABLE "CustomerTransaction" (
    "SaleID"   INT         PRIMARY KEY,
    "StoreID"  INT         NOT NULL,
    "CID"      INT,
    "DateTime" TIMESTAMP   NOT NULL,
    CONSTRAINT fk_transaction_store
        FOREIGN KEY ("StoreID") REFERENCES "Store"    ("StoreID"),
    CONSTRAINT fk_transaction_customer
        FOREIGN KEY ("CID")     REFERENCES "Customer" ("CID")
);


-- A purchase order from a store to a supplier.
-- DeliveryDate is when the order is expected (or arrived).
CREATE TABLE "RestockOrder" (
    "OrderID"      INT   PRIMARY KEY,
    "StoreID"      INT   NOT NULL,
    "SupplierID"   INT   NOT NULL,
    "DeliveryDate" DATE  NOT NULL,
    CONSTRAINT fk_restockorder_store
        FOREIGN KEY ("StoreID")    REFERENCES "Store"    ("StoreID"),
    CONSTRAINT fk_restockorder_supplier
        FOREIGN KEY ("SupplierID") REFERENCES "Supplier" ("SupplierID")
);


-- The individual products on a sale. PriceAtTime is stored here
-- because Product.Price can change — we need to know what the
-- customer actually paid at the moment of the transaction.
CREATE TABLE "SaleItem" (
    "SaleID"      INT            NOT NULL,
    "ProductID"   INT            NOT NULL,
    "Quantity"    INT            NOT NULL CHECK ("Quantity" > 0),
    "PriceAtTime" DECIMAL(10, 2) NOT NULL CHECK ("PriceAtTime" >= 0),
    CONSTRAINT pk_saleitem
        PRIMARY KEY ("SaleID", "ProductID"),
    CONSTRAINT fk_saleitem_transaction
        FOREIGN KEY ("SaleID")    REFERENCES "CustomerTransaction" ("SaleID"),
    CONSTRAINT fk_saleitem_product
        FOREIGN KEY ("ProductID") REFERENCES "Product"             ("ProductID")
);


-- The individual products on a restock order.
-- QuantityDelivered has to be at least 1.
CREATE TABLE "RestockDetail" (
    "OrderID"           INT  NOT NULL,
    "ProductID"         INT  NOT NULL,
    "QuantityDelivered" INT  NOT NULL CHECK ("QuantityDelivered" > 0),
    CONSTRAINT pk_restockdetail
        PRIMARY KEY ("OrderID", "ProductID"),
    CONSTRAINT fk_restockdetail_order
        FOREIGN KEY ("OrderID")   REFERENCES "RestockOrder" ("OrderID"),
    CONSTRAINT fk_restockdetail_product
        FOREIGN KEY ("ProductID") REFERENCES "Product"      ("ProductID")
);