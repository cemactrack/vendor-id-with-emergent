import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Shield, 
  Mail, 
  Phone, 
  MapPin,
  Twitter,
  Facebook,
  Linkedin,
  Instagram,
  Globe,
  Award,
  Users,
  Building2,
  ExternalLink
} from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const footerSections = [
    {
      title: 'Platform',
      links: [
        { name: 'Vendor Directory', href: '/' },
        { name: 'Search Vendors', href: '/search' },
        { name: 'Verify Vendor', href: '/verify' },
        { name: 'Get Verified', href: '/register' },
        { name: 'Pricing', href: '/pricing' }
      ]
    },
    {
      title: 'For Vendors',
      links: [
        { name: 'Vendor Dashboard', href: '/dashboard' },
        { name: 'Verification Process', href: '/verification-process' },
        { name: 'Trust Score', href: '/trust-score' },
        { name: 'Document Upload', href: '/documents' },
        { name: 'API Integration', href: '/api' }
      ]
    },
    {
      title: 'Security & Trust',
      links: [
        { name: 'How It Works', href: '/how-it-works' },
        { name: 'Security Features', href: '/security' },
        { name: 'Fraud Prevention', href: '/fraud-prevention' },
        { name: 'Compliance', href: '/compliance' },
        { name: 'Trust Standards', href: '/trust-standards' }
      ]
    },
    {
      title: 'Support',
      links: [
        { name: 'Help Center', href: '/help' },
        { name: 'Contact Us', href: '/contact' },
        { name: 'Documentation', href: '/docs' },
        { name: 'Developer API', href: '/api-docs' },
        { name: 'Status', href: '/status' }
      ]
    },
    {
      title: 'Company',
      links: [
        { name: 'About Us', href: '/about' },
        { name: 'Careers', href: '/careers' },
        { name: 'Press & Media', href: '/press' },
        { name: 'Partners', href: '/partners' },
        { name: 'Blog', href: '/blog' }
      ]
    }
  ];

  const socialLinks = [
    { name: 'Twitter', href: 'https://twitter.com/vendorid', icon: Twitter },
    { name: 'Facebook', href: 'https://facebook.com/vendorid', icon: Facebook },
    { name: 'LinkedIn', href: 'https://linkedin.com/company/vendorid', icon: Linkedin },
    { name: 'Instagram', href: 'https://instagram.com/vendorid', icon: Instagram }
  ];

  const stats = [
    { label: 'Verified Vendors', value: '50,000+', icon: Users },
    { label: 'Countries Covered', value: '120+', icon: Globe },
    { label: 'Trust Verifications', value: '1M+', icon: Shield },
    { label: 'Enterprise Partners', value: '500+', icon: Building2 }
  ];

  return (
    <footer className="bg-gray-900 text-white">
      {/* Stats Section */}
      <div className="border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Trusted Worldwide</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Join the global network of verified vendors and trusted businesses building the future of secure commerce.
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div key={index} className="text-center">
                  <div className="w-12 h-12 bg-emerald-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-2xl font-bold text-emerald-400 mb-1">{stat.value}</div>
                  <div className="text-sm text-gray-400">{stat.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8">
          {/* Brand Section */}
          <div className="lg:col-span-2">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center">
                <Shield className="w-7 h-7 text-white" />
              </div>
              <div>
                <div className="text-xl font-bold">Vendor-ID</div>
                <div className="text-sm text-gray-400">Trust Ecosystem</div>
              </div>
            </div>
            
            <p className="text-gray-400 mb-6 leading-relaxed">
              The world's leading vendor verification and trust platform. Building secure, 
              transparent, and reliable business relationships across the globe.
            </p>
            
            <div className="space-y-3 mb-6">
              <div className="flex items-center text-gray-400">
                <Mail className="w-4 h-4 mr-3 text-emerald-500" />
                <a href="mailto:support@vendoreco.com" className="hover:text-white transition-colors">
                  support@vendoreco.com
                </a>
              </div>
              <div className="flex items-center text-gray-400">
                <Phone className="w-4 h-4 mr-3 text-emerald-500" />
                <span>+1 (555) 123-4567</span>
              </div>
              <div className="flex items-center text-gray-400">
                <MapPin className="w-4 h-4 mr-3 text-emerald-500" />
                <span>San Francisco, CA</span>
              </div>
            </div>

            {/* Social Links */}
            <div className="flex space-x-4">
              {socialLinks.map((social, index) => {
                const Icon = social.icon;
                return (
                  <a
                    key={index}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-emerald-600 transition-colors"
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Footer Links */}
          {footerSections.map((section, index) => (
            <div key={index}>
              <h3 className="text-lg font-semibold mb-4">{section.title}</h3>
              <ul className="space-y-2">
                {section.links.map((link, linkIndex) => (
                  <li key={linkIndex}>
                    <Link
                      to={link.href}
                      className="text-gray-400 hover:text-emerald-400 transition-colors text-sm flex items-center"
                    >
                      {link.name}
                      {link.href.startsWith('http') && (
                        <ExternalLink className="w-3 h-3 ml-1" />
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Section */}
      <div className="border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex flex-wrap items-center space-x-6">
              <p className="text-sm text-gray-400">
                © {currentYear} Vendor Verification Ecosystem. All rights reserved.
              </p>
              <div className="flex items-center space-x-1">
                <Award className="w-4 h-4 text-emerald-500" />
                <span className="text-sm text-gray-400">ISO 27001 Certified</span>
              </div>
            </div>
            
            <div className="mt-4 md:mt-0">
              <div className="flex flex-wrap items-center space-x-6">
                <Link to="/privacy" className="text-sm text-gray-400 hover:text-emerald-400 transition-colors">
                  Privacy Policy
                </Link>
                <Link to="/terms" className="text-sm text-gray-400 hover:text-emerald-400 transition-colors">
                  Terms of Service
                </Link>
                <Link to="/cookies" className="text-sm text-gray-400 hover:text-emerald-400 transition-colors">
                  Cookie Policy
                </Link>
                <Link to="/security" className="text-sm text-gray-400 hover:text-emerald-400 transition-colors">
                  Security
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;