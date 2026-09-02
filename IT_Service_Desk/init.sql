CREATE DATABASE IF NOT EXISTS IT_S;
USE IT_S;

CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO roles (name)
VALUES
('EMPLOYEE'),
('AGENT'),
('ADMIN');

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
);

CREATE TABLE ticket_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO ticket_categories (name, description)
VALUES
('Hardware', 'Laptop, desktop and hardware problems'),
('Software', 'Application and software problems'),
('Network', 'Internet, Wi-Fi and network problems'),
('Database', 'Database-related problems'),
('Email', 'Email and mailbox problems'),
('Security', 'Security-related incidents'),
('Printer', 'Printer and printing problems'),
('Access/Login', 'Account and login problems'),
('Other', 'Other technical issues');

CREATE TABLE tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,

    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    category_id INT NOT NULL,
    created_by INT NOT NULL,

    priority ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        DEFAULT 'MEDIUM',

    severity ENUM('MINOR', 'MODERATE', 'MAJOR', 'CRITICAL')
        DEFAULT 'MODERATE',

    status ENUM(
        'OPEN',
        'ASSIGNED',
        'IN_PROGRESS',
        'RESOLVED',
        'CLOSED'
    ) DEFAULT 'OPEN',

    due_date DATETIME NULL,
    resolved_at DATETIME NULL,
    closed_at DATETIME NULL,

    is_escalated BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_ticket_category
        FOREIGN KEY (category_id)
        REFERENCES ticket_categories(id),

    CONSTRAINT fk_ticket_creator
        FOREIGN KEY (created_by)
        REFERENCES users(id)
);

CREATE TABLE ticket_assignments (
    id INT PRIMARY KEY AUTO_INCREMENT,

    ticket_id INT NOT NULL,
    agent_id INT NOT NULL,
    assigned_by INT NOT NULL,

    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    unassigned_at TIMESTAMP NULL,

    CONSTRAINT fk_assignment_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_assignment_agent
        FOREIGN KEY (agent_id)
        REFERENCES users(id),

    CONSTRAINT fk_assignment_admin
        FOREIGN KEY (assigned_by)
        REFERENCES users(id)
);

CREATE TABLE ticket_comments (
    id INT PRIMARY KEY AUTO_INCREMENT,

    ticket_id INT NOT NULL,
    user_id INT NOT NULL,

    comment TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_comment_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_comment_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
);

CREATE TABLE ticket_attachments (
    id INT PRIMARY KEY AUTO_INCREMENT,

    ticket_id INT NOT NULL,
    uploaded_by INT NOT NULL,

    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,

    file_size BIGINT NOT NULL,
    file_type VARCHAR(100),

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_attachment_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_attachment_user
        FOREIGN KEY (uploaded_by)
        REFERENCES users(id)
);

CREATE TABLE ticket_history (
    id INT PRIMARY KEY AUTO_INCREMENT,

    ticket_id INT NOT NULL,
    user_id INT NOT NULL,

    action VARCHAR(100) NOT NULL,

    old_value VARCHAR(255),
    new_value VARCHAR(255),

    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_history_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
);

CREATE TABLE sla_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,

    priority ENUM(
        'LOW',
        'MEDIUM',
        'HIGH',
        'CRITICAL'
    ) NOT NULL UNIQUE,

    response_time_minutes INT NOT NULL,
    resolution_time_minutes INT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO sla_rules (
    priority,
    response_time_minutes,
    resolution_time_minutes
)
VALUES
('CRITICAL', 30, 120),
('HIGH', 60, 240),
('MEDIUM', 120, 480),
('LOW', 240, 1440);

CREATE TABLE feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,

    ticket_id INT NOT NULL,
    user_id INT NOT NULL,

    rating INT NOT NULL,
    comment TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_feedback_rating
        CHECK (rating BETWEEN 1 AND 5),

    CONSTRAINT fk_feedback_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_feedback_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),

    CONSTRAINT uq_feedback_ticket
        UNIQUE (ticket_id)
);