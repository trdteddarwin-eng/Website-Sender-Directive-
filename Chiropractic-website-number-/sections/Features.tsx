import React from 'react';
import { Calendar, Clock, Shield, Bone } from 'lucide-react';

function MountainBg() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Nature background image */}
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: 'url(https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1920&h=800&fit=crop&q=80)',
          backgroundSize: 'cover',
          backgroundPosition: 'center bottom',
        }}
      />
      {/* Green gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-emerald-100/80 via-emerald-50/40 to-blue-50/60" />
      {/* SVG mountain silhouettes */}
      <svg className="absolute bottom-0 left-0 w-full h-48" viewBox="0 0 1440 200" preserveAspectRatio="none">
        <path
          fill="rgba(167, 243, 208, 0.4)"
          d="M0,120 C180,80 360,160 540,100 C720,40 900,140 1080,90 C1260,40 1350,100 1440,80 L1440,200 L0,200 Z"
        />
        <path
          fill="rgba(110, 231, 183, 0.3)"
          d="M0,150 C200,110 400,170 600,130 C800,90 1000,160 1200,120 C1350,90 1400,140 1440,110 L1440,200 L0,200 Z"
        />
        <path
          fill="rgba(52, 211, 153, 0.25)"
          d="M0,170 C240,140 480,190 720,155 C960,120 1100,175 1300,150 C1380,140 1420,160 1440,150 L1440,200 L0,200 Z"
        />
      </svg>
    </div>
  );
}

const Features: React.FC = () => {
  const features = [
    {
      icon: Bone,
      title: 'Personalized Treatment',
      description: 'Custom care plans built around your body and goals',
    },
    {
      icon: Calendar,
      title: 'Easy Scheduling',
      description: 'Book your adjustment online in seconds',
    },
    {
      icon: Clock,
      title: 'Flexible Hours',
      description: 'Evening and weekend appointments available',
    },
    {
      icon: Shield,
      title: 'Insurance Accepted',
      description: 'We work with most major insurance providers',
    },
  ];

  return (
    <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
      {/* Mountain/Nature Background */}
      <MountainBg />

      <div className="relative z-10 max-w-7xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-center text-gray-900 mb-16">
          What Sets Our Practice Apart
        </h2>

        {/* Three Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center mb-20">
          {/* Left Column */}
          <div className="text-center lg:text-left">
            <h3 className="text-2xl font-bold text-emerald-600 mb-4">
              Wellness Starts With Your Spine
            </h3>
            <p className="text-gray-600 mb-6 leading-relaxed">
              Experience chiropractic care designed around you at Action Chiropractic P.C.
              Dr. Bruce C. Bromberg takes the time to understand your body, with digital X-rays
              done on site, and crafts a treatment plan that delivers real results.
            </p>
            <div className="hidden lg:flex items-center justify-start">
              <svg
                className="w-32 h-8 text-emerald-500"
                viewBox="0 0 120 30"
                fill="none"
              >
                <path
                  d="M0 15 Q60 5 110 15"
                  stroke="currentColor"
                  strokeWidth="2"
                  fill="none"
                  strokeDasharray="4 2"
                />
                <polygon
                  points="110,10 120,15 110,20"
                  fill="currentColor"
                />
              </svg>
            </div>
          </div>

          {/* Center - Phone Mockup */}
          <div className="flex justify-center">
            <div className="relative">
              {/* Phone Frame */}
              <div className="w-64 h-[500px] bg-gray-900 rounded-[3rem] p-3 shadow-2xl">
                {/* Screen */}
                <div className="w-full h-full bg-white rounded-[2.5rem] overflow-hidden">
                  {/* Status Bar */}
                  <div className="bg-emerald-600 h-6 w-full flex items-center justify-between px-6 pt-2">
                    <span className="text-white text-xs">9:41</span>
                    <div className="flex gap-1">
                      <div className="w-3 h-3 bg-white rounded-full opacity-80"></div>
                      <div className="w-3 h-3 bg-white rounded-full opacity-60"></div>
                    </div>
                  </div>

                  {/* App Header */}
                  <div className="bg-emerald-600 px-4 pb-4">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                        <span className="text-emerald-600 font-bold text-sm">D</span>
                      </div>
                      <span className="text-white font-semibold">Action Chiro</span>
                    </div>
                    <h4 className="text-white text-lg font-bold">Your Appointments</h4>
                  </div>

                  {/* App Content */}
                  <div className="p-4 space-y-3">
                    {/* Cards */}
                    <div className="bg-blue-50 rounded-xl p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Calendar className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-800">Next Adjustment</p>
                          <p className="text-xs text-gray-500">Tomorrow, 10:00 AM</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-green-50 rounded-xl p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                          <Shield className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-800">Progress Score</p>
                          <p className="text-xs text-gray-500">Excellent - 92% improved</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-emerald-50 rounded-xl p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                          <Bone className="w-5 h-5 text-emerald-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-800">Home Exercises</p>
                          <p className="text-xs text-gray-500">3 stretches assigned today</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Phone Reflection */}
              <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-48 h-4 bg-gray-900/20 rounded-full blur-md"></div>
            </div>
          </div>

          {/* Right Column */}
          <div className="text-center lg:text-right">
            <button className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-8 py-4 rounded-full transition-all duration-300 hover:scale-105 hover:shadow-lg mb-6">
              Book Your First Visit
            </button>
            <p className="text-gray-600 leading-relaxed">
              New patients welcome. Call 516-280-7470 or visit us at
              179 School Street, Unit A, Westbury, NY 11590.
              Se habla Español.
            </p>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-2 cursor-pointer"
            >
              <div className="w-14 h-14 bg-emerald-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-600 transition-colors duration-300">
                <feature.icon className="w-7 h-7 text-emerald-600 group-hover:text-white transition-colors duration-300" />
              </div>
              <h4 className="text-lg font-bold text-gray-900 mb-2">
                {feature.title}
              </h4>
              <p className="text-gray-600 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
