"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Star, Trophy, Facebook, Twitter, Instagram, Linkedin, Building2, DollarSign, ClipboardList } from "lucide-react";

const teamMembers = [
  {
    id: 1,
    name: "Dr. Bruce C. Bromberg",
    specialty: "Chiropractor — Action Chiropractic P.C.",
    rating: 4.9,
    reviews: 215,
    image: "/dr-bromberg-hero.png",
  },
  {
    id: 2,
    name: "Sarah Mitchell, LMT",
    specialty: "Licensed Massage Therapist",
    rating: 4.8,
    reviews: 96,
    image: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop",
  },
  {
    id: 3,
    name: "Dr. James Chen, D.C.",
    specialty: "Sports Chiropractor",
    rating: 5.0,
    reviews: 128,
    image: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&h=400&fit=crop",
    featured: true,
  },
];

const features = [
  {
    id: 1,
    title: "Insurance & Billing Made Easy",
    description: "We handle the paperwork so you can focus on getting better. We accept most major insurance plans and offer flexible payment options.",
    Icon: DollarSign,
  },
  {
    id: 2,
    title: "Comprehensive Care Plans",
    description: "Every patient gets a personalized treatment plan with clear milestones, home exercises, and progress tracking from day one.",
    Icon: ClipboardList,
  },
];

const hospitalIcons = [
  "https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=50&h=50&fit=crop",
  "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=50&h=50&fit=crop",
  "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=50&h=50&fit=crop",
  "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=50&h=50&fit=crop",
];

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          className={`w-4 h-4 ${
            star <= Math.floor(rating)
              ? "fill-yellow-400 text-yellow-400"
              : star - 0.5 <= rating
              ? "fill-yellow-400/50 text-yellow-400"
              : "fill-gray-200 text-gray-200"
          }`}
        />
      ))}
      <span className="ml-2 text-sm font-medium text-gray-700">{rating}</span>
    </div>
  );
}

function SocialIcons() {
  const icons = [
    { Icon: Facebook, label: "Facebook" },
    { Icon: Twitter, label: "Twitter" },
    { Icon: Instagram, label: "Instagram" },
    { Icon: Linkedin, label: "LinkedIn" },
  ];

  return (
    <div className="flex items-center gap-2">
      {icons.map(({ Icon, label }) => (
        <motion.a
          key={label}
          href="#"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-blue-600 hover:text-white transition-colors duration-300"
          aria-label={label}
        >
          <Icon className="w-4 h-4" />
        </motion.a>
      ))}
    </div>
  );
}

function TeamCard({ doctor, index }: { doctor: typeof teamMembers[0]; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
      transition={{ duration: 0.6, delay: index * 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
      whileHover={{ y: -8 }}
      className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-shadow duration-300 border border-gray-100"
    >
      <div className="relative h-64 overflow-hidden">
        <motion.img
          src={doctor.image}
          alt={doctor.name}
          className="w-full h-full object-cover"
          whileHover={{ scale: 1.05 }}
          transition={{ duration: 0.4 }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300" />
      </div>
      <div className="p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-1">{doctor.name}</h3>
        <p className="text-emerald-600 font-medium mb-3">{doctor.specialty}</p>
        <div className="flex items-center justify-between">
          <StarRating rating={doctor.rating} />
          <span className="text-sm text-gray-500">({doctor.reviews} reviews)</span>
        </div>
        <div className="mt-4 pt-4 border-t border-gray-100">
          <SocialIcons />
        </div>
      </div>
    </motion.div>
  );
}

function AwardCard() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: -50 }}
      animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -50 }}
      transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-2xl p-8 border border-emerald-100 shadow-lg"
    >
      <div className="flex items-start gap-6">
        <motion.div
          initial={{ rotate: -10 }}
          animate={{ rotate: [0, -5, 5, 0] }}
          transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
          className="flex-shrink-0"
        >
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-400 to-green-600 flex items-center justify-center shadow-lg">
            <Trophy className="w-10 h-10 text-white" />
          </div>
        </motion.div>
        <div className="flex-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-sm font-semibold mb-3">
            <Star className="w-4 h-4 fill-emerald-600 text-emerald-600" />
            Award-Winning Chiropractor
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">Dr. Bruce C. Bromberg</h3>
          <p className="text-emerald-600 font-medium mb-3">Chiropractor — Action Chiropractic P.C.</p>
          <p className="text-gray-600 leading-relaxed">
            Dr. Bromberg leads Action Chiropractic P.C. in Westbury, NY, with precise spinal
            adjustments and a holistic approach to pain relief. Digital X-rays done on site
            for accurate diagnosis. He has helped thousands recover from back pain, neck injuries,
            and chronic conditions using drug-free, non-invasive techniques. Se habla Español.
          </p>
          <div className="mt-4 flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-3xl font-bold text-gray-900">10k+</span>
              <span className="text-sm text-gray-600">Adjustments</span>
            </div>
            <div className="w-px h-10 bg-gray-300" />
            <div className="flex items-center gap-2">
              <span className="text-3xl font-bold text-gray-900">30+</span>
              <span className="text-sm text-gray-600">Years</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function FeatureCard({ feature, index }: { feature: typeof features[0]; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{ duration: 0.5, delay: index * 0.1, ease: [0.25, 0.46, 0.45, 0.94] }}
      whileHover={{ scale: 1.02 }}
      className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm hover:shadow-lg transition-all duration-300 group cursor-pointer"
    >
      <div className="flex items-start gap-4">
        <div className="text-4xl group-hover:scale-110 transition-transform duration-300 text-emerald-500">
          <feature.Icon className="w-10 h-10" />
        </div>
        <div className="flex-1">
          <h4 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-emerald-600 transition-colors">
            {feature.title}
          </h4>
          <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
        </div>
      </div>
    </motion.div>
  );
}

function TrustBadge() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: 50 }}
      animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: 50 }}
      transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="flex items-center gap-4 bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
    >
      <div className="flex -space-x-3">
        {hospitalIcons.map((icon, index) => (
          <motion.div
            key={index}
            initial={{ scale: 0, x: -20 }}
            animate={isInView ? { scale: 1, x: 0 } : { scale: 0, x: -20 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            className="w-12 h-12 rounded-full border-2 border-white overflow-hidden shadow-md"
          >
            <img src={icon} alt={`Partner ${index + 1}`} className="w-full h-full object-cover" />
          </motion.div>
        ))}
        <motion.div
          initial={{ scale: 0 }}
          animate={isInView ? { scale: 1 } : { scale: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
          className="w-12 h-12 rounded-full bg-emerald-600 border-2 border-white flex items-center justify-center text-white font-bold text-sm shadow-md"
        >
          +99
        </motion.div>
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="text-3xl font-bold text-gray-900">5k+</span>
          <Building2 className="w-6 h-6 text-emerald-600" />
        </div>
        <p className="text-gray-600 text-sm font-medium">Happy Patients & Counting</p>
      </div>
    </motion.div>
  );
}

export default function TopDoctors() {
  const sectionRef = useRef(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-100px" });

  return (
    <section ref={sectionRef} className="py-20 md:py-32 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Section */}
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-16 items-center mb-16">
          {/* Left: Title */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
            transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <motion.span
              initial={{ opacity: 0, x: -20 }}
              animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="inline-block px-4 py-1.5 rounded-full bg-emerald-100 text-emerald-700 text-sm font-semibold mb-4"
            >
              Our Care Team
            </motion.span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight mb-4">
              Meet the Team Behind Your{" "}
              <span className="text-emerald-600">Recovery</span>
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed">
              Led by Dr. Bruce C. Bromberg at Action Chiropractic P.C. in Westbury, NY,
              our team delivers personalized, hands-on chiropractic care
              to get you back to living pain-free.
            </p>
          </motion.div>

          {/* Right: Trust Badge */}
          <div className="flex justify-start lg:justify-end">
            <TrustBadge />
          </div>
        </div>

        {/* Award Card */}
        <div className="mb-12">
          <AwardCard />
        </div>

        {/* Team Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {teamMembers.map((doctor, index) => (
            <TeamCard key={doctor.id} doctor={doctor} index={index} />
          ))}
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {features.map((feature, index) => (
            <FeatureCard key={feature.id} feature={feature} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}
