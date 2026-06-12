-- Import this file in phpMyAdmin: select u916710688_instacare → Import → Choose file
-- Demo logins after import: patient@example.com / password123 (same for doctors & admin)

-- schema
CREATE TABLE IF NOT EXISTS cities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  slug VARCHAR(100) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS specialties (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  slug VARCHAR(100) NOT NULL UNIQUE,
  icon VARCHAR(50) DEFAULT 'stethoscope',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  role ENUM('patient', 'doctor', 'admin') DEFAULT 'patient',
  city_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS hospitals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  slug VARCHAR(200) NOT NULL UNIQUE,
  description TEXT,
  address TEXT,
  city_id INT NOT NULL,
  phone VARCHAR(20),
  image_url VARCHAR(500),
  rating DECIMAL(2,1) DEFAULT 0,
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS doctors (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  specialty_id INT NOT NULL,
  hospital_id INT,
  qualification VARCHAR(255),
  experience_years INT DEFAULT 0,
  consultation_fee DECIMAL(10,2) DEFAULT 0,
  online_consultation BOOLEAN DEFAULT TRUE,
  in_clinic BOOLEAN DEFAULT TRUE,
  bio TEXT,
  image_url VARCHAR(500),
  rating DECIMAL(2,1) DEFAULT 0,
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (specialty_id) REFERENCES specialties(id) ON DELETE CASCADE,
  FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS labs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  slug VARCHAR(200) NOT NULL UNIQUE,
  description TEXT,
  city_id INT NOT NULL,
  phone VARCHAR(20),
  image_url VARCHAR(500),
  discount_percent INT DEFAULT 0,
  rating DECIMAL(2,1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lab_tests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  lab_id INT NOT NULL,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  discounted_price DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (lab_id) REFERENCES labs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  method ENUM('jazzcash', 'easypaisa') NOT NULL,
  reference_type ENUM('appointment', 'order') NOT NULL,
  reference_id INT NOT NULL,
  transaction_id VARCHAR(100),
  phone VARCHAR(20) NOT NULL,
  status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS appointments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT NOT NULL,
  doctor_id INT NOT NULL,
  appointment_date DATE NOT NULL,
  appointment_time TIME NOT NULL,
  type ENUM('in_clinic', 'online') DEFAULT 'in_clinic',
  status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
  payment_status ENUM('unpaid', 'paid', 'refunded') DEFAULT 'unpaid',
  room_id VARCHAR(100) UNIQUE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS deals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  discount_percent INT DEFAULT 0,
  image_url VARCHAR(500),
  lab_id INT,
  is_active BOOLEAN DEFAULT TRUE,
  expires_at DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (lab_id) REFERENCES labs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS blog_posts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  excerpt TEXT,
  content TEXT,
  image_url VARCHAR(500),
  author VARCHAR(150),
  published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  doctor_id INT NOT NULL,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_doctor_review (user_id, doctor_id)
);

CREATE TABLE IF NOT EXISTS medicine_categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  slug VARCHAR(100) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medicines (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  slug VARCHAR(200) NOT NULL UNIQUE,
  category_id INT NOT NULL,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  discounted_price DECIMAL(10,2),
  requires_prescription BOOLEAN DEFAULT FALSE,
  stock INT DEFAULT 100,
  image_url VARCHAR(500),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES medicine_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status ENUM('pending', 'confirmed', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
  payment_status ENUM('unpaid', 'paid', 'refunded') DEFAULT 'unpaid',
  shipping_address TEXT,
  phone VARCHAR(20),
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  medicine_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  price DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

-- seed data
INSERT INTO cities (name, slug) VALUES
('Lahore', 'lahore'),
('Karachi', 'karachi'),
('Islamabad', 'islamabad'),
('Rawalpindi', 'rawalpindi'),
('Faisalabad', 'faisalabad'),
('Multan', 'multan');

INSERT INTO specialties (name, slug, icon) VALUES
('Gynecologist', 'gynecologist', 'baby'),
('Dentist', 'dentist', 'tooth'),
('Dermatologist', 'dermatologist', 'skin'),
('Cardiologist', 'cardiologist', 'heart'),
('Neurologist', 'neurologist', 'brain'),
('ENT Specialist', 'ent-specialist', 'ear'),
('Pediatrician', 'pediatrician', 'child'),
('Gastroenterologist', 'gastroenterologist', 'stomach'),
('General Physician', 'general-physician', 'stethoscope'),
('Plastic Surgeon', 'plastic-surgeon', 'scalpel'),
('Urologist', 'urologist', 'kidney'),
('Psychiatrist', 'psychiatrist', 'mind');

INSERT INTO hospitals (name, slug, description, address, city_id, phone, rating, is_verified) VALUES
('Saleem Memorial Hospital', 'saleem-memorial-hospital', 'Leading multi-specialty hospital in Lahore', 'DHA Phase 5, Lahore', 1, '042-111-222-333', 4.5, TRUE),
('Horizon Hospital', 'horizon-hospital', 'Modern healthcare facility', 'Gulberg III, Lahore', 1, '042-111-333-444', 4.3, TRUE),
('Advanced International Hospital', 'advanced-international-hospital', 'Premium healthcare in Islamabad', 'F-8 Markaz, Islamabad', 3, '051-111-555-666', 4.6, TRUE),
('Mumtaz Hospital', 'mumtaz-hospital', 'Trusted hospital in Karachi', 'Clifton, Karachi', 2, '021-111-777-888', 4.4, TRUE),
('MIH', 'mih', 'Multi-specialty hospital serving Airline Housing Society and surrounding areas', '375 Airline Housing Society, Lahore', 1, '03114315611', 4.7, TRUE);

INSERT INTO users (name, email, password, phone, role, city_id) VALUES
('Dr. Ayesha Khan', 'ayesha.khan@example.com', '$2a$10$3UGsC4b9013ILuTQkfEhGeqzzzf7Ym1OONA6mNyhVgGTleacVWAp6', '03001234567', 'doctor', 1),
('Dr. Ahmed Ali', 'ahmed.ali@example.com', '$2a$10$3UGsC4b9013ILuTQkfEhGeqzzzf7Ym1OONA6mNyhVgGTleacVWAp6', '03009876543', 'doctor', 1),
('Dr. Sara Malik', 'sara.malik@example.com', '$2a$10$3UGsC4b9013ILuTQkfEhGeqzzzf7Ym1OONA6mNyhVgGTleacVWAp6', '03001112233', 'doctor', 3),
('Patient Demo', 'patient@example.com', '$2a$10$3UGsC4b9013ILuTQkfEhGeqzzzf7Ym1OONA6mNyhVgGTleacVWAp6', '03114315611', 'patient', 1),
('Admin User', 'admin@bestechcare.pk', '$2a$10$3UGsC4b9013ILuTQkfEhGeqzzzf7Ym1OONA6mNyhVgGTleacVWAp6', '03114315611', 'admin', 1),
('Dr. Arslan Amjad', 'arslan.amjad@example.com', '$2a$10$3UGsC4b9013ILuTQkfEhGeqzzzf7Ym1OONA6mNyhVgGTleacVWAp6', '03114315611', 'doctor', 1);

INSERT INTO doctors (user_id, specialty_id, hospital_id, qualification, experience_years, consultation_fee, online_consultation, in_clinic, bio, rating, is_verified) VALUES
(1, 1, 1, 'MBBS, FCPS (Gynecology)', 12, 2500.00, TRUE, TRUE, 'Experienced gynecologist specializing in women health.', 4.8, TRUE),
(2, 2, 2, 'BDS, MDS (Oral Surgery)', 8, 2000.00, TRUE, TRUE, 'Expert dentist with focus on cosmetic dentistry.', 4.6, TRUE),
(3, 4, 3, 'MBBS, FCPS (Cardiology)', 15, 3500.00, TRUE, TRUE, 'Senior cardiologist with extensive experience.', 4.9, TRUE),
(6, 9, 5, 'MBBS, FCPS (Medicine)', 10, 2000.00, TRUE, TRUE, 'General physician at MIH with expertise in primary care and preventive medicine.', 4.8, TRUE);

INSERT INTO labs (name, slug, description, city_id, phone, discount_percent, rating) VALUES
('Chughtai Lab', 'chughtai-lab', 'Pakistan leading diagnostic laboratory', 1, '042-111-748-748', 20, 4.7),
('Islamabad Diagnostic Centre', 'islamabad-diagnostic-centre', 'Full-service diagnostic center', 3, '051-111-000-111', 15, 4.5),
('Excel Labs', 'excel-labs', 'Trusted lab tests nationwide', 2, '021-111-222-333', 20, 4.6);

INSERT INTO lab_tests (lab_id, name, description, price, discounted_price) VALUES
(1, 'Complete Blood Count (CBC)', 'Full blood panel analysis', 1200.00, 960.00),
(1, 'Lipid Profile', 'Cholesterol and triglycerides test', 2500.00, 2000.00),
(1, 'Thyroid Profile', 'TSH, T3, T4 levels', 3000.00, 2400.00),
(2, 'HbA1c', 'Diabetes monitoring test', 1800.00, 1530.00),
(3, 'Liver Function Test', 'Comprehensive liver panel', 2200.00, 1760.00);

INSERT INTO deals (title, description, discount_percent, lab_id, is_active) VALUES
('Upto 20% Discount on Chughtai Lab Tests', 'Get discounted rates on all lab tests', 20, 1, TRUE),
('20% Off Heart Related Tests', 'Special discount on cardiac screening', 20, 1, TRUE),
('IDC Special Offer', 'Discounted diagnostic packages', 15, 2, TRUE);

INSERT INTO blog_posts (title, slug, excerpt, content, author) VALUES
('How to Choose the Right Doctor', 'how-to-choose-the-right-doctor', 'Tips for finding the best healthcare provider for your needs.', 'Finding the right doctor is crucial for your health journey. Consider specialty, experience, reviews, and location when making your choice.', 'BestechCare Team'),
('Benefits of Online Consultation', 'benefits-of-online-consultation', 'Why telemedicine is changing healthcare in Pakistan.', 'Online consultations save time, reduce travel costs, and provide access to specialists from anywhere in the country.', 'BestechCare Team'),
('Importance of Regular Health Checkups', 'importance-of-regular-health-checkups', 'Why preventive care matters for long-term wellness.', 'Regular checkups help detect health issues early and maintain overall wellness. Book your lab tests today.', 'BestechCare Team');

INSERT INTO medicine_categories (name, slug) VALUES
('Pain Killer', 'pain-killer'),
('Cold & Cough', 'cold-cough'),
('Diabetes Medicines', 'diabetes'),
('Heart Health', 'heart-health'),
('Skin Health', 'skin-health'),
('Vitamins & Supplements', 'vitamins');

INSERT INTO medicines (name, slug, category_id, description, price, discounted_price, requires_prescription, stock) VALUES
('Panadol Extra', 'panadol-extra', 1, 'Fast relief from headache and body pain', 120.00, 108.00, FALSE, 500),
('Brufen 400mg', 'brufen-400mg', 1, 'Anti-inflammatory pain relief tablets', 85.00, NULL, FALSE, 300),
('Augmentin 625mg', 'augmentin-625mg', 2, 'Antibiotic for bacterial infections', 450.00, 405.00, TRUE, 200),
('Disprin', 'disprin', 1, 'Aspirin for pain and fever relief', 45.00, NULL, FALSE, 400),
('Glucophage 500mg', 'glucophage-500mg', 3, 'Metformin for type 2 diabetes management', 320.00, 288.00, TRUE, 150),
('Aspirin Cardio', 'aspirin-cardio', 4, 'Low-dose aspirin for heart health', 180.00, NULL, TRUE, 100),
('Betnovate Cream', 'betnovate-cream', 5, 'Topical steroid for skin conditions', 250.00, 225.00, TRUE, 80),
('Centrum Multivitamin', 'centrum-multivitamin', 6, 'Daily multivitamin supplement', 2200.00, 1980.00, FALSE, 60),
('Strepsils', 'strepsils', 2, 'Sore throat lozenges', 350.00, NULL, FALSE, 250),
('Vitamin D3 5000IU', 'vitamin-d3-5000', 6, 'Bone health and immunity support', 850.00, 765.00, FALSE, 120);

INSERT INTO reviews (user_id, doctor_id, rating, comment) VALUES
(4, 1, 5, 'Dr. Ayesha is very professional and caring. Highly recommended!'),
(4, 2, 4, 'Great dentist, painless procedure. Will visit again.');
