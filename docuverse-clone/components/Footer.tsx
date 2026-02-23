'use client';

import React from 'react';
import { Leaf, Facebook, Twitter, Instagram, Linkedin } from 'lucide-react';

const Footer: React.FC = () => {
  const footerLinks = {
    aboutUs: {
      title: 'About Us',
      links: ['News', 'Investor Relation', 'Careers', 'Media Kit'],
    },
    resources: {
      title: 'Resources',
      links: ['Get Started', 'Learn', 'Case Studies'],
    },
    community: {
      title: 'Community',
      links: ['Discord', 'Events', 'FAQ', 'Blog'],
    },
    legal: {
      title: 'Legal',
      links: ['Brand Policy', 'Terms of Services', 'Careers', 'Media Kit'],
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
          {/* About Us */}
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {footerLinks.aboutUs.title}
            </h3>
            <ul className="space-y-2">
              {footerLinks.aboutUs.links.map((link) => (
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

          {/* Resources */}
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {footerLinks.resources.title}
            </h3>
            <ul className="space-y-2">
              {footerLinks.resources.links.map((link) => (
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

          {/* Community */}
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {footerLinks.community.title}
            </h3>
            <ul className="space-y-2">
              {footerLinks.community.links.map((link) => (
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
              <Leaf className="w-6 h-6 text-green-500" />
              <span className="text-white text-lg font-bold">DocuVerse</span>
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
              © {new Date().getFullYear()} DocuVerse. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
