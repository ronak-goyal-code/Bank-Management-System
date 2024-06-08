CREATE DATABASE BankDB;

USE BankDB;

-- Branch Table
CREATE TABLE Branch (
    branch_id INT AUTO_INCREMENT PRIMARY KEY,
    branch_name VARCHAR(100),
    location VARCHAR(255),
    phone_number VARCHAR(15)
);

-- Customer Table
CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_password VARCHAR(20),
    customer_name VARCHAR(50),
    email VARCHAR(100),
    phone_number VARCHAR(20),
    address VARCHAR(255),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Account Table
CREATE TABLE Account (
    account_number INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    branch_id INT,
    account_type ENUM('savings', 'current'),
    balance DECIMAL(10, 2),
    status ENUM('active', 'inactive'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (branch_id) REFERENCES Branch(branch_id)
);

-- Transaction Table
CREATE TABLE Transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    account_number INT,
    transaction_type ENUM('deposit', 'withdrawal', 'transfer'),
    amount DECIMAL(10, 2),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    FOREIGN KEY (account_number) REFERENCES Account(account_number)
);

-- Loan Table
CREATE TABLE Loan (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    account_number INT,
    loan_amount DECIMAL(10, 2),
    interest_rate DECIMAL(5, 2),
    term_length INT,
    start_date DATE,
    end_date DATE,
    amount_payable DECIMAL(10,2),
    status ENUM('pending', 'active', 'closed'),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (account_number) REFERENCES Account(account_number)
);


-- Available Brnaches
INSERT INTO Branch (branch_name, location, phone_number) VALUES
('Delhi', '123 Main Street, Delhi', '+911234567890'),
('Jaipur', '456 Malaviya Street, Jaipur', '+910987654321'),
('Gurugram', '789 Cyber Street, Gurugram', '+911357924680'),
('Ajmer', '321 Jain Street, Ajmer', '+912468013579');




