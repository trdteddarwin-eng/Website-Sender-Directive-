'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Heart,
  Activity,
  Brain,
  Bone,
  Wind,
  Users,
  Droplets,
  CircleDot,
} from 'lucide-react';

interface Specialty {
  icon: React.ElementType;
  title: string;
  description: string;
}

const specialties: Specialty[] = [
  {
    icon: Heart,
    title: 'Cardiology',
    description: 'Heart and cardiovascular system specialists dedicated to your cardiac health.',
  },
  {
    icon: Activity,
    title: 'Gastroenterology',
    description: 'Digestive system experts providing comprehensive GI care and treatment.',
  },
  {
    icon: Brain,
    title: 'Neurologist',
    description: 'Brain and nervous system specialists for neurological conditions and care.',
  },
  {
    icon: Bone,
    title: 'Orthopedic Surgeon',
    description: 'Bones and joints experts specializing in musculoskeletal health.',
  },
  {
    icon: Wind,
    title: 'Pulmonologist',
    description: 'Lungs and breathing specialists focused on respiratory wellness.',
  },
  {
    icon: Users,
    title: 'Gynecologist',
    description: "Women's health specialists providing compassionate reproductive care.",
  },
  {
    icon: Droplets,
    title: 'Nephrologist',
    description: 'Kidney health experts dedicated to renal care and disease management.',
  },
  {
    icon: CircleDot,
    title: 'Urologist',
    description: 'Urinary system specialists offering comprehensive urological care.',
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

export default function Specialties() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 xl:px-12" style={{ backgroundColor: '#F0F9FF' }}>
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={titleVariants}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Locate Trusted Experts Near You
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Connect with top-rated specialists across various medical fields. Our network 
            of experienced doctors is ready to provide personalized care tailored to your needs.
          </p>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          variants={containerVariants}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {specialties.map((specialty) => {
            const Icon = specialty.icon;
            return (
              <motion.div
                key={specialty.title}
                variants={cardVariants}
                whileHover={{ 
                  y: -8, 
                  boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.15)',
                  transition: { duration: 0.3 }
                }}
                className="bg-white rounded-xl p-6 shadow-md cursor-pointer transition-colors"
                style={{ boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' }}
              >
                <div 
                  className="w-14 h-14 rounded-full flex items-center justify-center mb-4"
                  style={{ backgroundColor: '#F0F9FF' }}
                >
                  <Icon 
                    className="w-7 h-7" 
                    style={{ color: '#3B82F6' }}
                    strokeWidth={1.5}
                  />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  {specialty.title}
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {specialty.description}
                </p>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
