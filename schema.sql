CREATE DATABASE IF NOT EXISTS nasa_home;
USE nasa_home;

CREATE TABLE Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Student', 'Teacher') NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) UNIQUE NOT NULL,
    capacity INT NOT NULL,
    teacher_id INT NULL,
    FOREIGN KEY (teacher_id) REFERENCES Users(id) ON DELETE SET NULL
);

CREATE TABLE Room_Assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    room_id INT NOT NULL,
    assigned_date DATE NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES Rooms(id) ON DELETE CASCADE
);

CREATE TABLE Food_Items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category ENUM('Non-Veg', 'Veg') NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE Orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Order_Details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(id) ON DELETE CASCADE,
    FOREIGN KEY (food_item_id) REFERENCES Food_Items(id) ON DELETE CASCADE
);

CREATE TABLE Payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_type ENUM('Meal', 'Hall Fee', 'Penalty') NOT NULL,
    status ENUM('Pending', 'Paid') DEFAULT 'Pending',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NULL,
    room_id INT NULL,
    description TEXT NOT NULL,
    is_anonymous BOOLEAN DEFAULT FALSE,
    status ENUM('Pending', 'Reviewed') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES Rooms(id) ON DELETE CASCADE
);

CREATE TABLE Maintenance_Requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    room_id INT NOT NULL,
    issue TEXT NOT NULL,
    status ENUM('Pending', 'In Progress', 'Resolved') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES Rooms(id) ON DELETE CASCADE
);

CREATE TABLE Notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user_read_created
ON Notifications (user_id, is_read, created_at);

CREATE TABLE Notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    target_role ENUM('All', 'Admin', 'Student', 'Teacher') DEFAULT 'All',
    is_active BOOLEAN DEFAULT TRUE,
    is_pinned BOOLEAN DEFAULT FALSE,
    expires_at DATETIME NULL,
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE SET NULL
);

CREATE INDEX idx_notices_visibility
ON Notices (is_active, target_role, is_pinned, created_at);

CREATE INDEX idx_notices_expires
ON Notices (expires_at);

CREATE TABLE Reading_Room_Bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    booking_date DATE NOT NULL,
    time_slot VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE,
    UNIQUE(booking_date, time_slot, student_id)
);

CREATE TABLE Chat_Messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES Users(id) ON DELETE CASCADE
);

-- Sample Data
INSERT INTO Users (email, password, role, full_name) VALUES 
('admin@nasa.com', 'admin123', 'Admin', 'System Admin'),
('student1@nasa.com', 'student123', 'Student', 'John Doe'),
('teacher1@nasa.com', 'teacher123', 'Teacher', 'Mr. Smith');

INSERT INTO Food_Items (name, category, price) VALUES 
('Beef Curry', 'Non-Veg', 5.00),
('Chicken Tikka', 'Non-Veg', 4.00),
('Veg Biryani', 'Veg', 3.50),
('Paneer Masala', 'Veg', 4.00);

INSERT INTO Rooms (room_number, capacity, teacher_id) VALUES 
('101', 2, 3),
('102', 2, NULL);

INSERT INTO Room_Assignments (student_id, room_id, assigned_date) VALUES 
(2, 1, '2023-09-01');

CREATE TABLE IF NOT EXISTS Hall_Fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('Unpaid', 'Paid') DEFAULT 'Unpaid',
    paid_at TIMESTAMP NULL,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE
);


