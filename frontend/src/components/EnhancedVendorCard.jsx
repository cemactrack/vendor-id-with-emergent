import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { RotateCcw, Printer, Download, Share2, Eye, EyeOff } from 'lucide-react';
import { vendorAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const EnhancedVendorCard = ({ vendor, isFlipped, onFlip, className = '' }) => {
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
    const printWindow = window.open('', '_blank');
    const cardElement = document.getElementById(`vendor-card-${vendor.id}`);
    
    printWindow.document.write(`
      <html>
        <head>
          <title>Vendor ID Card - ${vendor.name}</title>
          <style>
            body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
            .print-card { transform: scale(1.2); transform-origin: top left; }
            @media print { body { margin: 0; padding: 0; } }
          </style>
        </head>
        <body>
          <div class="print-card">${cardElement.outerHTML}</div>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
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
      // Fallback - copy to clipboard
      await navigator.clipboard.writeText(`Vendor: ${vendor.name}\nID: ${vendor.id}\nStatus: ${vendor.status}`);
      toast({
        title: "Copied to clipboard",
        description: "Vendor information copied to clipboard"
      });
    }
  };

  const handleDownload = async () => {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const cardElement = document.getElementById(`vendor-card-${vendor.id}`);
      
      // Simple implementation - in production you'd use html2canvas or similar
      const link = document.createElement('a');
      link.download = `vendor-card-${vendor.id}.png`;
      link.href = canvas.toDataURL();
      link.click();
      
      toast({
        title: "Download started",
        description: "Card image download initiated"
      });
    } catch (error) {
      toast({
        title: "Download failed",
        description: "Failed to download card image",
        variant: "destructive"
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center w-[340px] h-[215px] bg-gray-100 rounded-lg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
      </div>
    );
  }

  const template = cardData?.template || { colors: { primary: '#16a34a', secondary: '#0f766e', accent: '#eab308' } };
  const features = cardData?.features || {};
  const patterns = cardData?.patterns || {};

  const CircuitryPattern = () => (
    <div className="absolute inset-0 opacity-10 overflow-hidden pointer-events-none">
      {patterns.circuit ? (
        <img 
          src={`data:image/png;base64,${patterns.circuit}`}
          alt="Circuit Pattern"
          className="w-full h-full object-cover"
        />
      ) : (
        <svg width="100%" height="100%" viewBox="0 0 400 250">
          <defs>
            <pattern id="circuitry" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M10,10 L30,10 L30,30 M20,10 L20,30 M10,20 L30,20" 
                    stroke={template.colors.primary} 
                    strokeWidth="0.5" 
                    fill="none" />
              <circle cx="10" cy="10" r="1" fill={template.colors.primary} />
              <circle cx="30" cy="30" r="1" fill={template.colors.primary} />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#circuitry)" />
        </svg>
      )}
    </div>
  );

  const WatermarkText = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      {patterns.watermark ? (
        <img 
          src={`data:image/png;base64,${patterns.watermark}`}
          alt="Security Watermark"
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="text-6xl font-bold text-gray-200 opacity-20 transform rotate-12 select-none whitespace-nowrap">
          VERIFIED VENDOR-ID SECURE TRADE
        </div>
      )}
    </div>
  );

  const HolographicOverlay = () => (
    patterns.holographic && (
      <div className="absolute inset-0 opacity-30 overflow-hidden pointer-events-none">
        <img 
          src={`data:image/png;base64,${patterns.holographic}`}
          alt="Holographic Pattern"
          className="w-full h-full object-cover mix-blend-overlay"
        />
      </div>
    )
  );

  const CardFront = () => (
    <div 
      className="relative w-[340px] h-[215px] bg-white rounded-lg border-4 overflow-hidden shadow-2xl"
      style={{ borderColor: template.colors.primary }}
    >
      <CircuitryPattern />
      <WatermarkText />
      <HolographicOverlay />
      
      {/* Enhanced border with template colors */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className={`absolute h-4 flex items-center justify-center ${
              i === 0 ? 'top-0 left-0 right-0' :
              i === 1 ? 'bottom-0 left-0 right-0' :
              i === 2 ? 'left-0 top-0 bottom-0 w-4' :
              'right-0 top-0 bottom-0 w-4'
            }`}
            style={{ backgroundColor: template.colors.primary }}
          >
            <div className="text-white text-xs font-semibold tracking-widest overflow-hidden whitespace-nowrap"
                 style={{ transform: i > 1 ? `rotate(${i === 2 ? -90 : 90}deg)` : 'none' }}>
              VENDOR-ID VENDOR-ID VENDOR-ID
            </div>
          </div>
        ))}
      </div>

      <div className="relative z-10 p-6 h-full">
        {/* Enhanced Logo and Brand */}
        <div className="absolute top-6 left-6">
          <div className="flex items-center space-x-2 mb-1">
            <div className="relative">
              <div 
                className="w-8 h-8 rounded-sm flex items-center justify-center border"
                style={{ 
                  background: `linear-gradient(to bottom, ${template.colors.primary}, ${template.colors.secondary})`,
                  borderColor: template.colors.accent
                }}
              >
                <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: template.colors.secondary }}></div>
                </div>
              </div>
              <div 
                className="absolute -top-1 -right-1 w-3 h-3 rounded-full flex items-center justify-center"
                style={{ backgroundColor: template.colors.accent }}
              >
                <div className="w-1.5 h-1.5 transform rotate-45" style={{ backgroundColor: template.colors.secondary }}></div>
              </div>
            </div>
            <div>
              <div className="font-bold text-sm" style={{ color: template.colors.secondary }}>Vendor-ID</div>
              <div className="text-xs text-gray-600">Verified. Trusted. Secure Trade.</div>
            </div>
          </div>
        </div>

        {/* Smart Card Chip */}
        <div className="absolute top-6 right-6">
          <div 
            className="w-8 h-6 rounded border flex items-center justify-center"
            style={{ 
              background: `linear-gradient(to bottom, ${template.colors.accent}dd, ${template.colors.accent})`,
              borderColor: template.colors.accent
            }}
          >
            <div className="w-6 h-4 rounded-sm border flex flex-wrap" style={{ backgroundColor: template.colors.accent, borderColor: template.colors.secondary }}>
              {[...Array(4)].map((_, i) => (
                <div key={i} className="w-1 h-1 m-0.5" style={{ backgroundColor: template.colors.secondary }}></div>
              ))}
            </div>
          </div>
        </div>

        {/* Enhanced Vendor Photo */}
        <div className="absolute bottom-6 left-6">
          <div className="w-16 h-16 rounded-full border-2 border-white shadow-lg overflow-hidden bg-gray-200">
            {!imageError && vendor.photo ? (
              <img 
                src={vendor.photo} 
                alt={vendor.name}
                className="w-full h-full object-cover"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="w-full h-full bg-gray-300 flex items-center justify-center text-gray-500 text-xs">
                PHOTO
              </div>
            )}
          </div>
        </div>

        {/* Enhanced QR Code */}
        <div className="absolute bottom-6 left-24">
          <div className="w-12 h-12 bg-white border border-gray-300 rounded flex items-center justify-center overflow-hidden">
            <img 
              src={vendorAPI.getQRCodeURL(vendor.id)} 
              alt="QR Code"
              className="w-10 h-10 object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
            <div className="w-10 h-10 bg-black opacity-80 flex items-center justify-center text-white text-xs" style={{display: 'none'}}>
              QR
            </div>
          </div>
        </div>

        {/* Enhanced Barcode */}
        <div className="absolute bottom-6 left-40">
          <div className="w-16 h-12 bg-white border border-gray-300 rounded flex items-center justify-center overflow-hidden">
            <img 
              src={vendorAPI.getBarcodeURL(vendor.id)} 
              alt="Barcode"
              className="w-14 h-8 object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
            <div className="w-14 h-8 bg-black opacity-80 flex items-center justify-center flex-col" style={{display: 'none'}}>
              {[...Array(8)].map((_, i) => (
                <div key={i} className="w-full h-1 bg-white my-0.5"></div>
              ))}
            </div>
          </div>
        </div>

        {/* Enhanced Center Text Block */}
        <div className="absolute top-16 left-1/2 transform -translate-x-1/2 text-center">
          <div className="font-bold text-sm mb-1" style={{ color: template.colors.secondary }}>VENDOR ID CARD</div>
          <div className="text-black font-bold text-lg mb-1">{vendor.name}</div>
          <div className="font-semibold text-sm mb-1" style={{ color: template.colors.secondary }}>{vendor.id}</div>
          <div className="text-gray-700 text-xs mb-1">ISSUE DATE: {vendor.issueDate}</div>
          {features.expiry_date && vendor.expiryDate && (
            <div className="text-gray-700 text-xs">EXPIRES: {vendor.expiryDate}</div>
          )}
          {features.company_info && vendor.company && (
            <div className="text-gray-600 text-xs mt-1">{vendor.company}</div>
          )}
          {features.company_info && vendor.position && (
            <div className="text-gray-600 text-xs">{vendor.position}</div>
          )}
        </div>

        {/* Enhanced Verified Seal */}
        <div className="absolute top-20 right-6">
          <div 
            className="w-16 h-16 rounded-full border-4 bg-white flex flex-col items-center justify-center"
            style={{ borderColor: template.colors.secondary }}
          >
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center mb-1"
              style={{ backgroundColor: template.colors.primary }}
            >
              <div 
                className="w-4 h-4 rounded-sm flex items-center justify-center"
                style={{ backgroundColor: template.colors.accent }}
              >
                <div className="w-2 h-2 bg-white transform rotate-45"></div>
              </div>
            </div>
            <div className="text-xs font-bold text-center leading-none" style={{ color: template.colors.secondary }}>
              <div>VERIFIED</div>
              <div>VENDOR-ID</div>
            </div>
          </div>
        </div>

        {/* Security Code (Premium+ templates) */}
        {features.security_code && vendor.securityCode && (
          <div className="absolute bottom-2 right-6">
            <div className="flex items-center space-x-1">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowSecurityCode(!showSecurityCode)}
                className="p-1 h-6"
              >
                {showSecurityCode ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              </Button>
              <div className="text-xs font-mono" style={{ color: template.colors.secondary }}>
                {showSecurityCode ? vendor.securityCode : '******'}
              </div>
            </div>
          </div>
        )}

        {/* Digital Signature (Executive template) */}
        {features.digital_signature && vendor.digitalSignature && (
          <div className="absolute bottom-2 left-6">
            <div className="text-xs font-mono text-gray-500">
              SIG: {vendor.digitalSignature.slice(0, 8)}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const CardBack = () => (
    <div 
      className="relative w-[340px] h-[215px] bg-white rounded-lg border-4 overflow-hidden shadow-2xl"
      style={{ borderColor: template.colors.primary }}
    >
      <CircuitryPattern />
      <WatermarkText />
      <HolographicOverlay />
      
      {/* Enhanced border */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className={`absolute h-4 flex items-center justify-center ${
              i === 0 ? 'top-0 left-0 right-0' :
              i === 1 ? 'bottom-0 left-0 right-0' :
              i === 2 ? 'left-0 top-0 bottom-0 w-4' :
              'right-0 top-0 bottom-0 w-4'
            }`}
            style={{ backgroundColor: template.colors.primary }}
          >
            <div className="text-white text-xs font-semibold tracking-widest overflow-hidden whitespace-nowrap"
                 style={{ transform: i > 1 ? `rotate(${i === 2 ? -90 : 90}deg)` : 'none' }}>
              VENDOR-ID VENDOR-ID VENDOR-ID
            </div>
          </div>
        ))}
      </div>

      <div className="relative z-10 p-6 h-full">
        {/* Enhanced Magnetic Stripe */}
        <div className="absolute top-6 left-6 right-6">
          <div className="h-6 bg-black rounded flex items-center justify-center overflow-hidden">
            <div className="text-white text-xs font-mono tracking-wider">
              {Array(24).fill('█').join('')}
            </div>
          </div>
        </div>

        {/* Enhanced Fingerprint Icon */}
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2">
          <div className="w-16 h-20 flex items-center justify-center">
            <svg className="w-12 h-16" fill={template.colors.primary} viewBox="0 0 24 24">
              <path d="M12 2C8.69 2 6 4.69 6 8c0 1.89.85 3.58 2.18 4.72L12 16.47l3.82-3.75C17.15 11.58 18 9.89 18 8c0-3.31-2.69-6-6-6zm0 8.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 5.5 12 5.5s2.5 1.12 2.5 2.5S13.38 10.5 12 10.5z"/>
            </svg>
          </div>
        </div>

        {/* Enhanced QR Code */}
        <div className="absolute top-20 right-6">
          <div className="w-16 h-16 bg-white border border-gray-300 rounded flex items-center justify-center overflow-hidden">
            <img 
              src={vendorAPI.getQRCodeURL(vendor.id)} 
              alt="QR Code"
              className="w-14 h-14 object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
            <div className="w-14 h-14 bg-black opacity-80 flex items-center justify-center text-white text-xs" style={{display: 'none'}}>
              QR
            </div>
          </div>
        </div>

        {/* Enhanced Bottom Text */}
        <div className="absolute bottom-6 right-6 left-6">
          <div className="text-xs leading-relaxed" style={{ color: template.colors.secondary }}>
            This card is the property of Africa Digital Commerce Council (ADCC). 
            If found, please return to www.vendor-id.com. 
            Unauthorized use is prohibited.
            {features.digital_signature && vendor.digitalSignature && (
              <div className="mt-2 font-mono text-gray-500">
                Digital Signature: {vendor.digitalSignature}
              </div>
            )}
          </div>
        </div>

        {/* Bottom Right Chip */}
        <div className="absolute bottom-6 right-6">
          <div 
            className="w-6 h-4 rounded border flex items-center justify-center"
            style={{ 
              background: `linear-gradient(to bottom, ${template.colors.accent}dd, ${template.colors.accent})`,
              borderColor: template.colors.accent
            }}
          >
            <div className="w-4 h-2 rounded-sm border flex" style={{ backgroundColor: template.colors.accent, borderColor: template.colors.secondary }}>
              <div className="w-1 h-1 m-0.5" style={{ backgroundColor: template.colors.secondary }}></div>
              <div className="w-1 h-1 m-0.5" style={{ backgroundColor: template.colors.secondary }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`relative ${className}`}>
      <div className="flex flex-col items-center space-y-4">
        <div className="flex flex-wrap gap-2 mb-2 justify-center">
          <Button onClick={onFlip} variant="outline" size="sm">
            <RotateCcw className="w-4 h-4 mr-2" />
            Flip Card
          </Button>
          <Button onClick={handlePrint} variant="outline" size="sm">
            <Printer className="w-4 h-4 mr-2" />
            Print
          </Button>
          <Button onClick={handleDownload} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          <Button onClick={handleShare} variant="outline" size="sm">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>
        
        <div 
          id={`vendor-card-${vendor.id}`}
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
        
        <div className="flex flex-wrap items-center justify-center gap-2">
          <Badge 
            variant={vendor.status === 'verified' ? 'default' : 
                     vendor.status === 'expired' ? 'destructive' :
                     vendor.status === 'suspended' ? 'destructive' : 'secondary'}
            style={vendor.status === 'verified' ? { backgroundColor: template.colors.primary } : {}}
          >
            {vendor.status.toUpperCase()}
          </Badge>
          <span className="text-sm text-gray-500">ID: {vendor.id}</span>
          <Badge variant="outline">{vendor.template.toUpperCase()}</Badge>
          {vendor.expiryDate && (
            <span className="text-xs text-gray-500">Expires: {vendor.expiryDate}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedVendorCard;