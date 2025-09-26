import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { 
  Shield, 
  Search, 
  CheckCircle, 
  Users, 
  Globe, 
  TrendingUp,
  ArrowRight,
  Star,
  Building2,
  QrCode,
  Eye,
  Award,
  Lock
} from 'lucide-react';
import Layout from './layout/Layout';

const LandingPage = () => {
  const features = [
    {
      icon: Shield,
      title: 'Verified Trust',
      description: 'Every vendor undergoes rigorous verification including business registration, tax compliance, and identity checks.'
    },
    {
      icon: QrCode,
      title: 'Instant Verification',
      description: 'Scan QR codes to instantly verify vendor authenticity and trust scores in real-time.'
    },
    {
      icon: Globe,
      title: 'Global Network',
      description: 'Access verified vendors from 120+ countries with standardized trust protocols.'
    },
    {
      icon: TrendingUp,
      title: 'Trust Scoring',
      description: 'Dynamic trust scores based on verification completeness, compliance, and community feedback.'
    },
    {
      icon: Lock,
      title: 'Fraud Prevention',
      description: 'Advanced security measures including document verification and fraud reporting systems.'
    },
    {
      icon: Award,
      title: 'Compliance Ready',
      description: 'ISO 27001 certified platform ensuring the highest security and compliance standards.'
    }
  ];

  const stats = [
    { label: 'Verified Vendors', value: '50,000+', icon: Users },
    { label: 'Countries', value: '120+', icon: Globe },
    { label: 'Verifications', value: '1M+', icon: Shield },
    { label: 'Trust Score', value: '99.8%', icon: Star }
  ];

  const testimonials = [
    {
      name: 'Sarah Johnson',
      role: 'Procurement Manager',
      company: 'TechCorp Inc.',
      content: 'Vendor-ID has transformed how we verify suppliers. The trust scores give us confidence in our partnerships.',
      rating: 5
    },
    {
      name: 'Ahmed Hassan',
      role: 'CEO',
      company: 'Global Logistics Ltd.',
      content: 'As a verified vendor, we\'ve seen a 40% increase in business inquiries. The platform builds real trust.',
      rating: 5
    },
    {
      name: 'Maria Santos',
      role: 'Supply Chain Director',
      company: 'Retail Solutions',
      content: 'The fraud prevention features saved us from potential losses. Highly recommended for any business.',
      rating: 5
    }
  ];

  return (
    <Layout>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-emerald-50 via-teal-50 to-blue-50 py-20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="w-24 h-24 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-3xl flex items-center justify-center mx-auto mb-8">
            <Shield className="w-12 h-12 text-white" />
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Verify. Trust. <span className="text-emerald-600">Secure Trade.</span>
          </h1>
          
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-12">
            The world's leading vendor verification platform. Build trusted business relationships 
            with verified suppliers, protect against fraud, and accelerate growth with confidence.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link to="/search">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 px-8 py-4 text-lg">
                <Search className="w-5 h-5 mr-2" />
                Search Verified Vendors
              </Button>
            </Link>
            <Link to="/register">
              <Button variant="outline" size="lg" className="px-8 py-4 text-lg">
                Get Your Business Verified
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div key={index} className="text-center">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                    <Icon className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                  <div className="text-sm text-gray-600">{stat.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Why Choose Vendor-ID?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Comprehensive verification, real-time trust scoring, and global compliance 
              in one powerful platform.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow duration-300">
                  <CardContent className="p-8">
                    <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-6">
                      <Icon className="w-6 h-6 text-emerald-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-3">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 leading-relaxed">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600">
              Simple, secure, and comprehensive verification process
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-xl font-bold">
                1
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Register & Verify</h3>
              <p className="text-gray-600">
                Submit business documents, identity verification, and complete your vendor profile.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-xl font-bold">
                2
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Get Verified</h3>
              <p className="text-gray-600">
                Our team reviews your documents and assigns your unique Vendor ID and trust score.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-xl font-bold">
                3
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Start Trading</h3>
              <p className="text-gray-600">
                Display your Vendor ID badge, connect with partners, and build trusted relationships.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Trusted by Businesses Worldwide
            </h2>
            <p className="text-xl text-gray-600">
              See what our verified vendors and partners have to say
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow duration-300">
                <CardContent className="p-8">
                  <div className="flex items-center mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                    ))}
                  </div>
                  <p className="text-gray-600 mb-6 italic">
                    "{testimonial.content}"
                  </p>
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mr-4">
                      <span className="text-emerald-600 font-semibold">
                        {testimonial.name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{testimonial.name}</div>
                      <div className="text-sm text-gray-600">
                        {testimonial.role}, {testimonial.company}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-emerald-600 to-teal-600">
        <div className="max-w-4xl mx-auto px-6 text-center text-white">
          <h2 className="text-4xl font-bold mb-4">
            Ready to Build Trusted Relationships?
          </h2>
          <p className="text-xl text-emerald-100 mb-8">
            Join thousands of verified vendors and businesses already using Vendor-ID 
            to secure their supply chains and accelerate growth.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-white text-emerald-600 hover:bg-gray-100 px-8 py-4 text-lg">
                Get Verified Today
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/search">
              <Button variant="outline" size="lg" className="border-white text-white hover:bg-white hover:text-emerald-600 px-8 py-4 text-lg">
                <Search className="w-5 h-5 mr-2" />
                Explore Vendors
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
};

export default LandingPage;