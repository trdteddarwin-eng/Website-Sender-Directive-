"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  Search,
  Clock,
  TrendingUp,
  Heart,
  Activity,
  Thermometer,
  Zap,
} from "lucide-react";

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

// Mission Statement Section
export function MissionSection() {
  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <p className="text-lg md:text-xl lg:text-2xl text-gray-700 leading-relaxed mb-8">
            At Docuverse, we believe that true wellness isn&apos;t about achieving
            perfection it&apos;s about embracing the everyday moments that nurture your
            body, mind, and spirit. We&apos;re dedicated to creating meaningful
            healthcare experiences through care, innovation, and human connection.
          </p>

          <motion.a
            href="#"
            className="inline-flex items-center gap-2 text-gray-800 font-semibold hover:text-green-600 transition-colors group"
            whileHover={{ x: 4 }}
          >
            Learn More
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </motion.a>
        </motion.div>
      </div>
    </section>
  );
}

// Your Journey to Better Care Section
export function JourneySection() {
  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="text-center mb-12 md:mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Your Journey to Better Care
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            We handle the details so you can move forward confidently
          </p>
        </motion.div>

        {/* Cards Grid Layout */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          {/* LEFT: Dr. Omar Karim Profile Card */}
          <motion.div
            variants={fadeInUp}
            className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 hover:shadow-xl hover:-translate-y-2 transition-all duration-300"
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center mb-4 overflow-hidden">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-2xl font-bold">
                  OK
                </div>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">
                Dr. Omar Karim
              </h3>
              <p className="text-gray-500 mb-4">Cardiologist</p>
              <button className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 hover:scale-[1.02]">
                Book Appointment
              </button>
            </div>
          </motion.div>

          {/* CENTER: Search Doctor Card */}
          <motion.div
            variants={fadeInUp}
            className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 hover:shadow-xl hover:-translate-y-2 transition-all duration-300"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">
              Search Doctor
            </h3>

            {/* Search Input */}
            <div className="relative mb-6">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search doctors..."
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>

            {/* Suggested Doctors */}
            <div className="flex items-center gap-3">
              <div className="flex -space-x-3">
                {[
                  "bg-blue-400",
                  "bg-green-400",
                  "bg-purple-400",
                  "bg-orange-400",
                ].map((color, i) => (
                  <div
                    key={i}
                    className={`w-10 h-10 rounded-full ${color} border-2 border-white flex items-center justify-center text-white text-xs font-bold`}
                  >
                    {["SK", "AN", "RJ", "ML"][i]}
                  </div>
                ))}
              </div>
              <span className="text-sm text-gray-500">50+ doctors available</span>
            </div>
          </motion.div>

          {/* RIGHT COLUMN: Emergency + AI Cards */}
          <div className="flex flex-col gap-6">
            {/* Emergency Services Card */}
            <motion.div
              variants={fadeInUp}
              className="bg-gradient-to-br from-red-50 to-orange-50 rounded-2xl shadow-lg p-6 border border-red-100 hover:shadow-xl hover:-translate-y-2 transition-all duration-300"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-red-500 flex items-center justify-center flex-shrink-0">
                  <Clock className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    Emergency Services
                  </h3>
                  <p className="text-sm text-gray-600">
                    24/7 emergency care available. Get immediate assistance for
                    urgent medical needs.
                  </p>
                  <div className="mt-3 flex items-center gap-2">
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-red-100 text-red-700 text-xs font-semibold">
                      <span className="w-2 h-2 rounded-full bg-red-500 mr-2 animate-pulse" />
                      Available Now
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* AI Overview Card */}
            <motion.div
              variants={fadeInUp}
              className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl shadow-lg p-6 border border-green-100 hover:shadow-xl hover:-translate-y-2 transition-all duration-300"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-green-500 flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    AI Overview
                  </h3>
                  <p className="text-sm text-gray-600">
                    AI-powered health insights and trend analysis for better
                    decision-making.
                  </p>
                  <div className="mt-3 flex items-center gap-2 text-green-600">
                    <Activity className="w-4 h-4" />
                    <span className="text-xs font-medium">Real-time analytics</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Floating Health Stats Row */}
        <motion.div
          className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={staggerContainer}
        >
          {[
            { icon: Heart, label: "Heart Rate", value: "120 bpm", color: "text-red-500" },
            { icon: Activity, label: "Blood Oxygen", value: "98%", color: "text-blue-500" },
            { icon: Thermometer, label: "Temperature", value: "36.5°C", color: "text-orange-500" },
            { icon: Zap, label: "Activity", value: "8,432 steps", color: "text-green-500" },
          ].map((stat, i) => (
            <motion.div
              key={i}
              variants={fadeInUp}
              className="bg-white rounded-xl p-4 shadow-md border border-gray-100 flex items-center gap-3 hover:shadow-lg transition-shadow"
            >
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
              <div>
                <p className="text-xs text-gray-500">{stat.label}</p>
                <p className="text-sm font-bold text-gray-900">{stat.value}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// Main Journey Component
export default function Journey() {
  return (
    <>
      <MissionSection />
      <JourneySection />
    </>
  );
}
