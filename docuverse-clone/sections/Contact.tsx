'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Star, MapPin, Clock, ChevronLeft, ChevronRight } from 'lucide-react';

interface Testimonial {
  id: number;
  quote: string;
  rating: number;
  name: string;
  title: string;
  avatar: string;
}

const testimonials: Testimonial[] = [
  {
    id: 1,
    quote: "DocuVerse completely transformed how I manage my healthcare. Finding specialists and booking appointments has never been easier. The AI assistant helped me understand my symptoms before my visit.",
    rating: 5,
    name: "Sarah Mitchell",
    title: "Patient, New York",
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face",
  },
  {
    id: 2,
    quote: "As a busy professional, I appreciate how DocuVerse saves me time. The app interface is intuitive, and I've never had issues with appointment scheduling or accessing my health records.",
    rating: 5,
    name: "Michael Chen",
    title: "Business Executive",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face",
  },
  {
    id: 3,
    quote: "The doctors in the DocuVerse network are top-notch. I found a cardiologist within days, and the consultation was thorough and professional. Highly recommend this platform!",
    rating: 4,
    name: "Emily Rodriguez",
    title: "Healthcare Professional",
    avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face",
  },
  {
    id: 4,
    quote: "Emergency care coordination through DocuVerse was seamless. When my mother needed urgent care, the platform connected us with specialists who provided immediate attention.",
    rating: 5,
    name: "David Thompson",
 title: "Family Caregiver",
    avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face",
  },
  {
    id: 5,
    quote: "I've been using DocuVerse for my family's healthcare needs for over a year. The convenience of having all our medical records in one place is invaluable.",
    rating: 5,
    name: "Jennifer Park",
    title: "Mother of Three",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=face",
  },
  {
    id: 6,
    quote: "The AI health overview feature gave me insights I wouldn't have gotten otherwise. It helped me prepare better questions for my doctor appointment.",
    rating: 4,
    name: "Robert Williams",
    title: "Tech Enthusiast",
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&crop=face",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const cardVariants = {
  hidden: { 
    opacity: 0, 
    y: 30 
  },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.4, 0, 0.2, 1],
    },
  },
};

const titleVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.4, 0, 0.2, 1],
    },
  },
};

function TestimonialCard({ testimonial }: { testimonial: Testimonial }) {
  return (
    <motion.div
      variants={cardVariants}
      whileHover={{ 
        y: -8, 
        boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.1)',
        transition: { duration: 0.3 }
      }}
      className="bg-white rounded-2xl p-6 shadow-md border border-gray-100 flex flex-col h-full"
      style={{ boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)' }}
    >
      {/* Star Rating */}
      <div className="flex gap-1 mb-4">
        {Array.from({ length: 5 }).map((_, index) => (
          <Star
            key={index}
            className={`w-5 h-5 ${
              index < testimonial.rating
                ? 'text-amber-400 fill-amber-400'
                : 'text-gray-200'
            }`}
          />
        ))}
      </div>

      {/* Quote */}
      <p className="text-gray-600 text-sm leading-relaxed mb-6 flex-grow">
        "{testimonial.quote}"
      </p>

      {/* User Info */}
      <div className="flex items-center gap-3 mt-auto">
        <img
          src={testimonial.avatar}
          alt={testimonial.name}
          className="w-12 h-12 rounded-full object-cover"
        />
        <div>
          <p className="font-semibold text-gray-900">{testimonial.name}</p>
          <p className="text-sm text-gray-500">{testimonial.title}</p>
        </div>
      </div>
    </motion.div>
  );
}

function TestimonialsSection() {
  const [currentPage, setCurrentPage] = useState(0);
  const testimonialsPerPage = 3;
  const totalPages = Math.ceil(testimonials.length / testimonialsPerPage);

  const currentTestimonials = testimonials.slice(
    currentPage * testimonialsPerPage,
    (currentPage + 1) * testimonialsPerPage
  );

  const nextPage = () => {
    setCurrentPage((prev) => (prev + 1) % totalPages);
  };

  const prevPage = () => {
    setCurrentPage((prev) => (prev - 1 + totalPages) % totalPages);
  };

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 xl:px-12 bg-white">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={titleVariants}
          className="text-center mb-12"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            What Our Patients Say
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Real stories from real patients who have transformed their healthcare experience with DocuVerse.
          </p>
        </motion.div>

        {/* Testimonials Grid */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          variants={containerVariants}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
        >
          {currentTestimonials.map((testimonial) => (
            <TestimonialCard key={testimonial.id} testimonial={testimonial} />
          ))}
        </motion.div>

        {/* Navigation Dots & Arrows */}
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={prevPage}
            className="p-2 rounded-full border border-gray-200 hover:bg-gray-50 transition-colors"
            aria-label="Previous testimonials"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600" />
          </button>

          <div className="flex gap-2">
            {Array.from({ length: totalPages }).map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentPage(index)}
                className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                  index === currentPage
                    ? 'bg-emerald-500 w-8'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
                aria-label={`Go to page ${index + 1}`}
              />
            ))}
          </div>

          <button
            onClick={nextPage}
            className="p-2 rounded-full border border-gray-200 hover:bg-gray-50 transition-colors"
            aria-label="Next testimonials"
          >
            <ChevronRight className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-16 text-center"
        >
          <div className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-emerald-50 to-blue-50 rounded-full border border-emerald-100">
            <div className="flex -space-x-2">
              {testimonials.slice(0, 4).map((t, i) => (
                <img
                  key={i}
                  src={t.avatar}
                  alt=""
                  className="w-10 h-10 rounded-full border-2 border-white object-cover"
                />
              ))}
              <div className="w-10 h-10 rounded-full border-2 border-white bg-emerald-500 flex items-center justify-center text-white text-xs font-bold">
                +246
              </div>
            </div>
            <span className="text-lg font-semibold text-gray-800">
              Plus 250 Medical branches all over the country!
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function ContactSection() {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    service: '',
    email: '',
    description: '',
    newsletter: false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Form submission logic would go here
    console.log('Form submitted:', formData);
  };

  const services = [
    'General Consultation',
    'Cardiology',
    'Neurology',
    'Orthopedics',
    'Gastroenterology',
    'Emergency Care',
    'Preventive Care',
    'Other',
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 xl:px-12" style={{ backgroundColor: '#F0F9FF' }}>
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={titleVariants}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-4">
            Contact Us
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Get in touch with our team. We're here to help you with any questions or concerns.
          </p>
        </motion.div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16">
          {/* Left Column - Office Info */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
            className="space-y-8"
          >
            {/* Location Card */}
            <div className="bg-white rounded-2xl p-8 shadow-md">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <MapPin className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Our Location</h3>
                  <p className="text-gray-600 text-lg">
                    Manhattan, New York 2023
                  </p>
                  <p className="text-gray-500 mt-2">
                    123 Healthcare Avenue, Suite 500<br />
                    New York, NY 10001
                  </p>
                </div>
              </div>
            </div>

            {/* Office Hours Card */}
            <div className="bg-white rounded-2xl p-8 shadow-md">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center flex-shrink-0">
                  <Clock className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Office Hours</h3>
                  <p className="text-gray-600 text-lg">
                    Monday - Friday, 11 AM - 2 PM
                  </p>
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-gray-600">
                      <span>Monday - Friday</span>
                      <span className="font-medium">11:00 AM - 2:00 PM</span>
                    </div>
                    <div className="flex justify-between text-gray-500">
                      <span>Saturday - Sunday</span>
                      <span>Closed</span>
                    </div>
                    <div className="flex justify-between text-gray-500">
                      <span>Holidays</span>
                      <span>Closed</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Map Placeholder */}
            <div className="bg-white rounded-2xl p-4 shadow-md overflow-hidden">
              <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl flex items-center justify-center">
                <div className="text-center">
                  <MapPin className="w-12 h-12 text-blue-400 mx-auto mb-2" />
                  <p className="text-gray-500 font-medium">Interactive Map</p>
                  <p className="text-gray-400 text-sm">Manhattan, New York</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Right Column - Contact Form */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
          >
            <div className="bg-white rounded-2xl p-8 shadow-lg">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">
                Send Us a Message
              </h3>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Name Row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-2">
                      First Name
                    </label>
                    <input
                      type="text"
                      id="firstName"
                      value={formData.firstName}
                      onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-2">
                      Last Name
                    </label>
                    <input
                      type="text"
                      id="lastName"
                      value={formData.lastName}
                      onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                      placeholder="Doe"
                    />
                  </div>
                </div>

                {/* Services Dropdown */}
                <div>
                  <label htmlFor="service" className="block text-sm font-medium text-gray-700 mb-2">
                    Services <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="service"
                    required
                    value={formData.service}
                    onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none bg-white"
                  >
                    <option value="" disabled>Select a service</option>
                    {services.map((service) => (
                      <option key={service} value={service}>
                        {service}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Email */}
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    id="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                    placeholder="john.doe@example.com"
                  />
                </div>

                {/* Project Description */}
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                    Project Description
                  </label>
                  <textarea
                    id="description"
                    rows={4}
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none resize-none"
                    placeholder="Tell us about your project or inquiry..."
                  />
                </div>

                {/* Newsletter Checkbox */}
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id="newsletter"
                    checked={formData.newsletter}
                    onChange={(e) => setFormData({ ...formData, newsletter: e.target.checked })}
                    className="w-5 h-5 mt-0.5 rounded border-gray-300 text-emerald-500 focus:ring-emerald-500"
                  />
                  <label htmlFor="newsletter" className="text-sm text-gray-600">
                    Sign up for news and updates. Stay informed about our latest services and health tips.
                  </label>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  className="w-full py-4 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-lg rounded-lg shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
                >
                  Submit
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export default function Contact() {
  return (
    <>
      <TestimonialsSection />
      <ContactSection />
    </>
  );
}
