-- Database and schema setup
CREATE DATABASE ekondo_db;
USE ekondo_db;

-- Table for roles
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Table for departments
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Table for users with relationships
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role_id INT,
    department_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- Table for statuses
CREATE TABLE statuses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table for expenses
CREATE TABLE expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status_id INT,
    created_by INT NOT NULL,
    department_id INT,
    management_approval_document VARCHAR(255),
    proforma_invoice_document VARCHAR(255),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (status_id) REFERENCES statuses(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- Table for cash advances
CREATE TABLE cash_advance (
    id SERIAL PRIMARY KEY,
    branch VARCHAR(255) NOT NULL,
    officer_id INT REFERENCES users(id),
    request_date DATE DEFAULT CURRENT_DATE,
    approval_date DATE,
    amount NUMERIC(10, 2) NOT NULL,
    purpose TEXT,
    status VARCHAR(50) DEFAULT 'Pending',
    management_approval_doc BYTEA,
    proforma_invoice BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Table for OPEX/CAPEX/RETIREMENT
CREATE TABLE opex_capex_retirement (
    id INT PRIMARY KEY AUTO_INCREMENT,
    branch VARCHAR(50) NOT NULL,
    department VARCHAR(50),
    payee_name VARCHAR(100) NOT NULL,
    payee_account_number VARCHAR(20) NOT NULL,
    invoice_amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    cash_advance DECIMAL(10, 2) DEFAULT 0,
    refund_reimbursement DECIMAL(10, 2) DEFAULT 0,
    less_what DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) NOT NULL,
    receipt_filename VARCHAR(255),
    officer_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Table for petty cash advances
CREATE TABLE petty_cash_advance (
    id SERIAL PRIMARY KEY,
    branch VARCHAR(255) NOT NULL,
    officer_id INT REFERENCES users(id),
    request_date DATE DEFAULT CURRENT_DATE,
    amount NUMERIC(10, 2) NOT NULL,
    purpose TEXT,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Table for petty cash retirements
CREATE TABLE petty_cash_retirement (
    id SERIAL PRIMARY KEY,
    branch VARCHAR(255) NOT NULL,
    officer_id INT REFERENCES users(id),
    retirement_date DATE DEFAULT CURRENT_DATE,
    retired_amount NUMERIC(10, 2) NOT NULL,
    details TEXT,
    receipt BYTEA,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Table for stationary requests
CREATE TABLE stationary_request (
    id SERIAL PRIMARY KEY,
    branch VARCHAR(255) NOT NULL,
    officer_id INT REFERENCES users(id),
    request_date DATE DEFAULT CURRENT_DATE,
    item_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    justification TEXT,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Table for audit logs
CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    previous_value TEXT,
    new_value TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table for document uploads
CREATE TABLE document_uploads (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table for notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);



-- Transaction management table
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    request_type VARCHAR(50) NOT NULL,
    request_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Pending'
);

-- History/versioning table for request updates
CREATE TABLE request_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    request_id INT NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    changed_by INT NOT NULL,
    change_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    previous_value JSON,
    new_value JSON,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Notification settings table
CREATE TABLE notification_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- File metadata table for document uploads
CREATE TABLE file_metadata (
    id INT PRIMARY KEY AUTO_INCREMENT,
    upload_id INT NOT NULL,
    file_type VARCHAR(50),
    file_size INT,
    FOREIGN KEY (upload_id) REFERENCES document_uploads(id) ON DELETE CASCADE
);

-- Expense approval workflow table
CREATE TABLE expense_approval_workflow (
    id INT PRIMARY KEY AUTO_INCREMENT,
    expense_id INT NOT NULL,
    approver_id INT NOT NULL,
    approval_status VARCHAR(50) DEFAULT 'Pending',
    approval_date TIMESTAMP,
    FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Insert default roles
INSERT INTO roles (name) VALUES
    ('Officer'),
    ('Supervisor'),
    ('Reviewer'),
    ('Approver'),
    ('Admin'),
    ('Super Admin');
