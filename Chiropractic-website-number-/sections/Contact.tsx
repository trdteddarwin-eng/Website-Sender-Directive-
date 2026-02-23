'use client';

import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Clock, CalendarDays, Phone, ChevronRight } from 'lucide-react';

function getDays(startDate: Date, count: number) {
  const days: Date[] = [];
  for (let i = 0; i < count; i++) {
    const d = new Date(startDate);
    d.setDate(d.getDate() + i);
    days.push(d);
  }
  return days;
}

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const WEEKDAY_SLOTS = [
  '08:00 am', '09:00 am', '10:00 am', '11:00 am',
  '12:00 pm', '01:00 pm', '02:00 pm', '03:00 pm',
  '04:00 pm', '05:00 pm',
];

const SATURDAY_SLOTS = [
  '10:00 am', '11:00 am', '12:00 pm', '01:00 pm',
];

const reasons = [
  'Initial Consultation',
  'Spinal Adjustment',
  'Sports Rehabilitation',
  'Posture Correction',
  'Pain Management',
  'Massage Therapy',
  'X-Ray & Diagnostics',
  'Pediatric Chiropractic',
  'Follow-up Visit',
];

export default function Contact() {
  const [reason, setReason] = useState('');
  const [selectedDay, setSelectedDay] = useState(0);
  const [selectedTime, setSelectedTime] = useState('');
  const [weekOffset, setWeekOffset] = useState(0);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');

  const today = useMemo(() => new Date(), []);

  const startDate = useMemo(() => {
    const d = new Date(today);
    d.setDate(d.getDate() + weekOffset * 5);
    return d;
  }, [today, weekOffset]);

  const visibleDays = useMemo(() => getDays(startDate, 5), [startDate]);

  const selectedDate = visibleDays[selectedDay];
  const dayOfWeek = selectedDate?.getDay();
  // Sunday = closed, Saturday = short hours, else weekday
  const timeSlots = dayOfWeek === 0 ? [] : dayOfWeek === 6 ? SATURDAY_SLOTS : WEEKDAY_SLOTS;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Booking:', {
      reason,
      date: selectedDate?.toLocaleDateString(),
      time: selectedTime,
      firstName,
      lastName,
      email,
    });
  };

  return (
    <section id="contact" className="py-20 px-4 sm:px-6 lg:px-8 xl:px-12 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left Column — Copy */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className="text-emerald-600 font-semibold text-sm tracking-widest uppercase">
              Book Online
            </span>
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mt-3 leading-tight">
              Schedule Your Visit in{' '}
              <span className="text-emerald-500">60 Seconds</span>
            </h2>
            <p className="text-gray-600 text-lg mt-6 leading-relaxed max-w-lg">
              Skip the phone tag. Pick a time that works for you and we'll confirm
              your appointment instantly. New patients welcome.
            </p>

            <div className="mt-10 space-y-5">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                  <Clock className="w-5 h-5 text-emerald-600" />
                </div>
                <span className="text-gray-700">Same-day appointments often available</span>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                  <CalendarDays className="w-5 h-5 text-emerald-600" />
                </div>
                <span className="text-gray-700">Easy online rescheduling & cancellation</span>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                  <Phone className="w-5 h-5 text-emerald-600" />
                </div>
                <span className="text-gray-700">
                  Prefer to call?{' '}
                  <a href="tel:5162807470" className="text-emerald-600 font-semibold hover:underline">
                    (516) 280-7470
                  </a>
                </span>
              </div>
            </div>
          </motion.div>

          {/* Right Column — Booking Form */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <form
              onSubmit={handleSubmit}
              className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8"
            >
              <h3 className="text-2xl font-bold text-gray-900 mb-6">
                Book an Appointment
              </h3>

              {/* Reason */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  What brings you in?
                </label>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none bg-white text-gray-700"
                >
                  <option value="">Select a reason</option>
                  {reasons.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>

              {/* Date Picker */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-700">
                    {weekOffset === 0 ? 'Today' : visibleDays[0]?.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                  <button
                    type="button"
                    onClick={() => setWeekOffset((w) => w + 1)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
                <div className="grid grid-cols-5 gap-2">
                  {visibleDays.map((day, i) => {
                    const isSelected = selectedDay === i;
                    const isSunday = day.getDay() === 0;
                    return (
                      <button
                        key={i}
                        type="button"
                        disabled={isSunday}
                        onClick={() => { setSelectedDay(i); setSelectedTime(''); }}
                        className={`flex flex-col items-center py-3 rounded-xl text-sm font-medium transition-all ${
                          isSunday
                            ? 'text-gray-300 cursor-not-allowed'
                            : isSelected
                            ? 'bg-emerald-500 text-white shadow-md'
                            : 'bg-gray-50 text-gray-700 hover:bg-emerald-50 hover:text-emerald-700'
                        }`}
                      >
                        <span className="text-xs">{DAY_NAMES[day.getDay()]}</span>
                        <span className="text-lg font-bold">{day.getDate()}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Time Slots */}
              <div className="mb-6">
                {timeSlots.length === 0 ? (
                  <p className="text-sm text-gray-400 text-center py-4">
                    Closed on Sundays
                  </p>
                ) : (
                  <div className="grid grid-cols-4 gap-2">
                    {timeSlots.map((slot) => {
                      const isSelected = selectedTime === slot;
                      return (
                        <button
                          key={slot}
                          type="button"
                          onClick={() => setSelectedTime(slot)}
                          className={`py-2.5 rounded-lg text-sm font-medium transition-all ${
                            isSelected
                              ? 'bg-emerald-500 text-white shadow-md'
                              : 'bg-gray-50 text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 border border-gray-200'
                          }`}
                        >
                          {slot}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Name Row */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    First name
                  </label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="First name"
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Last name
                  </label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="Last name"
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                  />
                </div>
              </div>

              {/* Email */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                />
              </div>

              {/* Submit */}
              <button
                type="submit"
                className="w-full py-4 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-lg rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99]"
              >
                Book an Appointment
              </button>
              <p className="text-center text-sm text-gray-400 mt-3">
                Free consultation for new patients
              </p>
            </form>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
