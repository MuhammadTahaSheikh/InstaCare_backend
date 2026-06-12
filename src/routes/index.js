import { Router } from 'express';
import { authenticate, requireRole } from '../middleware/auth.js';
import * as auth from '../controllers/authController.js';
import * as doctors from '../controllers/doctorController.js';
import * as hospitals from '../controllers/hospitalController.js';
import * as labs from '../controllers/labController.js';
import * as appointments from '../controllers/appointmentController.js';
import * as misc from '../controllers/miscController.js';
import * as reviews from '../controllers/reviewController.js';
import * as medicines from '../controllers/medicineController.js';
import * as admin from '../controllers/adminController.js';
import * as payments from '../controllers/paymentController.js';
import * as consultation from '../controllers/consultationController.js';

const adminOnly = [authenticate, requireRole('admin')];

const router = Router();

// Auth
router.post('/auth/register', auth.register);
router.post('/auth/login', auth.login);
router.get('/auth/verify-email', auth.verifyEmail);
router.post('/auth/verify-email', auth.verifyEmail);
router.post('/auth/resend-verification', auth.resendVerification);
router.get('/auth/profile', authenticate, auth.getProfile);

// Doctors
router.get('/doctors', doctors.getDoctors);
router.get('/doctors/:doctorId/reviews', reviews.getDoctorReviews);
router.get('/doctors/:id', doctors.getDoctorById);

// Hospitals
router.get('/hospitals', hospitals.getHospitals);
router.get('/hospitals/:id', hospitals.getHospitalById);

// Labs
router.get('/labs', labs.getLabs);
router.get('/labs/:id', labs.getLabById);
router.get('/lab-tests', labs.getLabTests);

// Appointments
router.post('/appointments', authenticate, appointments.createAppointment);
router.get('/appointments/my', authenticate, appointments.getMyAppointments);
router.patch('/appointments/:id/cancel', authenticate, appointments.cancelAppointment);

// Payments
router.get('/payments/preview', authenticate, payments.getPreview);
router.post('/payments/initiate', authenticate, payments.initiate);
router.post('/payments/verify', authenticate, payments.verify);

// Video Consultation
router.get('/consultation/doctor/my', authenticate, consultation.getDoctorConsultations);
router.get('/consultation/:id', authenticate, consultation.getConsultationRoom);

// Reviews
router.post('/reviews', authenticate, reviews.createReview);

// Medicines
router.get('/medicine-categories', medicines.getCategories);
router.get('/medicines', medicines.getMedicines);
router.get('/medicines/:id', medicines.getMedicineById);
router.post('/orders', authenticate, medicines.createOrder);
router.get('/orders/my', authenticate, medicines.getMyOrders);

// Admin
router.get('/admin/stats', ...adminOnly, admin.getStats);
router.get('/admin/appointments', ...adminOnly, admin.getAllAppointments);
router.patch('/admin/appointments/:id/status', ...adminOnly, admin.updateAppointmentStatus);
router.get('/admin/doctors', ...adminOnly, admin.getAllDoctors);
router.patch('/admin/doctors/:id/verify', ...adminOnly, admin.verifyDoctor);
router.get('/admin/hospitals', ...adminOnly, admin.getAllHospitals);
router.patch('/admin/hospitals/:id/verify', ...adminOnly, admin.verifyHospital);
router.get('/admin/orders', ...adminOnly, admin.getAllOrders);
router.patch('/admin/orders/:id/status', ...adminOnly, admin.updateOrderStatus);
router.post('/admin/medicines', ...adminOnly, admin.createMedicine);
router.patch('/admin/medicines/:id', ...adminOnly, admin.updateMedicine);
router.delete('/admin/medicines/:id', ...adminOnly, admin.deleteMedicine);

// Misc
router.get('/specialties', misc.getSpecialties);
router.get('/cities', misc.getCities);
router.get('/deals', misc.getDeals);
router.get('/blog', misc.getBlogPosts);
router.get('/blog/:slug', misc.getBlogPostBySlug);

export default router;
