"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  TrendingUp,
  Heart,
  Activity,
  Bone,
  Zap,
  Shield,
  Star,
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

const journeyEmojis = [
  { emoji: "🦴", style: { top: "5%", left: "3%" } as React.CSSProperties, delay: "0s", duration: "6s" },
  { emoji: "🧘", style: { top: "10%", right: "5%" } as React.CSSProperties, delay: "1.2s", duration: "5.5s" },
  { emoji: "💆", style: { top: "30%", right: "2%" } as React.CSSProperties, delay: "0.6s", duration: "7s" },
  { emoji: "🏋️", style: { bottom: "15%", left: "4%" } as React.CSSProperties, delay: "1.8s", duration: "6s" },
  { emoji: "🩻", style: { top: "55%", right: "4%" } as React.CSSProperties, delay: "0.3s", duration: "5s" },
  { emoji: "🌿", style: { bottom: "25%", right: "6%" } as React.CSSProperties, delay: "2s", duration: "7s" },
  { emoji: "⚡", style: { top: "8%", left: "20%" } as React.CSSProperties, delay: "0.9s", duration: "6s" },
  { emoji: "🤸", style: { bottom: "10%", left: "15%" } as React.CSSProperties, delay: "1.5s", duration: "5.5s" },
  { emoji: "❤️", style: { top: "40%", left: "1%" } as React.CSSProperties, delay: "2.3s", duration: "6.5s" },
  { emoji: "🧬", style: { bottom: "35%", right: "10%" } as React.CSSProperties, delay: "0.7s", duration: "7s" },
];

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
            At Action Chiropractic P.C., we believe your body has an incredible ability to
            heal itself — it just needs the right alignment. Dr. Bruce C. Bromberg combines
            decades of hands-on experience with modern techniques to help you live pain-free,
            move freely, and feel your absolute best. Digital X-rays done on site for accurate
            diagnosis. Se habla Español.
          </p>

          <motion.a
            href="#"
            className="inline-flex items-center gap-2 text-gray-800 font-semibold hover:text-emerald-600 transition-colors group"
            whileHover={{ x: 4 }}
          >
            Learn More About Our Approach
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
    <section className="relative py-16 md:py-24 bg-white overflow-hidden">
      {/* Floating Emojis */}
      {journeyEmojis.map((item, i) => (
        <span
          key={i}
          className="absolute select-none pointer-events-none text-xl z-[1]"
          style={{
            ...item.style,
            opacity: 0.3,
            animation: `float-emoji ${item.duration} ease-in-out ${item.delay} infinite`,
          }}
        >
          {item.emoji}
        </span>
      ))}

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
            Your Path to Pain-Free Living
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            From your first visit to lasting relief, we guide you every step of the way
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
          {/* LEFT: Dr. Bromberg Profile Card */}
          <motion.div
            variants={fadeInUp}
            className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 hover:shadow-xl hover:-translate-y-2 transition-all duration-300"
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-24 h-24 rounded-full overflow-hidden mb-4 shadow-md">
                <img
                  src="/dr-bromberg-hero.png"
                  alt="Dr. Bruce C. Bromberg"
                  className="w-full h-full object-cover"
                />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-1">
                Dr. Bruce C. Bromberg
              </h3>
              <p className="text-gray-500 mb-4">Chiropractor — Action Chiropractic P.C.</p>
              <button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 hover:scale-[1.02]">
                Book Appointment
              </button>
            </div>
          </motion.div>

          {/* CENTER: Trust / Credentials Card */}
          <motion.div
            variants={fadeInUp}
            className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 hover:shadow-xl hover:-translate-y-2 transition-all duration-300"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">
              Why Patients Choose Us
            </h3>

            {/* Trust stats */}
            <div className="space-y-4 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                  <Star className="w-5 h-5 text-emerald-500 fill-emerald-500" />
                </div>
                <div>
                  <p className="font-semibold text-sm text-gray-800">4.9 Star Rating</p>
                  <p className="text-xs text-gray-500">Based on 200+ patient reviews</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <p className="font-semibold text-sm text-gray-800">Board Certified</p>
                  <p className="text-xs text-gray-500">Licensed & fully insured</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <Heart className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-sm text-gray-800">10,000+ Adjustments</p>
                  <p className="text-xs text-gray-500">Over 30 years of practice</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* RIGHT COLUMN: Services + Wellness */}
          <div className="flex flex-col gap-6">
            {/* Services Card */}
            <motion.div
              variants={fadeInUp}
              className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-2xl shadow-lg p-6 border border-emerald-100 hover:shadow-xl hover:-translate-y-2 transition-all duration-300"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-500 flex items-center justify-center flex-shrink-0">
                  <Bone className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    Our Services
                  </h3>
                  <p className="text-sm text-gray-600">
                    Spinal adjustments, sports rehab, posture correction,
                    massage therapy & pain management — all under one roof.
                  </p>
                  <div className="mt-3 flex items-center gap-2">
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse" />
                      Accepting New Patients
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Wellness Results Card */}
            <motion.div
              variants={fadeInUp}
              className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl shadow-lg p-6 border border-blue-100 hover:shadow-xl hover:-translate-y-2 transition-all duration-300"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    Real Results
                  </h3>
                  <p className="text-sm text-gray-600">
                    95% of patients report significant pain reduction within
                    the first 3 visits. Feel the difference fast.
                  </p>
                  <div className="mt-3 flex items-center gap-2 text-blue-600">
                    <Activity className="w-4 h-4" />
                    <span className="text-xs font-medium">Proven outcomes</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Chiropractic Benefits Row */}
        <motion.div
          className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={staggerContainer}
        >
          {[
            { icon: Bone, label: "Spinal Health", value: "Expert Care", color: "text-blue-500" },
            { icon: Activity, label: "Pain Relief", value: "Drug-Free", color: "text-emerald-500" },
            { icon: Heart, label: "Wellness", value: "Whole-Body", color: "text-emerald-500" },
            { icon: Zap, label: "Recovery", value: "Fast Results", color: "text-blue-500" },
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
