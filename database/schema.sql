-- Job Tracker DB Schema
-- Run this once to set up the database

CREATE DATABASE IF NOT EXISTS job_tracker_db;
USE job_tracker_db;

CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company VARCHAR(100) NOT NULL,
    role VARCHAR(150) NOT NULL,
    job_type ENUM('Full-time', 'Internship', 'Contract', 'Part-time') DEFAULT 'Full-time',
    status ENUM('Applied', 'Interview', 'Offer', 'Rejected') DEFAULT 'Applied',
    location VARCHAR(100),
    salary VARCHAR(50),
    date_applied DATE,
    notes TEXT,
    job_link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- sample data
INSERT INTO applications (company, role, job_type, status, location, salary, date_applied, notes, job_link) VALUES
('Google', 'Software Engineer Intern', 'Internship', 'Interview', 'Bengaluru', '80000/mo', '2026-01-10', 'Referred by college senior. DSA rounds expected.', 'https://careers.google.com'),
('Flipkart', 'Backend Developer', 'Full-time', 'Applied', 'Bengaluru', '12 LPA', '2026-01-15', 'Applied via portal.', 'https://www.flipkartcareers.com'),
('Zoho', 'Python Developer', 'Full-time', 'Offer', 'Chennai', '8 LPA', '2025-12-20', 'Got offer letter. Evaluating.', ''),
('Infosys', 'Systems Engineer', 'Full-time', 'Rejected', 'Mysuru', '6 LPA', '2025-12-05', 'Rejected after aptitude test.', ''),
('Razorpay', 'Full Stack Intern', 'Internship', 'Applied', 'Remote', '50000/mo', '2026-01-20', 'Sent GitHub + portfolio link.', 'https://razorpay.com/jobs');
