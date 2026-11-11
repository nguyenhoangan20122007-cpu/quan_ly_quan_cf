CREATE DATABASE IF NOT EXISTS quan_ly_quan_ca_phe CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE quan_ly_quan_ca_phe;

CREATE TABLE IF NOT EXISTS users (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 username VARCHAR(60) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 role VARCHAR(20) NOT NULL DEFAULT 'staff'
);
CREATE TABLE IF NOT EXISTS customers (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 phone VARCHAR(20) NULL
);
CREATE TABLE IF NOT EXISTS categories (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS products (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 category_id INT NOT NULL,
 name VARCHAR(120) NOT NULL,
 price DECIMAL(12,2) NOT NULL,
 description TEXT NULL,
 FOREIGN KEY (category_id) REFERENCES categories(id)
);
CREATE TABLE IF NOT EXISTS orders (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 user_id INT NULL,
 customer_id INT NULL,
 created_at DATETIME NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'pending',
 total DECIMAL(12,2) NOT NULL DEFAULT 0,
 FOREIGN KEY (user_id) REFERENCES users(id),
 FOREIGN KEY (customer_id) REFERENCES customers(id)
);
CREATE TABLE IF NOT EXISTS order_items (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 order_id INT NOT NULL,
 product_id INT NOT NULL,
 quantity INT NOT NULL,
 unit_price DECIMAL(12,2) NOT NULL,
 sugar_percent INT NOT NULL DEFAULT 100,
 ice_level VARCHAR(20) NOT NULL DEFAULT 'normal',
 note VARCHAR(255) NULL,
 FOREIGN KEY (order_id) REFERENCES orders(id),
 FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Du lieu mau, chi chay mot lan tren database
INSERT INTO users (id, username, password_hash, role) VALUES
 (1,'admin','demo_not_real_hash_admin','admin'),
 (2,'nhanvien1','demo_not_real_hash_staff','staff');
INSERT INTO customers (id,name,phone) VALUES
 (1,'Nguyễn Văn An','0912345678'),
 (2,'Trần Thị Bình','0987654321');
INSERT INTO categories (id,name) VALUES
 (1,'Cà phê'),(2,'Trà sữa'),(3,'Trà trái cây');
INSERT INTO products (id,category_id,name,price,description) VALUES
 (1,1,'Cà phê đen',25000,'Cà phê đen truyền thống'),
 (2,1,'Cà phê sữa',30000,'Cà phê sữa đá'),
 (3,2,'Trà sữa trân châu',40000,'Trà sữa kèm trân châu'),
 (4,3,'Trà đào',35000,'Trà đào cam sả');
INSERT INTO orders (id,user_id,customer_id,created_at,status,total) VALUES
 (1,2,1,NOW(),'paid',55000),
 (2,2,2,NOW(),'pending',80000);
INSERT INTO order_items (id,order_id,product_id,quantity,unit_price,sug ar_percent,ice_level,note) VALUES
 (1,1,1,1,25000,50,'normal','Ít đường'),
 (2,1,2,1,30000,100,'normal',NULL),
 (3,2,3,2,40000,70,'less','Ít đá');

SHOW TABLES;
SELECT * FROM categories;
SELECT * FROM products;
SELECT * FROM orders;
SELECT * FROM order_items;
SELECT SUM(total) AS tong_doanh_thu FROM orders WHERE status='paid';
