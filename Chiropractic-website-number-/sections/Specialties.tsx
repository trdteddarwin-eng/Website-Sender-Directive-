'use client';

import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { services } from '../data/services';

const steps = [
  {
    number: '01',
    title: 'Consultation',
    description: "Schedule your initial visit. We'll discuss your health history, symptoms, and goals.",
  },
  {
    number: '02',
    title: 'Custom Treatment Plan',
    description: 'Dr. Bromberg creates a personalized care plan based on your examination and X-ray results.',
  },
  {
    number: '03',
    title: 'Ongoing Care',
    description: 'Regular adjustments and progress check-ins to keep you feeling your best long-term.',
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
    y: 30,
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
    <section id="services" className="py-24 px-4 sm:px-6 lg:px-8 xl:px-12 bg-white">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={titleVariants}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#22C55E]/10 text-[#22C55E] text-sm font-semibold mb-6">
            <span className="w-2 h-2 rounded-full bg-[#22C55E]" />
            Our Services
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Our{' '}
            <span className="bg-gradient-to-r from-[#22C55E] to-[#16A34A] bg-clip-text text-transparent">
              Chiropractic Services
            </span>
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Dr. Bruce C. Bromberg offers a full range of chiropractic treatments at Action
            Chiropractic P.C. — from spinal adjustments to digital X-rays, all done on site in Westbury, NY.
          </p>
        </motion.div>

        {/* Service Cards Grid */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          variants={containerVariants}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-24"
        >
          {services.map((service) => {
            const Icon = service.icon;
            return (
              <motion.div key={service.slug} variants={cardVariants}>
                <Link
                  to={`/services/${service.slug}`}
                  className="group relative bg-white rounded-2xl border border-gray-100 p-6 cursor-pointer transition-all duration-300 hover:border-[#22C55E]/30 hover:shadow-[0_20px_40px_-15px_rgba(79,70,229,0.15)] block h-full"
                >
                  <div className="w-14 h-14 rounded-2xl bg-[#22C55E]/10 flex items-center justify-center mb-5 transition-all duration-300 group-hover:bg-gradient-to-br group-hover:from-[#22C55E] group-hover:to-[#16A34A]">
                    <Icon className="w-6 h-6 text-[#22C55E] transition-colors duration-300 group-hover:text-white" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    {service.title}
                  </h3>
                  <p className="text-sm text-gray-600 leading-relaxed mb-4">
                    {service.shortDescription}
                  </p>
                  <div className="flex items-center gap-1 text-[#22C55E] text-sm font-medium opacity-0 translate-y-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0">
                    Learn More
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </motion.div>

        {/* How It Works */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={titleVariants}
        >
          <div className="rounded-3xl bg-[#F9FAFB] px-6 py-16 sm:px-12 mb-16">
            <div className="text-center mb-12">
              <h3 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
                How It Works
              </h3>
              <p className="text-gray-600 max-w-xl mx-auto">
                Getting started with Action Chiropractic is simple. Here's what to expect.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
              {steps.map((step, index) => {
                return (
                  <div key={step.number} className="text-center relative">
                    {/* Connector line */}
                    {index < steps.length - 1 && (
                      <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-[2px] bg-gradient-to-r from-[#22C55E]/30 to-[#16A34A]/30" />
                    )}
                    <div className="relative inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-[#22C55E] to-[#16A34A] text-white text-xl font-bold mb-4">
                      {step.number}
                    </div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h4>
                    <p className="text-sm text-gray-600 leading-relaxed">{step.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>

      </div>
    </section>
  );
}
