'use client';

import React from 'react';
import { Grid3X3, Facebook, Twitter, Instagram, Linkedin } from 'lucide-react';

const Footer: React.FC = () => {
  const footerLinks = {
    services: {
      title: 'Services',
      links: ['Spinal Adjustments', 'Sports Rehab', 'Pain Management', 'Massage Therapy'],
    },
    about: {
      title: 'About',
      links: ['Dr. Bromberg', 'Our Approach', 'Patient Stories', 'Office Tour'],
    },
    patients: {
      title: 'For Patients',
      links: ['New Patients', 'Insurance & Billing', 'FAQ', 'Blog'],
    },
    legal: {
      title: 'Legal',
      links: ['Privacy Policy', 'Terms of Service', 'HIPAA Notice', 'Accessibility'],
    },
  };

  const socialIcons = [
    { icon: Facebook, href: '#', label: 'Facebook' },
    { icon: Twitter, href: '#', label: 'Twitter' },
    { icon: Instagram, href: '#', label: 'Instagram' },
    { icon: Linkedin, href: '#', label: 'LinkedIn' },
  ];

  return (
    <footer className="bg-[#1F2937] text-white">
      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Services */}
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {footerLinks.services.title}
            </h3>
            <ul className="space-y-2">
              {footerLinks.services.links.map((link) => (
                <li key={link}>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* About */}
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {footerLinks.about.title}
            </h3>
            <ul className="space-y-2">
              {footerLinks.about.links.map((link) => (
                <li key={link}>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Patients */}
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {footerLinks.patients.title}
            </h3>
            <ul className="space-y-2">
              {footerLinks.patients.links.map((link) => (
                <li key={link}>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {footerLinks.legal.title}
            </h3>
            <ul className="space-y-2">
              {footerLinks.legal.links.map((link) => (
                <li key={link}>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="border-t border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-emerald-500 rounded flex items-center justify-center">
                <Grid3X3 className="w-4 h-4 text-white" />
              </div>
              <span className="text-white text-lg font-bold">Action Chiropractic P.C.</span>
            </div>

            {/* Social Icons */}
            <div className="flex items-center gap-4">
              {socialIcons.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  aria-label={social.label}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>

            {/* Copyright */}
            <p className="text-gray-400 text-sm">
              &copy; {new Date().getFullYear()} Action Chiropractic P.C.. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
