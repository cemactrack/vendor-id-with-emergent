import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { RotateCcw, Printer, Download, Share2, Eye, EyeOff } from 'lucide-react';
import { vendorAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const ProfessionalVendorCard = ({ vendor, isFlipped, onFlip, className = '' }) => {
  const [imageError, setImageError] = useState(false);
  const [cardData, setCardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSecurityCode, setShowSecurityCode] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadCardData();
  }, [vendor.id]);

  const loadCardData = async () => {
    try {
      const data = await vendorAPI.getEnhancedCardData(vendor.id);
      setCardData(data);
    } catch (error) {
      console.error('Failed to load card data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Vendor ID Card - ${vendor.name}`,
          text: `Vendor ID: ${vendor.id}`,
          url: window.location.href
        });
      } catch (error) {
        console.log('Error sharing:', error);
      }
    } else {
      await navigator.clipboard.writeText(`Vendor: ${vendor.name}\nID: ${vendor.id}\nStatus: ${vendor.status}`);
      toast({
        title: "Copied to clipboard",
        description: "Vendor information copied to clipboard"
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center w-[400px] h-[250px] bg-gray-100 rounded-lg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
      </div>
    );
  }

  const template = cardData?.template || { colors: { primary: '#16a34a', secondary: '#0f766e', accent: '#eab308' } };
  const features = cardData?.features || {};
  const patterns = cardData?.patterns || {};

  // Professional gradient backgrounds based on template
  const getGradientBackground = () => {
    switch (vendor.template) {
      case 'premium':
        return 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)';
      case 'executive':
        return 'linear-gradient(135deg, #fefefe 0%, #f1f5f9 50%, #e2e8f0 100%)';
      default:
        return 'linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #f1f5f9 100%)';
    }
  };

  // Professional microtext pattern
  const MicrotextBorder = () => (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {/* Top Border */}
      <div className="absolute top-0 left-0 right-0 h-3 bg-green-600 flex items-center justify-center overflow-hidden">
        <div className="text-white text-xs font-bold tracking-wider whitespace-nowrap animate-marquee">
          VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID
        </div>
      </div>
      
      {/* Bottom Border */}
      <div className="absolute bottom-0 left-0 right-0 h-3 bg-green-600 flex items-center justify-center overflow-hidden">
        <div className="text-white text-xs font-bold tracking-wider whitespace-nowrap">
          QR-ID • SECURE • VERIFIED • AUTHENTIC • QR-ID • SECURE • VERIFIED • AUTHENTIC • QR-ID • SECURE • VERIFIED • AUTHENTIC • QR-ID • SECURE • VERIFIED • AUTHENTIC
        </div>
      </div>
      
      {/* Left Border */}
      <div className="absolute left-0 top-0 bottom-0 w-3 bg-green-600 flex flex-col items-center justify-center overflow-hidden">
        <div className="text-white text-xs font-bold tracking-wider transform -rotate-90 whitespace-nowrap">
          VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID
        </div>
      </div>
      
      {/* Right Border */}
      <div className="absolute right-0 top-0 bottom-0 w-3 bg-green-600 flex flex-col items-center justify-center overflow-hidden">
        <div className="text-white text-xs font-bold tracking-wider transform rotate-90 whitespace-nowrap">
          VENDOR-ID • VENDOR-ID • VENDOR-ID • VENDOR-ID
        </div>
      </div>
    </div>
  );

  // Professional geometric background pattern
  const GeometricPattern = () => (
    <div className="absolute inset-0 opacity-5 overflow-hidden pointer-events-none">
      <svg width="100%" height="100%" viewBox="0 0 400 250">
        <defs>
          <pattern id="professional-pattern" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
            {/* Diagonal lines */}
            <path d="M0,0 L60,60 M0,60 L60,0" stroke="#16a34a" strokeWidth="0.5" opacity="0.3" />
            {/* Grid lines */}
            <path d="M30,0 L30,60 M0,30 L60,30" stroke="#16a34a" strokeWidth="0.3" opacity="0.2" />
            {/* Corner dots */}
            <circle cx="0" cy="0" r="1" fill="#16a34a" opacity="0.4" />
            <circle cx="60" cy="60" r="1" fill="#16a34a" opacity="0.4" />
            <circle cx="30" cy="30" r="0.5" fill="#16a34a" opacity="0.3" />
          </pattern>
          
          {/* Radial pattern for center */}
          <radialGradient id="center-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#16a34a" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#16a34a" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#professional-pattern)" />
        <ellipse cx="200" cy="125" rx="120" ry="80" fill="url(#center-glow)" />
      </svg>
    </div>
  );

  // Professional security watermark
  const SecurityWatermark = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div className="text-8xl font-bold text-gray-100 opacity-15 transform rotate-12 select-none whitespace-nowrap tracking-wider">
        VERIFIED VENDOR-ID SECURE TRADE
      </div>
    </div>
  );

  const CardFront = () => (
    <div 
      className="relative w-[400px] h-[250px] rounded-lg overflow-hidden shadow-2xl border border-gray-200"
      style={{ 
        background: getGradientBackground(),
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.4)'
      }}
    >
      <MicrotextBorder />
      <GeometricPattern />
      <SecurityWatermark />
      
      {/* Glossy overlay effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>
      
      <div className="relative z-10 p-4 h-full">
        {/* Professional Header Logo */}
        <div className="absolute top-4 left-4">
          <div className="flex items-center space-x-2 mb-1">
            <div className="relative">
              {/* Enhanced logo with professional styling */}
              <div 
                className="w-10 h-10 rounded-md flex items-center justify-center border-2 shadow-md"
                style={{ 
                  background: `linear-gradient(145deg, ${template.colors.primary}, ${template.colors.secondary})`,
                  borderColor: template.colors.accent,
                  boxShadow: 'inset 0 2px 4px rgba(255,255,255,0.3), 0 4px 8px rgba(0,0,0,0.2)'
                }}
              >
                <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-inner">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: template.colors.secondary }}>
                    <div className="w-full h-full rounded-full bg-gradient-to-br from-white/50 to-transparent"></div>
                  </div>
                </div>
              </div>
              {/* Security seal overlay */}
              <div 
                className="absolute -top-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center shadow-md"
                style={{ backgroundColor: template.colors.accent }}
              >
                <div className="w-2 h-2 transform rotate-45" style={{ backgroundColor: template.colors.secondary }}></div>
              </div>
            </div>
            <div>
              <div className="font-bold text-sm" style={{ color: template.colors.secondary }}>Vendor-ID</div>
              <div className="text-xs text-gray-600 font-medium">Verified. Trusted. Secure Trade.</div>
            </div>
          </div>
        </div>

        {/* Professional EMV Chip - Top Right */}
        <div className="absolute top-4 right-4">
          <div 
            className="w-10 h-7 rounded border shadow-md flex items-center justify-center"
            style={{ 
              background: `linear-gradient(145deg, #fbbf24, #f59e0b)`,
              borderColor: '#d97706',
              boxShadow: 'inset 0 2px 4px rgba(255,255,255,0.4), 0 2px 8px rgba(0,0,0,0.15)'
            }}
          >
            <div className="w-8 h-5 rounded-sm border flex flex-wrap" style={{ backgroundColor: '#f59e0b', borderColor: '#d97706' }}>
              {[...Array(6)].map((_, i) => (
                <div key={i} className="w-1 h-1 m-0.5 bg-amber-800 rounded-full"></div>
              ))}
            </div>
          </div>
        </div>

        {/* Professional Vendor Photo */}
        <div className="absolute bottom-20 left-4">
          <div className="w-20 h-24 rounded-lg border-3 border-white shadow-xl overflow-hidden bg-gray-100">
            {!imageError && vendor.photo ? (
              <img 
                src={vendor.photo} 
                alt={vendor.name}
                className="w-full h-full object-cover"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center text-gray-500 text-xs font-medium">
                PHOTO
              </div>
            )}
          </div>
        </div>

        {/* QR Code - Professional styling */}
        <div className="absolute bottom-4 left-4">
          <div className="bg-white p-1 rounded border shadow-md">
            <div className="w-12 h-12 bg-white border border-gray-200 rounded flex items-center justify-center overflow-hidden">
              <img 
                src={vendorAPI.getQRCodeURL(vendor.id)} 
                alt="QR Code"
                className="w-11 h-11 object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="w-11 h-11 bg-black opacity-80 flex items-center justify-center text-white text-xs" style={{display: 'none'}}>
                QR
              </div>
            </div>
            <div className="text-xs text-center text-gray-600 font-medium mt-1">QR-ID</div>
          </div>
        </div>

        {/* Professional Barcode */}
        <div className="absolute bottom-4 right-16">
          <div className="bg-white p-1 rounded shadow-md">
            <div className="w-12 h-16 bg-white border border-gray-200 rounded flex items-center justify-center overflow-hidden">
              <img 
                src={vendorAPI.getBarcodeURL(vendor.id)} 
                alt="Barcode"
                className="w-10 h-14 object-contain transform rotate-90"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="w-10 h-14 bg-black opacity-80 flex items-center justify-center flex-col" style={{display: 'none'}}>
                {[...Array(10)].map((_, i) => (
                  <div key={i} className="w-full h-1 bg-white my-0.5"></div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Center Information Block */}
        <div className="absolute top-16 left-1/2 transform -translate-x-1/2 text-center">
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-lg border border-white/50">
            <div className="font-bold text-lg mb-2" style={{ color: template.colors.secondary }}>VENDOR ID CARD</div>
            <div className="text-black font-bold text-xl mb-2">{vendor.name}</div>
            <div className="font-bold text-base mb-2" style={{ color: template.colors.secondary }}>{vendor.id}</div>
            <div className="text-gray-700 text-sm mb-1">ISSUE DATE: {vendor.issueDate}</div>
            {vendor.expiryDate && (
              <div className="text-gray-700 text-sm">EXPIRES: {vendor.expiryDate}</div>
            )}
            {vendor.company && (
              <div className="text-gray-600 text-sm mt-2 font-medium">{vendor.company}</div>
            )}
            {vendor.position && (
              <div className="text-gray-600 text-sm">{vendor.position}</div>
            )}
          </div>
        </div>

        {/* Professional Central Security Emblem */}
        <div className="absolute top-12 right-6">
          <div 
            className="w-20 h-20 rounded-full flex flex-col items-center justify-center shadow-2xl border-4"
            style={{ 
              background: `conic-gradient(from 0deg, ${template.colors.primary}, ${template.colors.secondary}, ${template.colors.accent}, ${template.colors.primary})`,
              borderColor: 'white',
              boxShadow: 'inset 0 4px 8px rgba(255,255,255,0.3), 0 8px 16px rgba(0,0,0,0.2), 0 0 20px rgba(22,163,74,0.3)'
            }}
          >
            {/* Inner circle */}
            <div className="w-14 h-14 bg-white rounded-full flex flex-col items-center justify-center shadow-inner relative">
              {/* Holographic effect */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-transparent via-white/30 to-transparent"></div>
              
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center mb-1 relative z-10"
                style={{ backgroundColor: template.colors.primary }}
              >
                <div 
                  className="w-5 h-5 rounded-sm flex items-center justify-center"
                  style={{ backgroundColor: template.colors.accent }}
                >
                  <div className="w-3 h-3 bg-white transform rotate-45"></div>
                </div>
              </div>
              
              <div className="text-xs font-bold text-center leading-tight relative z-10" style={{ color: template.colors.secondary }}>
                <div>VERIFIED</div>
                <div>VENDOR-ID</div>
              </div>
            </div>
            
            {/* Outer ring text */}
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="w-20 h-20 transform -rotate-90">
                <path 
                  id="circle-path" 
                  d="M 40,40 m -35,0 a 35,35 0 1,1 70,0 a 35,35 0 1,1 -70,0" 
                  fill="none" 
                  stroke="none" 
                />
                <text className="text-xs font-bold fill-white" style={{ fontSize: '6px' }}>
                  <textPath href="#circle-path">
                    VERIFIED VENDOR-ID SECURE TRADE • VERIFIED VENDOR-ID SECURE TRADE •
                  </textPath>
                </text>
              </svg>
            </div>
          </div>
        </div>

        {/* Security Code Display (Premium+ templates) */}
        {features.security_code && vendor.securityCode && (
          <div className="absolute bottom-4 right-4">
            <div className="bg-white/90 backdrop-blur-sm rounded px-2 py-1 shadow-md border border-white/50">
              <div className="flex items-center space-x-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowSecurityCode(!showSecurityCode)}
                  className="p-1 h-5 w-5"
                >
                  {showSecurityCode ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                </Button>
                <div className="text-xs font-mono font-bold" style={{ color: template.colors.secondary }}>
                  {showSecurityCode ? vendor.securityCode : '••••••'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Digital Signature (Executive template) */}
        {features.digital_signature && vendor.digitalSignature && (
          <div className="absolute bottom-12 left-28">
            <div className="bg-white/80 backdrop-blur-sm rounded px-2 py-1 shadow-sm border border-white/30">
              <div className="text-xs font-mono text-gray-500">
                SIG: {vendor.digitalSignature.slice(0, 8)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const CardBack = () => (
    <div 
      className="relative w-[400px] h-[250px] rounded-lg overflow-hidden shadow-2xl border border-gray-200"
      style={{ 
        background: getGradientBackground(),
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.4)'
      }}
    >
      <MicrotextBorder />
      <GeometricPattern />
      <SecurityWatermark />
      
      {/* Glossy overlay effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>
      
      <div className="relative z-10 p-4 h-full">
        {/* Professional Magnetic Stripe */}
        <div className="absolute top-6 left-4 right-4">
          <div className="h-8 bg-gradient-to-r from-gray-800 via-black to-gray-800 rounded flex items-center justify-center shadow-inner border border-gray-700">
            <div className="text-white text-xs font-mono tracking-wider opacity-80">
              {Array(32).fill('█').join('')}
            </div>
          </div>
        </div>

        {/* Enhanced Security Fingerprint */}
        <div className="absolute top-24 left-1/2 transform -translate-x-1/2">
          <div className="w-20 h-24 flex items-center justify-center">
            <div 
              className="w-16 h-20 rounded-lg flex items-center justify-center shadow-lg border-2"
              style={{ 
                backgroundColor: template.colors.primary + '20',
                borderColor: template.colors.primary
              }}
            >
              <svg className="w-12 h-16" fill={template.colors.primary} viewBox="0 0 24 24">
                <path d="M12 1C8.27 1 5.18 4.04 5.01 7.73C4.96 8.39 5.12 9.09 5.46 9.75C6.12 11.04 7.18 12.17 8.5 13.05C9.73 13.86 11.18 14.34 12.7 14.42C13.21 14.45 13.72 14.42 14.22 14.32C15.77 14.03 17.21 13.3 18.36 12.23C19.65 11.04 20.53 9.47 20.9 7.73C21.06 6.96 21.01 6.16 20.77 5.42C20.22 3.8 19.03 2.47 17.5 1.68C16.26 1.04 14.87 0.75 13.5 0.82C12.97 0.85 12.47 0.93 12 1ZM12 3C14.76 3 17 5.24 17 8S14.76 13 12 13S7 10.76 7 8S9.24 3 12 3ZM12 5C10.34 5 9 6.34 9 8S10.34 11 12 11S15 9.66 15 8S13.66 5 12 5Z"/>
              </svg>
            </div>
          </div>
        </div>

        {/* Professional QR Code - Back */}
        <div className="absolute top-24 right-6">
          <div className="bg-white p-2 rounded shadow-lg border border-gray-200">
            <div className="w-16 h-16 bg-white border border-gray-300 rounded flex items-center justify-center overflow-hidden">
              <img 
                src={vendorAPI.getQRCodeURL(vendor.id)} 
                alt="QR Code"
                className="w-15 h-15 object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="w-15 h-15 bg-black opacity-80 flex items-center justify-center text-white text-xs" style={{display: 'none'}}>
                QR
              </div>
            </div>
          </div>
        </div>

        {/* Professional Legal Text */}
        <div className="absolute bottom-16 left-4 right-4">
          <div className="bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-md border border-white/50">
            <div className="text-xs leading-relaxed font-medium" style={{ color: template.colors.secondary }}>
              <div className="font-bold mb-1">SECURITY NOTICE</div>
              This card is the property of <strong>Africa Digital Commerce Council (ADCC)</strong>. 
              If found, please return to <strong>www.vendor-id.com</strong>. 
              Unauthorized use, duplication, or alteration is strictly prohibited and may result in legal action.
              
              {features.digital_signature && vendor.digitalSignature && (
                <div className="mt-2 pt-2 border-t border-gray-300">
                  <div className="font-mono text-gray-600 text-xs">
                    Digital Signature: {vendor.digitalSignature}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Enhanced Bottom Right Chip */}
        <div className="absolute bottom-4 right-4">
          <div 
            className="w-8 h-6 rounded border shadow-md flex items-center justify-center"
            style={{ 
              background: `linear-gradient(145deg, #fbbf24, #f59e0b)`,
              borderColor: '#d97706',
              boxShadow: 'inset 0 2px 4px rgba(255,255,255,0.4), 0 2px 8px rgba(0,0,0,0.15)'
            }}
          >
            <div className="w-6 h-4 rounded-sm border flex" style={{ backgroundColor: '#f59e0b', borderColor: '#d97706' }}>
              <div className="w-1 h-1 bg-amber-800 m-0.5 rounded-full"></div>
              <div className="w-1 h-1 bg-amber-800 m-0.5 rounded-full"></div>
            </div>
          </div>
          <div className="text-xs text-center text-gray-600 font-medium mt-1">CHIP</div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`relative ${className}`}>
      <div className="flex flex-col items-center space-y-6">
        <div className="flex flex-wrap gap-3 mb-4 justify-center">
          <Button onClick={onFlip} variant="outline" size="sm" className="shadow-md hover:shadow-lg transition-shadow">
            <RotateCcw className="w-4 h-4 mr-2" />
            Flip Card
          </Button>
          <Button onClick={handlePrint} variant="outline" size="sm" className="shadow-md hover:shadow-lg transition-shadow">
            <Printer className="w-4 h-4 mr-2" />
            Print
          </Button>
          <Button onClick={handleShare} variant="outline" size="sm" className="shadow-md hover:shadow-lg transition-shadow">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>
        
        <div 
          id={`professional-vendor-card-${vendor.id}`}
          className={`transition-transform duration-700 transform-style-preserve-3d ${
            isFlipped ? 'rotate-y-180' : ''
          }`}
          style={{ transformStyle: 'preserve-3d' }}
        >
          <div className={`${isFlipped ? 'hidden' : 'block'}`}>
            <CardFront />
          </div>
          <div className={`${isFlipped ? 'block' : 'hidden'}`}>
            <CardBack />
          </div>
        </div>
        
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Badge 
            variant={vendor.status === 'verified' ? 'default' : 
                     vendor.status === 'expired' ? 'destructive' :
                     vendor.status === 'suspended' ? 'destructive' : 'secondary'}
            className="shadow-sm"
            style={vendor.status === 'verified' ? { backgroundColor: template.colors.primary } : {}}
          >
            {vendor.status.toUpperCase()}
          </Badge>
          <span className="text-sm text-gray-600 font-medium">ID: {vendor.id}</span>
          <Badge variant="outline" className="shadow-sm" style={{ borderColor: template.colors.primary, color: template.colors.primary }}>
            {vendor.template.toUpperCase()}
          </Badge>
          {vendor.expiryDate && (
            <span className="text-xs text-gray-500">Expires: {vendor.expiryDate}</span>
          )}
        </div>
      </div>
      
      {/* Professional CSS for animations */}
      <style jsx>{`
        @keyframes marquee {
          0% { transform: translateX(100%); }
          100% { transform: translateX(-100%); }
        }
        .animate-marquee {
          animation: marquee 15s linear infinite;
        }
        .transform-style-preserve-3d {
          transform-style: preserve-3d;
        }
        .rotate-y-180 {
          transform: rotateY(180deg);
        }
      `}</style>
    </div>
  );
};

export default ProfessionalVendorCard;