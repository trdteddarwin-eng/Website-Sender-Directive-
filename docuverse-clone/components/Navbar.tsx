'use client';

import React, { useState } from 'react';
import { Menu, X, Leaf } from 'lucide-react';

const Navbar: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navLinks = [
    { name: 'Home', href: '#' },
    { name: 'Find Doctors', href: '#' },
    { name: 'Health Overview', href: '#' },
    { name: 'Emergency', href: '#' },
    { name: 'AI Assistant', href: '#' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 w-full bg-[#3B82F6]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <Leaf className="w-8 h-8 text-green-500" />
            <span className="text-white text-xl font-bold">DocuVerse</span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="text-white hover:text-gray-200 transition-colors text-sm font-medium"
              >
                {link.name}
              </a>
            ))}
          </div>

          {/* Book Appointment Button */}
          <div className="hidden md:block">
            <button className="bg-[#22C55E] hover:bg-green-600 text-white font-medium px-4 py-2 rounded-lg transition-colors">
              Book Appointment
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-white p-2"
            >
              {isMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden bg-[#3B82F6] pb-4">
            <div className="flex flex-col gap-2 px-2">
              {navLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.href}
                  className="text-white hover:text-gray-200 transition-colors text-sm font-medium py-2 px-3 rounded-md hover:bg-blue-600"
                >
                  {link.name}
                </a>
              ))}
              <button className="bg-[#22C55E] hover:bg-green-600 text-white font-medium px-4 py-2 rounded-lg transition-colors mt-2 w-full">
                Book Appointment
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
