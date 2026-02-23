import React from 'react';
import { Search, Calendar, Clock, Shield } from 'lucide-react';

const Features: React.FC = () => {
  const features = [
    {
      icon: Search,
      title: 'Smart Doctor Search',
      description: 'Find the best doctors based on your symptoms',
    },
    {
      icon: Calendar,
      title: 'Instant Appointments',
      description: 'Book appointments in seconds',
    },
    {
      icon: Clock,
      title: '24/7 Virtual Care',
      description: 'Connect with doctors anytime',
    },
    {
      icon: Shield,
      title: 'Digital Health Records',
      description: 'Access your medical history securely',
    },
  ];

  return (
    <section className="bg-blue-50 py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-center text-gray-900 mb-16">
          Key Features That Make Our App Stand Out
        </h2>

        {/* Three Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center mb-20">
          {/* Left Column */}
          <div className="text-center lg:text-left">
            <h3 className="text-2xl font-bold text-blue-600 mb-4">
              Wellness In Your Pocket!
            </h3>
            <p className="text-gray-600 mb-6 leading-relaxed">
              Experience healthcare like never before with our intuitive mobile app. 
              Access all features on the go and stay connected with your health journey 
              wherever you are.
            </p>
            <div className="hidden lg:flex items-center justify-start">
              <svg 
                className="w-32 h-8 text-blue-500" 
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
                  <div className="bg-blue-600 h-6 w-full flex items-center justify-between px-6 pt-2">
                    <span className="text-white text-xs">9:41</span>
                    <div className="flex gap-1">
                      <div className="w-3 h-3 bg-white rounded-full opacity-80"></div>
                      <div className="w-3 h-3 bg-white rounded-full opacity-60"></div>
                    </div>
                  </div>
                  
                  {/* App Header */}
                  <div className="bg-blue-600 px-4 pb-4">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                        <span className="text-blue-600 font-bold text-sm">D</span>
                      </div>
                      <span className="text-white font-semibold">Docu verse</span>
                    </div>
                    <h4 className="text-white text-lg font-bold">Health Updates</h4>
                  </div>

                  {/* App Content */}
                  <div className="p-4 space-y-3">
                    {/* Search Bar */}
                    <div className="bg-gray-100 rounded-full px-4 py-2 flex items-center gap-2">
                      <Search className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-400 text-sm">Search doctors...</span>
                    </div>

                    {/* Cards */}
                    <div className="bg-blue-50 rounded-xl p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Calendar className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-800">Next Appointment</p>
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
                          <p className="font-semibold text-sm text-gray-800">Health Score</p>
                          <p className="text-xs text-gray-500">Excellent - 95/100</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-purple-50 rounded-xl p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                          <Clock className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-800">Medication</p>
                          <p className="text-xs text-gray-500">2 reminders today</p>
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
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-full transition-all duration-300 hover:scale-105 hover:shadow-lg mb-6">
              Download Now
            </button>
            <p className="text-gray-600 leading-relaxed">
              Get the Docuverse app today and take control of your health. 
              Available on iOS and Android. Join millions of users who trust 
              us with their healthcare needs.
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
              <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors duration-300">
                <feature.icon className="w-7 h-7 text-blue-600 group-hover:text-white transition-colors duration-300" />
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
