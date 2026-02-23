'use client';

import React, { useState } from 'react';
import { Menu, X, Grid3X3, Search } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === '/';

  const navLinks = [
    { name: 'Home', href: '/' },
    { name: 'About', href: isHome ? '#about' : '/#about' },
    { name: 'Services', href: isHome ? '#services' : '/#services' },
    { name: 'Contact', href: isHome ? '#contact' : '/#contact' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 w-full bg-transparent">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
              <Grid3X3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-white text-xl font-bold">Action Chiro</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) =>
              link.href.startsWith('#') ? (
                <a
                  key={link.name}
                  href={link.href}
                  className="text-white/90 hover:text-white transition-colors text-sm font-medium"
                >
                  {link.name}
                </a>
              ) : link.href.startsWith('/#') ? (
                <Link
                  key={link.name}
                  to={link.href}
                  className="text-white/90 hover:text-white transition-colors text-sm font-medium"
                >
                  {link.name}
                </Link>
              ) : (
                <Link
                  key={link.name}
                  to={link.href}
                  className="text-white/90 hover:text-white transition-colors text-sm font-medium"
                >
                  {link.name}
                </Link>
              )
            )}
          </div>

          {/* Right side: Search, X icon, Book Appointment */}
          <div className="hidden md:flex items-center gap-4">
            <button className="text-white/80 hover:text-white transition-colors">
              <Search className="w-5 h-5" />
            </button>
            <button className="text-white/80 hover:text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
            <a
              href="tel:+15162218515"
              className="bg-[#22C55E] hover:bg-green-600 text-white font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Book Appointment
            </a>
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
          <div className="md:hidden bg-black/20 backdrop-blur-md pb-4 rounded-b-xl">
            <div className="flex flex-col gap-2 px-2">
              {navLinks.map((link) =>
                link.href.startsWith('#') ? (
                  <a
                    key={link.name}
                    href={link.href}
                    onClick={() => setIsMenuOpen(false)}
                    className="text-white/90 hover:text-white transition-colors text-sm font-medium py-2 px-3 rounded-md hover:bg-white/10"
                  >
                    {link.name}
                  </a>
                ) : (
                  <Link
                    key={link.name}
                    to={link.href}
                    onClick={() => setIsMenuOpen(false)}
                    className="text-white/90 hover:text-white transition-colors text-sm font-medium py-2 px-3 rounded-md hover:bg-white/10"
                  >
                    {link.name}
                  </Link>
                )
              )}
              <a
                href="tel:+15162218515"
                className="bg-[#22C55E] hover:bg-green-600 text-white font-medium px-4 py-2 rounded-lg transition-colors mt-2 w-full text-center"
              >
                Book Appointment
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
