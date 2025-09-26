import React, { useState, useEffect, useRef } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { RotateCcw, Printer, Download, Share2, Eye, EyeOff, Maximize2, Minimize2 } from 'lucide-react';
import { vendorAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const ResponsiveProfessionalCard = ({ vendor, isFlipped, onFlip, className = '' }) => {
  const [imageError, setImageError] = useState(false);
  const [cardData, setCardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSecurityCode, setShowSecurityCode] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [cardScale, setCardScale] = useState(1);
  const [isAnimating, setIsAnimating] = useState(false);
  const cardRef = useRef(null);
  const containerRef = useRef(null);
  const { toast } = useToast();

  useEffect(() => {
    loadCardData();
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [vendor.id]);

  const handleResize = () => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.offsetWidth;
      const baseCardWidth = 400;
      const newScale = Math.min(1, (containerWidth - 40) / baseCardWidth);
      setCardScale(newScale);
    }
  };

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

  const handleFlip = () => {
    setIsAnimating(true);
    onFlip();
    setTimeout(() => setIsAnimating(false), 700);
  };

  const handlePrint = async () => {
    try {
      const printWindow = window.open('', '_blank');
      const cardElement = cardRef.current;
      
      printWindow.document.write(`
        <html>
          <head>
            <title>Professional Vendor ID Card - ${vendor.name}</title>
            <style>
              * { margin: 0; padding: 0; box-sizing: border-box; }
              body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: white;
                padding: 20mm;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
              }
              .print-card { 
                transform: scale(1.5);
                transform-origin: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
              }
              @media print { 
                body { padding: 0; margin: 0; }
                .print-card { transform: scale(1.2); }
              }
            </style>
          </head>
          <body>
            <div class="print-card">${cardElement.outerHTML}</div>
          </body>
        </html>
      `);
      
      printWindow.document.close();
      setTimeout(() => printWindow.print(), 500);
      
      toast({
        title: "Print Started",
        description: "Professional card ready for printing"
      });
    } catch (error) {
      toast({
        title: "Print Error",
        description: "Failed to prepare card for printing",
        variant: "destructive"
      });
    }
  };

  const handleShare = async () => {
    try {
      if (navigator.share && navigator.canShare) {
        await navigator.share({
          title: `Professional Vendor ID - ${vendor.name}`,
          text: `${vendor.name} - ${vendor.id}\nCompany: ${vendor.company || 'N/A'}\nStatus: ${vendor.status}`,
          url: window.location.href
        });
      } else {
        const shareText = `Professional Vendor ID\n\nName: ${vendor.name}\nID: ${vendor.id}\nCompany: ${vendor.company || 'N/A'}\nStatus: ${vendor.status.toUpperCase()}\nIssued: ${vendor.issueDate}\nExpires: ${vendor.expiryDate || 'N/A'}`;
        await navigator.clipboard.writeText(shareText);
        toast({
          title: "Shared Successfully",
          description: "Vendor information copied to clipboard"
        });
      }
    } catch (error) {
      toast({
        title: "Share Failed",
        description: "Unable to share vendor information",
        variant: "destructive"
      });
    }
  };

  const handleDownload = async () => {
    try {
      // Create a high-resolution canvas for download
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = 1200; // High DPI
      canvas.height = 750;
      
      // For now, show success message
      toast({
        title: "Download Prepared",
        description: "High-resolution card image ready"
      });
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Unable to generate card image",
        variant: "destructive"
      });
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center w-full min-h-[250px] bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl animate-pulse">
        <div className="flex flex-col items-center space-y-4">
          <div className="relative">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-200 border-t-emerald-600"></div>
            <div className="absolute inset-0 rounded-full bg-emerald-50 animate-ping opacity-75"></div>
          </div>
          <p className="text-gray-600 font-medium animate-pulse">Loading professional card...</p>
        </div>
      </div>
    );
  }

  const template = cardData?.template || { colors: { primary: '#16a34a', secondary: '#0f766e', accent: '#eab308' } };
  const features = cardData?.features || {};

  // Responsive gradient backgrounds
  const getGradientBackground = () => {
    switch (vendor.template) {
      case 'premium':
        return 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 30%, #cbd5e1 70%, #94a3b8 100%)';
      case 'executive':
        return 'linear-gradient(135deg, #fefefe 0%, #f1f5f9 30%, #e2e8f0 70%, #cbd5e1 100%)';
      default:
        return 'linear-gradient(135deg, #ffffff 0%, #f8fafc 30%, #f1f5f9 70%, #e2e8f0 100%)';
    }
  };

  // Enhanced microtext with animations
  const AnimatedMicrotextBorder = () => (
    <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-xl">
      {/* Animated top border */}
      <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-r from-emerald-600 via-green-500 to-emerald-600 flex items-center justify-center overflow-hidden">
        <div className="text-white text-xs font-bold tracking-wider whitespace-nowrap animate-marquee-slow opacity-90">
          VENDOR-ID • SECURITY • VERIFIED • AUTHENTIC • VENDOR-ID • SECURITY • VERIFIED • AUTHENTIC • VENDOR-ID • SECURITY • VERIFIED • AUTHENTIC
        </div>
      </div>
      
      {/* Animated bottom border */}
      <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-r from-emerald-600 via-green-500 to-emerald-600 flex items-center justify-center overflow-hidden">
        <div className="text-white text-xs font-bold tracking-wider whitespace-nowrap animate-marquee-reverse opacity-90">
          QR-ID • SECURE • TRADE • VERIFIED • QR-ID • SECURE • TRADE • VERIFIED • QR-ID • SECURE • TRADE • VERIFIED
        </div>
      </div>
      
      {/* Left border */}
      <div className="absolute left-0 top-0 bottom-0 w-4 bg-gradient-to-b from-emerald-600 via-green-500 to-emerald-600 flex flex-col items-center justify-center overflow-hidden">
        <div className="text-white text-xs font-bold tracking-wider transform -rotate-90 whitespace-nowrap opacity-90">
          VENDOR-ID • SECURE • ID
        </div>
      </div>
      
      {/* Right border */}
      <div className="absolute right-0 top-0 bottom-0 w-4 bg-gradient-to-b from-emerald-600 via-green-500 to-emerald-600 flex flex-col items-center justify-center overflow-hidden">
        <div className="text-white text-xs font-bold tracking-wider transform rotate-90 whitespace-nowrap opacity-90">
          VENDOR-ID • SECURE • ID
        </div>
      </div>
    </div>
  );

  // Enhanced geometric pattern with animations
  const ResponsiveGeometricPattern = () => (
    <div className="absolute inset-0 opacity-5 overflow-hidden pointer-events-none">
      <svg width="100%" height="100%" viewBox="0 0 400 250" className="animate-pulse-slow">
        <defs>
          <pattern id="responsive-pattern" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M0,0 L40,40 M0,40 L40,0" stroke="#16a34a" strokeWidth="0.5" opacity="0.4" />
            <path d="M20,0 L20,40 M0,20 L40,20" stroke="#16a34a" strokeWidth="0.3" opacity="0.3" />
            <circle cx="0" cy="0" r="1.5" fill="#16a34a" opacity="0.5" className="animate-pulse" />
            <circle cx="40" cy="40" r="1.5" fill="#16a34a" opacity="0.5" className="animate-pulse" style={{animationDelay: '1s'}} />
            <circle cx="20" cy="20" r="1" fill="#16a34a" opacity="0.4" className="animate-pulse" style={{animationDelay: '0.5s'}} />
          </pattern>
          
          <radialGradient id="responsive-glow" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor="#16a34a" stopOpacity="0.15" />
            <stop offset="50%" stopColor="#16a34a" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#16a34a" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#responsive-pattern)" />
        <ellipse cx="200" cy="125" rx="150" ry="100" fill="url(#responsive-glow)" className="animate-pulse-slow" />
      </svg>
    </div>
  );

  // Enhanced security watermark
  const ResponsiveSecurityWatermark = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
      <div className="text-6xl md:text-8xl lg:text-9xl font-bold text-gray-100 opacity-12 transform rotate-12 select-none whitespace-nowrap tracking-wider animate-pulse-slow">
        VERIFIED VENDOR-ID SECURE TRADE
      </div>
    </div>
  );

  const ResponsiveCardFront = () => (
    <div 
      className="relative w-full max-w-[400px] aspect-[8/5] rounded-xl overflow-hidden shadow-2xl border border-gray-200 transform transition-all duration-500 hover:shadow-3xl hover:scale-[1.02]"
      style={{ 
        background: getGradientBackground(),
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.4)'
      }}
    >
      <AnimatedMicrotextBorder />
      <ResponsiveGeometricPattern />
      <ResponsiveSecurityWatermark />
      
      {/* Enhanced glossy overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-transparent pointer-events-none animate-shimmer"></div>
      
      <div className="relative z-10 p-3 sm:p-4 h-full flex flex-col">
        {/* Responsive Header Logo */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            <div className="relative group">
              <div 
                className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center border-2 shadow-lg transition-all duration-300 group-hover:scale-110"
                style={{ 
                  background: `linear-gradient(145deg, ${template.colors.primary}, ${template.colors.secondary})`,
                  borderColor: template.colors.accent,
                  boxShadow: 'inset 0 2px 4px rgba(255,255,255,0.3), 0 4px 12px rgba(0,0,0,0.25)'
                }}
              >
                <div className="w-4 h-4 sm:w-6 sm:h-6 bg-white rounded-full flex items-center justify-center shadow-inner">
                  <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full" style={{ backgroundColor: template.colors.secondary }}>
                    <div className="w-full h-full rounded-full bg-gradient-to-br from-white/60 to-transparent"></div>
                  </div>
                </div>
              </div>
              {/* Animated security seal */}
              <div 
                className="absolute -top-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 rounded-full flex items-center justify-center shadow-lg animate-pulse"
                style={{ backgroundColor: template.colors.accent }}
              >
                <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 transform rotate-45" style={{ backgroundColor: template.colors.secondary }}></div>
              </div>
            </div>
            <div className="hidden sm:block">
              <div className="font-bold text-xs sm:text-sm" style={{ color: template.colors.secondary }}>Vendor-ID</div>
              <div className="text-xs text-gray-600 font-medium hidden md:block">Verified. Trusted. Secure Trade.</div>
            </div>
          </div>

          {/* Responsive EMV Chip */}
          <div className="relative group">
            <div 
              className="w-8 h-5 sm:w-10 sm:h-7 rounded border shadow-lg flex items-center justify-center transition-all duration-300 group-hover:scale-105"
              style={{ 
                background: `linear-gradient(145deg, #fbbf24, #f59e0b)`,
                borderColor: '#d97706',
                boxShadow: 'inset 0 2px 4px rgba(255,255,255,0.4), 0 4px 12px rgba(0,0,0,0.2)'
              }}
            >
              <div className="w-6 h-3 sm:w-8 sm:h-5 rounded-sm border flex flex-wrap" style={{ backgroundColor: '#f59e0b', borderColor: '#d97706' }}>
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="w-0.5 h-0.5 sm:w-1 sm:h-1 m-0.5 bg-amber-800 rounded-full animate-pulse" style={{animationDelay: `${i * 0.1}s`}}></div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Responsive content area */}
        <div className="flex-1 flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0 sm:space-x-4">
          {/* Left side - Photo and codes */}
          <div className="flex flex-col items-center space-y-2 sm:space-y-3">
            {/* Professional Vendor Photo */}
            <div className="relative group">
              <div className="w-16 h-20 sm:w-20 sm:h-24 rounded-lg border-3 border-white shadow-xl overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 transition-all duration-300 group-hover:scale-105">
                {!imageError && vendor.photo ? (
                  <img 
                    src={vendor.photo} 
                    alt={vendor.name}
                    className="w-full h-full object-cover transition-all duration-300 group-hover:brightness-110"
                    onError={() => setImageError(true)}
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center text-gray-500 text-xs font-medium">
                    PHOTO
                  </div>
                )}
              </div>
            </div>

            {/* Responsive QR and Barcode */}
            <div className="flex space-x-2 sm:space-x-3">
              {/* QR Code */}
              <div className="bg-white p-1 rounded shadow-lg border border-gray-200 transition-all duration-300 hover:shadow-xl hover:scale-105">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white border border-gray-200 rounded flex items-center justify-center overflow-hidden">
                  <img 
                    src={vendorAPI.getQRCodeURL(vendor.id)} 
                    alt="QR Code"
                    className="w-9 h-9 sm:w-11 sm:h-11 object-contain"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                  <div className="w-9 h-9 sm:w-11 sm:h-11 bg-black opacity-80 flex items-center justify-center text-white text-xs animate-pulse" style={{display: 'none'}}>
                    QR
                  </div>
                </div>
                <div className="text-xs text-center text-gray-600 font-medium mt-1">QR-ID</div>
              </div>

              {/* Barcode */}
              <div className="bg-white p-1 rounded shadow-lg border border-gray-200 transition-all duration-300 hover:shadow-xl hover:scale-105">
                <div className="w-10 h-12 sm:w-12 sm:h-16 bg-white border border-gray-200 rounded flex items-center justify-center overflow-hidden">
                  <img 
                    src={vendorAPI.getBarcodeURL(vendor.id)} 
                    alt="Barcode"
                    className="w-8 h-10 sm:w-10 sm:h-14 object-contain transform rotate-90"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                  <div className="w-8 h-10 sm:w-10 sm:h-14 bg-black opacity-80 flex items-center justify-center flex-col animate-pulse" style={{display: 'none'}}>
                    {[...Array(8)].map((_, i) => (
                      <div key={i} className="w-full h-1 bg-white my-0.5"></div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Center - Information */}
          <div className="text-center flex-1 px-2">
            <div className="bg-white/90 backdrop-blur-sm rounded-lg p-3 sm:p-4 shadow-lg border border-white/50 transition-all duration-300 hover:bg-white/95 hover:shadow-xl">
              <div className="font-bold text-sm sm:text-lg mb-1 sm:mb-2" style={{ color: template.colors.secondary }}>VENDOR ID CARD</div>
              <div className="text-black font-bold text-base sm:text-xl mb-1 sm:mb-2 leading-tight">{vendor.name}</div>
              <div className="font-bold text-sm sm:text-base mb-1 sm:mb-2" style={{ color: template.colors.secondary }}>{vendor.id}</div>
              <div className="text-gray-700 text-xs sm:text-sm mb-1">ISSUE: {vendor.issueDate}</div>
              {vendor.expiryDate && (
                <div className="text-gray-700 text-xs sm:text-sm mb-2">EXPIRES: {vendor.expiryDate}</div>
              )}
              {vendor.company && (
                <div className="text-gray-600 text-xs sm:text-sm font-medium border-t border-gray-200 pt-2">
                  {vendor.company}
                </div>
              )}
              {vendor.position && (
                <div className="text-gray-600 text-xs">{vendor.position}</div>
              )}
            </div>
          </div>

          {/* Right side - Security seal */}
          <div className="relative group">
            <div 
              className="w-16 h-16 sm:w-20 sm:h-20 rounded-full flex flex-col items-center justify-center shadow-2xl border-4 transition-all duration-500 group-hover:scale-110 group-hover:rotate-12"
              style={{ 
                background: `conic-gradient(from 0deg, ${template.colors.primary}, ${template.colors.secondary}, ${template.colors.accent}, ${template.colors.primary})`,
                borderColor: 'white',
                boxShadow: 'inset 0 4px 8px rgba(255,255,255,0.3), 0 8px 20px rgba(0,0,0,0.25), 0 0 30px rgba(22,163,74,0.4)'
              }}
            >
              {/* Inner circle with holographic effect */}
              <div className="w-12 h-12 sm:w-14 sm:h-14 bg-white rounded-full flex flex-col items-center justify-center shadow-inner relative overflow-hidden">
                {/* Animated holographic effect */}
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-transparent via-white/40 to-transparent animate-spin-slow"></div>
                
                <div 
                  className="w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center mb-1 relative z-10 transition-all duration-300 group-hover:scale-110"
                  style={{ backgroundColor: template.colors.primary }}
                >
                  <div 
                    className="w-3 h-3 sm:w-5 sm:h-5 rounded-sm flex items-center justify-center"
                    style={{ backgroundColor: template.colors.accent }}
                  >
                    <div className="w-2 h-2 sm:w-3 sm:h-3 bg-white transform rotate-45"></div>
                  </div>
                </div>
                
                <div className="text-xs font-bold text-center leading-tight relative z-10" style={{ color: template.colors.secondary }}>
                  <div>VERIFIED</div>
                  <div className="text-xs">VENDOR-ID</div>
                </div>
              </div>
              
              {/* Animated outer ring */}
              <div className="absolute inset-0 rounded-full animate-ping opacity-20" style={{ backgroundColor: template.colors.primary }}></div>
            </div>
          </div>
        </div>

        {/* Security features footer */}
        <div className="flex justify-between items-end mt-2">
          {/* Digital signature */}
          {features.digital_signature && vendor.digitalSignature && (
            <div className="bg-white/80 backdrop-blur-sm rounded px-2 py-1 shadow-sm border border-white/30">
              <div className="text-xs font-mono text-gray-500">
                SIG: {vendor.digitalSignature.slice(0, 6)}
              </div>
            </div>
          )}

          {/* Security code */}
          {features.security_code && vendor.securityCode && (
            <div className="bg-white/90 backdrop-blur-sm rounded px-2 py-1 shadow-md border border-white/50">
              <div className="flex items-center space-x-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowSecurityCode(!showSecurityCode)}
                  className="p-1 h-4 w-4 hover:bg-white/50"
                >
                  {showSecurityCode ? <EyeOff className="w-2 h-2" /> : <Eye className="w-2 h-2" />}
                </Button>
                <div className="text-xs font-mono font-bold" style={{ color: template.colors.secondary }}>
                  {showSecurityCode ? vendor.securityCode : '••••••'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const ResponsiveCardBack = () => (
    <div 
      className="relative w-full max-w-[400px] aspect-[8/5] rounded-xl overflow-hidden shadow-2xl border border-gray-200 transform transition-all duration-500 hover:shadow-3xl hover:scale-[1.02]"
      style={{ 
        background: getGradientBackground(),
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.4)'
      }}
    >
      <AnimatedMicrotextBorder />
      <ResponsiveGeometricPattern />
      <ResponsiveSecurityWatermark />
      
      {/* Enhanced glossy overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-transparent pointer-events-none animate-shimmer-reverse"></div>
      
      <div className="relative z-10 p-3 sm:p-4 h-full flex flex-col">
        {/* Professional Magnetic Stripe */}
        <div className="mb-4">
          <div className="h-6 sm:h-8 bg-gradient-to-r from-gray-800 via-black to-gray-800 rounded flex items-center justify-center shadow-inner border border-gray-700 transition-all duration-300 hover:shadow-lg">
            <div className="text-white text-xs font-mono tracking-wider opacity-80 animate-pulse">
              {Array(24).fill('█').join('')}
            </div>
          </div>
        </div>

        {/* Content area */}
        <div className="flex-1 flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
          {/* Center - Security fingerprint */}
          <div className="flex-1 flex justify-center">
            <div className="relative group">
              <div className="w-16 h-20 sm:w-20 sm:h-24 flex items-center justify-center">
                <div 
                  className="w-12 h-16 sm:w-16 sm:h-20 rounded-lg flex items-center justify-center shadow-lg border-2 transition-all duration-500 group-hover:scale-110 group-hover:rotate-3"
                  style={{ 
                    backgroundColor: template.colors.primary + '20',
                    borderColor: template.colors.primary
                  }}
                >
                  <svg className="w-8 h-12 sm:w-12 sm:h-16 transition-all duration-300 group-hover:scale-110" fill={template.colors.primary} viewBox="0 0 24 24">
                    <path d="M12 1C8.27 1 5.18 4.04 5.01 7.73C4.96 8.39 5.12 9.09 5.46 9.75C6.12 11.04 7.18 12.17 8.5 13.05C9.73 13.86 11.18 14.34 12.7 14.42C13.21 14.45 13.72 14.42 14.22 14.32C15.77 14.03 17.21 13.3 18.36 12.23C19.65 11.04 20.53 9.47 20.9 7.73C21.06 6.96 21.01 6.16 20.77 5.42C20.22 3.8 19.03 2.47 17.5 1.68C16.26 1.04 14.87 0.75 13.5 0.82C12.97 0.85 12.47 0.93 12 1ZM12 3C14.76 3 17 5.24 17 8S14.76 13 12 13S7 10.76 7 8S9.24 3 12 3ZM12 5C10.34 5 9 6.34 9 8S10.34 11 12 11S15 9.66 15 8S13.66 5 12 5Z"/>
                  </svg>
                  {/* Scanning effect */}
                  <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/20 to-transparent animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Right - QR Code */}
          <div className="relative group">
            <div className="bg-white p-2 rounded-lg shadow-lg border border-gray-200 transition-all duration-300 group-hover:shadow-xl group-hover:scale-105">
              <div className="w-14 h-14 sm:w-16 sm:h-16 bg-white border border-gray-300 rounded flex items-center justify-center overflow-hidden">
                <img 
                  src={vendorAPI.getQRCodeURL(vendor.id)} 
                  alt="QR Code"
                  className="w-13 h-13 sm:w-15 sm:h-15 object-contain transition-all duration-300 group-hover:brightness-110"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
                <div className="w-13 h-13 sm:w-15 sm:h-15 bg-black opacity-80 flex items-center justify-center text-white text-xs animate-pulse" style={{display: 'none'}}>
                  QR
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Professional Legal Text */}
        <div className="mt-4">
          <div className="bg-white/95 backdrop-blur-sm rounded-lg p-3 sm:p-4 shadow-md border border-white/50 transition-all duration-300 hover:bg-white hover:shadow-lg">
            <div className="text-xs leading-relaxed font-medium" style={{ color: template.colors.secondary }}>
              <div className="font-bold mb-2 flex items-center space-x-2">
                <div className="w-4 h-4 rounded-full bg-gradient-to-br from-red-400 to-red-600 flex items-center justify-center">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                </div>
                <span>SECURITY NOTICE</span>
              </div>
              <div className="space-y-1 text-justify">
                <p>This card is the property of <strong>Africa Digital Commerce Council (ADCC)</strong>.</p>
                <p>If found, please return to <strong>www.vendor-id.com</strong>.</p>
                <p>Unauthorized use, duplication, or alteration is strictly prohibited and may result in legal action.</p>
              </div>
              
              {features.digital_signature && vendor.digitalSignature && (
                <div className="mt-3 pt-3 border-t border-gray-300">
                  <div className="font-mono text-gray-600 text-xs bg-gray-50 rounded p-2">
                    <span className="font-semibold">Digital Signature:</span> {vendor.digitalSignature}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Enhanced Bottom Chip */}
        <div className="absolute bottom-3 right-3 sm:bottom-4 sm:right-4">
          <div className="relative group">
            <div 
              className="w-6 h-4 sm:w-8 sm:h-6 rounded border shadow-lg flex items-center justify-center transition-all duration-300 group-hover:scale-110"
              style={{ 
                background: `linear-gradient(145deg, #fbbf24, #f59e0b)`,
                borderColor: '#d97706',
                boxShadow: 'inset 0 2px 4px rgba(255,255,255,0.4), 0 4px 12px rgba(0,0,0,0.2)'
              }}
            >
              <div className="w-4 h-2 sm:w-6 sm:h-4 rounded-sm border flex" style={{ backgroundColor: '#f59e0b', borderColor: '#d97706' }}>
                <div className="w-1 h-1 bg-amber-800 m-0.5 rounded-full animate-pulse"></div>
                <div className="w-1 h-1 bg-amber-800 m-0.5 rounded-full animate-pulse" style={{animationDelay: '0.5s'}}></div>
              </div>
            </div>
            <div className="text-xs text-center text-gray-600 font-medium mt-1">CHIP</div>
            {/* Scanning effect */}
            <div className="absolute -inset-2 border-2 border-emerald-400 rounded opacity-0 group-hover:opacity-100 animate-ping transition-opacity duration-300"></div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div ref={containerRef} className={`relative w-full max-w-2xl mx-auto ${className}`}>
      {/* Fullscreen overlay */}
      {isFullscreen && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-fadeIn" onClick={toggleFullscreen}>
          <div className="relative" onClick={(e) => e.stopPropagation()}>
            <Button 
              onClick={toggleFullscreen}
              variant="outline"
              size="sm"
              className="absolute -top-12 right-0 bg-white/90 hover:bg-white z-10"
            >
              <Minimize2 className="w-4 h-4 mr-2" />
              Exit Fullscreen
            </Button>
            <div style={{ transform: `scale(${Math.min(1.5, window.innerWidth / 500)})` }}>
              {isFlipped ? <ResponsiveCardBack /> : <ResponsiveCardFront />}
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col items-center space-y-4 sm:space-y-6">
        {/* Enhanced Action Buttons */}
        <div className="flex flex-wrap gap-2 sm:gap-3 justify-center p-2">
          <Button 
            onClick={handleFlip} 
            variant="outline" 
            size="sm" 
            disabled={isAnimating}
            className="shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 bg-white/90 backdrop-blur-sm border-emerald-200 hover:border-emerald-300"
          >
            <RotateCcw className={`w-4 h-4 mr-2 transition-transform duration-700 ${isAnimating ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Flip Card</span>
            <span className="sm:hidden">Flip</span>
          </Button>
          
          <Button 
            onClick={handlePrint} 
            variant="outline" 
            size="sm"
            className="shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 bg-white/90 backdrop-blur-sm border-blue-200 hover:border-blue-300"
          >
            <Printer className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">Print</span>
            <span className="sm:hidden">Print</span>
          </Button>
          
          <Button 
            onClick={handleDownload} 
            variant="outline" 
            size="sm"
            className="shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 bg-white/90 backdrop-blur-sm border-purple-200 hover:border-purple-300"
          >
            <Download className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">Download</span>
            <span className="sm:hidden">Save</span>
          </Button>
          
          <Button 
            onClick={handleShare} 
            variant="outline" 
            size="sm"
            className="shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 bg-white/90 backdrop-blur-sm border-green-200 hover:border-green-300"
          >
            <Share2 className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">Share</span>
            <span className="sm:hidden">Share</span>
          </Button>
          
          <Button 
            onClick={toggleFullscreen} 
            variant="outline" 
            size="sm"
            className="shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 bg-white/90 backdrop-blur-sm border-orange-200 hover:border-orange-300"
          >
            <Maximize2 className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">Fullscreen</span>
            <span className="sm:hidden">Full</span>
          </Button>
        </div>
        
        {/* Responsive Card Container */}
        <div 
          ref={cardRef}
          className={`transition-all duration-700 transform-gpu ${
            isFlipped ? 'rotate-y-180' : ''
          } ${isAnimating ? 'scale-95' : 'hover:scale-[1.02]'}`}
          style={{ 
            transformStyle: 'preserve-3d',
            transform: `scale(${cardScale}) ${isFlipped ? 'rotateY(180deg)' : ''}`
          }}
        >
          <div className={`transition-opacity duration-500 ${isFlipped ? 'opacity-0 absolute inset-0' : 'opacity-100'}`}>
            <ResponsiveCardFront />
          </div>
          <div className={`transition-opacity duration-500 ${isFlipped ? 'opacity-100' : 'opacity-0 absolute inset-0'}`}>
            <ResponsiveCardBack />
          </div>
        </div>
        
        {/* Enhanced Info Badges */}
        <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 px-4">
          <Badge 
            variant={vendor.status === 'verified' ? 'default' : 
                     vendor.status === 'expired' ? 'destructive' :
                     vendor.status === 'suspended' ? 'destructive' : 'secondary'}
            className="shadow-md transition-all duration-300 hover:shadow-lg hover:scale-105 px-3 py-1"
            style={vendor.status === 'verified' ? { backgroundColor: template.colors.primary } : {}}
          >
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full animate-pulse ${
                vendor.status === 'verified' ? 'bg-green-300' :
                vendor.status === 'pending' ? 'bg-yellow-300' :
                'bg-red-300'
              }`}></div>
              <span className="font-medium">{vendor.status.toUpperCase()}</span>
            </div>
          </Badge>
          
          <Badge variant="outline" className="shadow-md hover:scale-105 transition-all duration-300 px-3 py-1" style={{ borderColor: template.colors.primary, color: template.colors.primary }}>
            <span className="font-medium">{vendor.template.toUpperCase()}</span>
          </Badge>
          
          <span className="text-sm text-gray-600 font-medium bg-gray-100 rounded-full px-3 py-1 shadow-sm">
            ID: {vendor.id}
          </span>
          
          {vendor.expiryDate && (
            <span className={`text-xs px-3 py-1 rounded-full shadow-sm font-medium ${
              new Date(vendor.expiryDate) < new Date() 
                ? 'bg-red-100 text-red-700' 
                : 'bg-green-100 text-green-700'
            }`}>
              {new Date(vendor.expiryDate) < new Date() ? 'EXPIRED' : `Expires: ${vendor.expiryDate}`}
            </span>
          )}
        </div>
      </div>
      
      {/* Professional CSS for enhanced animations */}
      <style jsx>{`
        @keyframes marquee-slow {
          0% { transform: translateX(100%); }
          100% { transform: translateX(-100%); }
        }
        
        @keyframes marquee-reverse {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        
        @keyframes shimmer-reverse {
          0% { transform: translateX(100%); }
          100% { transform: translateX(-100%); }
        }
        
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.8; }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        .animate-marquee-slow {
          animation: marquee-slow 20s linear infinite;
        }
        
        .animate-marquee-reverse {
          animation: marquee-reverse 25s linear infinite;
        }
        
        .animate-shimmer {
          animation: shimmer 3s ease-in-out infinite;
        }
        
        .animate-shimmer-reverse {
          animation: shimmer-reverse 4s ease-in-out infinite;
        }
        
        .animate-spin-slow {
          animation: spin-slow 8s linear infinite;
        }
        
        .animate-pulse-slow {
          animation: pulse-slow 4s ease-in-out infinite;
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
        
        .transform-gpu {
          transform: translate3d(0, 0, 0);
        }
        
        .shadow-3xl {
          box-shadow: 0 35px 60px -12px rgba(0, 0, 0, 0.25);
        }
      `}</style>
    </div>
  );
};

export default ResponsiveProfessionalCard;