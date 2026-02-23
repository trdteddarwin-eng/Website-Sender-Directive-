"use client";

import React, { useEffect, useState } from "react";
import { Heart, Droplets, Thermometer, Zap } from "lucide-react";

interface HealthCard {
  id: number;
  icon: React.ReactNode;
  value: string;
  label: string;
  color: string;
  bgColor: string;
  position: {
    top?: string;
    bottom?: string;
    left?: string;
    right?: string;
  };
  delay: string;
}

const healthCards: HealthCard[] = [
  {
    id: 1,
    icon: <Heart className="w-5 h-5" />,
    value: "120 bpm",
    label: "Heart Rate",
    color: "text-red-500",
    bgColor: "bg-red-50",
    position: { top: "15%", left: "10%" },
    delay: "0s",
  },
  {
    id: 2,
    icon: <Droplets className="w-5 h-5" />,
    value: "98%",
    label: "Blood Oxygen",
    color: "text-blue-500",
    bgColor: "bg-blue-50",
    position: { top: "25%", right: "12%" },
    delay: "0.5s",
  },
  {
    id: 3,
    icon: <Thermometer className="w-5 h-5" />,
    value: "36.5°C",
    label: "Temperature",
    color: "text-orange-500",
    bgColor: "bg-orange-50",
    position: { bottom: "30%", left: "8%" },
    delay: "1s",
  },
  {
    id: 4,
    icon: <Zap className="w-5 h-5" />,
    value: "8,432",
    label: "Steps Today",
    color: "text-green-500",
    bgColor: "bg-green-50",
    position: { bottom: "25%", right: "10%" },
    delay: "1.5s",
  },
];

export default function Hero() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <section className="relative w-full min-h-screen overflow-hidden bg-gradient-to-br from-sky-50 via-blue-50 to-cyan-50">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-200 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-cyan-200 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-sky-100 rounded-full blur-3xl" />
      </div>

      {/* Large Background Text */}
      <div
        className={`absolute inset-0 flex items-center justify-center pointer-events-none transition-all duration-1000 ${
          isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"
        }`}
      >
        <h1 className="text-[120px] md:text-[180px] lg:text-[220px] font-black text-blue-900/5 uppercase tracking-wider select-none">
          DOCUVERSE
        </h1>
      </div>

      {/* Main Content */}
      <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8 min-h-screen flex flex-col items-center justify-center py-20">
        {/* Hero Title */}
        <div
          className={`text-center mb-8 transition-all duration-700 delay-200 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-800 mb-4">
            Your Health, <span className="text-blue-600">Simplified</span>
          </h2>
        </div>

        {/* Doctor Image with Floating Cards */}
        <div
          className={`relative w-full max-w-2xl mx-auto mb-10 transition-all duration-700 delay-400 ${
            isVisible ? "opacity-100 scale-100" : "opacity-0 scale-95"
          }`}
        >
          {/* Doctor Image Container */}
          <div className="relative mx-auto w-64 h-80 md:w-80 md:h-96">
            {/* Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-t from-blue-400/20 to-transparent rounded-3xl blur-xl" />

            {/* Doctor Image */}
            <div className="relative w-full h-full rounded-3xl overflow-hidden shadow-2xl border-4 border-white/50">
              <img
                src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=600&h=800&fit=crop&crop=face"
                alt="Professional Doctor"
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          {/* Floating Health Cards */}
          {healthCards.map((card) => (
            <div
              key={card.id}
              className="absolute animate-float"
              style={{
                ...card.position,
                animationDelay: card.delay,
                animation: `float 3s ease-in-out ${card.delay} infinite`,
              }}
            >
              <div
                className={`${card.bgColor} backdrop-blur-sm rounded-xl px-4 py-3 shadow-lg border border-white/60 flex items-center gap-3 min-w-[140px]`}
              >
                <div className={`${card.color} p-2 rounded-lg bg-white/80`}>
                  {card.icon}
                </div>
                <div>
                  <p className="text-lg font-bold text-slate-800">{card.value}</p>
                  <p className="text-xs text-slate-500">{card.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Tagline */}
        <div
          className={`text-center mb-8 max-w-xl transition-all duration-700 delay-600 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <p className="text-lg md:text-xl text-slate-600 leading-relaxed">
            Find the right specialist for your health needs. Book appointments with
            top-rated doctors in minutes, not days.
          </p>
        </div>

        {/* CTA Button */}
        <div
          className={`transition-all duration-700 delay-700 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <button className="group relative px-8 py-4 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-lg rounded-full shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 active:scale-95 overflow-hidden">
            <span className="relative z-10 flex items-center gap-2">
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              Book Appointment
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-emerald-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </button>
        </div>

        {/* Stats Row */}
        <div
          className={`mt-16 grid grid-cols-3 gap-8 md:gap-16 transition-all duration-700 delay-800 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <div className="text-center">
            <p className="text-3xl md:text-4xl font-bold text-slate-800">500+</p>
            <p className="text-sm text-slate-500 mt-1">Expert Doctors</p>
          </div>
          <div className="text-center">
            <p className="text-3xl md:text-4xl font-bold text-slate-800">50k+</p>
            <p className="text-sm text-slate-500 mt-1">Happy Patients</p>
          </div>
          <div className="text-center">
            <p className="text-3xl md:text-4xl font-bold text-slate-800">4.9</p>
            <p className="text-sm text-slate-500 mt-1">App Rating</p>
          </div>
        </div>
      </div>

    </section>
  );
}
