"use client";

import React from "react";
import {
  Award,
  Star,
  Activity,
  Zap,
  Target,
  ScanLine,
  Shield,
  Users,
} from "lucide-react";

const carouselCards = [
  {
    icon: Award,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
    title: "30+ Years",
    subtitle: "Experience",
    tagline: "Expert Chiropractic Care",
  },
  {
    icon: Star,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
    title: "4.9 Rating",
    subtitle: "500+ Reviews",
    tagline: "Trusted by Families",
  },
  {
    icon: Activity,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
    title: "Spinal",
    subtitle: "Adjustments",
    tagline: "Precision Alignment",
  },
  {
    icon: Zap,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
    title: "Pain Relief",
    subtitle: "Drug-Free",
    tagline: "Natural Solutions",
  },
  {
    icon: Target,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
    title: "Sports Rehab",
    subtitle: "Recovery",
    tagline: "Get Back in the Game",
  },
  {
    icon: ScanLine,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
    title: "On-Site",
    subtitle: "X-Rays",
    tagline: "Same-Day Results",
  },
  {
    icon: Shield,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
    title: "Licensed",
    subtitle: "& Insured",
    tagline: "Board Certified",
  },
  {
    icon: Users,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-500",
    title: "Se Habla",
    subtitle: "Español",
    tagline: "Everyone Welcome",
  },
];

export default function Hero() {
  return (
    <section
      className="relative w-full min-h-screen overflow-hidden"
      style={{
        background:
          "linear-gradient(180deg, #1a5276 0%, #2980b9 15%, #5dade2 35%, #85c1e9 55%, #aed6f1 70%, #d6eaf8 85%, #ebf5fb 95%, #ffffff 100%)",
      }}
    >
      {/* Cloud shapes */}
      <div className="absolute top-[8%] left-[5%] w-[500px] h-[200px] bg-white/25 rounded-full blur-3xl animate-cloud-drift" />
      <div className="absolute top-[15%] right-[10%] w-[400px] h-[160px] bg-white/20 rounded-full blur-3xl animate-cloud-drift" style={{ animationDelay: "-5s" }} />
      <div className="absolute top-[25%] left-[30%] w-[600px] h-[180px] bg-white/15 rounded-full blur-3xl animate-cloud-drift" style={{ animationDelay: "-10s" }} />
      <div className="absolute top-[5%] right-[25%] w-[350px] h-[140px] bg-white/20 rounded-full blur-3xl animate-cloud-drift" style={{ animationDelay: "-3s" }} />
      <div className="absolute top-[35%] left-[60%] w-[450px] h-[150px] bg-white/10 rounded-full blur-3xl animate-cloud-drift" style={{ animationDelay: "-8s" }} />

      {/* ACTION CHIRO text — behind doctor */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-[1]">
        <h1
          className="text-[80px] sm:text-[140px] md:text-[200px] lg:text-[260px] xl:text-[320px] font-black uppercase tracking-wider select-none"
          style={{
            color: "transparent",
            WebkitTextStroke: "2px rgba(255,255,255,0.6)",
          }}
        >
          ACTION CHIRO
        </h1>
      </div>

      {/* Doctor image + carousel — carousel orbits around the doctor */}
      <div className="absolute inset-0 flex items-end justify-center z-20 pointer-events-none">
        <div className="relative w-[440px] h-[340px] sm:w-[540px] sm:h-[400px] md:w-[680px] md:h-[500px] lg:w-[1000px] lg:h-[850px]">
          <img
            src="/dr-bromberg-hero.png"
            alt="Dr. Bruce C. Bromberg, Chiropractor"
            className="w-full h-full object-contain object-bottom"
          />
          {/* Bottom fade to white */}
          <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent" />

          {/* 3D Carousel — orbits around doctor's body */}
          <div className="absolute pointer-events-auto carousel-position">
            <div className="carousel-wrapper" style={{ width: 0, height: 0 }}>
              <div
                className="carousel-inner"
                style={{ "--quantity": 8 } as React.CSSProperties}
              >
                {carouselCards.map((card, i) => {
                  const Icon = card.icon;
                  return (
                    <div
                      key={i}
                      className="carousel-card"
                      style={{ "--index": i } as React.CSSProperties}
                    >
                      <div className="carousel-card-inner">
                        <div className={`w-7 h-7 sm:w-8 sm:h-8 md:w-9 md:h-9 lg:w-10 lg:h-10 rounded-xl ${card.iconBg} flex items-center justify-center`}>
                          <Icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 lg:w-5 lg:h-5 ${card.iconColor}`} />
                        </div>
                        <p className="text-xs sm:text-sm lg:text-base font-bold text-slate-800 leading-tight">
                          {card.title}
                        </p>
                        <p className="text-[10px] sm:text-xs lg:text-sm font-semibold text-slate-600 leading-tight -mt-1">
                          {card.subtitle}
                        </p>
                        <p className="text-[8px] sm:text-[9px] lg:text-[10px] text-slate-400 leading-snug">
                          {card.tagline}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tagline at bottom */}
      <div className="absolute bottom-8 left-0 right-0 z-20 text-center px-4">
        <p className="text-base md:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Expert chiropractic care in Westbury, NY — spinal adjustments,
          digital X-rays on site & pain relief. Se habla Español.
        </p>
      </div>
    </section>
  );
}
