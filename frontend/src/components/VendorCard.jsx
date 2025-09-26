import React, { useState } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { RotateCcw, Printer, Download } from 'lucide-react';
import { generateQRCode, generateBarcode } from '../data/mock';

const VendorCard = ({ vendor, isFlipped, onFlip, className = '' }) => {
  const [imageError, setImageError] = useState(false);

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

  const CircuitryPattern = () => (
    <div className="absolute inset-0 opacity-5 overflow-hidden pointer-events-none">
      <svg width="100%" height="100%" viewBox="0 0 400 250">
        <defs>
          <pattern id="circuitry" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M10,10 L30,10 L30,30 M20,10 L20,30 M10,20 L30,20" 
                  stroke="#16a34a" 
                  strokeWidth="0.5" 
                  fill="none" />
            <circle cx="10" cy="10" r="1" fill="#16a34a" />
            <circle cx="30" cy="30" r="1" fill="#16a34a" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#circuitry)" />
      </svg>
    </div>
  );

  const WatermarkText = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div className="text-6xl font-bold text-gray-200 opacity-20 transform rotate-12 select-none whitespace-nowrap">
        VERIFIED VENDOR-ID SECURE TRADE
      </div>
    </div>
  );

  const CardFront = () => (
    <div className="relative w-[340px] h-[215px] bg-white rounded-lg border-4 border-green-500 overflow-hidden shadow-2xl">
      <CircuitryPattern />
      <WatermarkText />
      
      {/* Repeating border text */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-4 bg-green-500 flex items-center justify-center">
          <div className="text-white text-xs font-semibold tracking-widest overflow-hidden whitespace-nowrap">
            VENDOR-ID VENDOR-ID VENDOR-ID VENDOR-ID VENDOR-ID
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-4 bg-green-500 flex items-center justify-center">
          <div className="text-white text-xs font-semibold tracking-widest overflow-hidden whitespace-nowrap">
            VENDOR-ID VENDOR-ID VENDOR-ID VENDOR-ID VENDOR-ID
          </div>
        </div>
        <div className="absolute left-0 top-0 bottom-0 w-4 bg-green-500 flex items-center justify-center">
          <div className="text-white text-xs font-semibold tracking-widest transform -rotate-90 whitespace-nowrap">
            VENDOR-ID
          </div>
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-4 bg-green-500 flex items-center justify-center">
          <div className="text-white text-xs font-semibold tracking-widest transform rotate-90 whitespace-nowrap">
            VENDOR-ID
          </div>
        </div>
      </div>

      <div className="relative z-10 p-6 h-full">
        {/* Top Left - Logo and Brand */}
        <div className="absolute top-6 left-6">
          <div className="flex items-center space-x-2 mb-1">
            <div className="relative">
              <div className="w-8 h-8 bg-gradient-to-b from-green-500 to-teal-700 rounded-sm flex items-center justify-center border border-yellow-400">
                <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center">
                  <div className="w-2 h-2 bg-teal-700 rounded-full"></div>
                </div>
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full flex items-center justify-center">
                <div className="w-1.5 h-1.5 bg-teal-700 transform rotate-45"></div>
              </div>
            </div>
            <div>
              <div className="text-teal-700 font-bold text-sm">Vendor-ID</div>
              <div className="text-xs text-gray-600">Verified. Trusted. Secure Trade.</div>
            </div>
          </div>
        </div>

        {/* Smart Card Chip - Top Right */}
        <div className="absolute top-6 right-6">
          <div className="w-8 h-6 bg-gradient-to-b from-yellow-300 to-yellow-500 rounded border border-yellow-600 flex items-center justify-center">
            <div className="w-6 h-4 bg-yellow-400 rounded-sm border border-yellow-600 flex flex-wrap">
              <div className="w-1 h-1 bg-yellow-600 m-0.5"></div>
              <div className="w-1 h-1 bg-yellow-600 m-0.5"></div>
              <div className="w-1 h-1 bg-yellow-600 m-0.5"></div>
              <div className="w-1 h-1 bg-yellow-600 m-0.5"></div>
            </div>
          </div>
        </div>

        {/* Vendor Photo - Bottom Left */}
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

        {/* QR Code - Below Photo */}
        <div className="absolute bottom-6 left-24">
          <div className="w-12 h-12 bg-white border border-gray-300 rounded flex items-center justify-center">
            <div className="w-10 h-10 bg-black opacity-80 flex items-center justify-center text-white text-xs">
              QR
            </div>
          </div>
        </div>

        {/* Barcode - Right of QR */}
        <div className="absolute bottom-6 left-40">
          <div className="w-16 h-12 bg-white border border-gray-300 rounded flex items-center justify-center">
            <div className="w-14 h-8 bg-black opacity-80 flex items-center justify-center flex-col">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="w-full h-1 bg-white my-0.5"></div>
              ))}
            </div>
          </div>
        </div>

        {/* Center Text Block */}
        <div className="absolute top-16 left-1/2 transform -translate-x-1/2 text-center">
          <div className="text-teal-700 font-bold text-sm mb-1">VENDOR ID CARD</div>
          <div className="text-black font-bold text-lg mb-1">{vendor.name}</div>
          <div className="text-teal-700 font-semibold text-sm mb-1">{vendor.id}</div>
          <div className="text-gray-700 text-xs">ISSUE DATE: {vendor.issueDate}</div>
        </div>

        {/* Verified Seal - Right Side */}
        <div className="absolute top-20 right-6">
          <div className="w-16 h-16 rounded-full border-4 border-teal-700 bg-white flex flex-col items-center justify-center">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mb-1">
              <div className="w-4 h-4 bg-yellow-400 rounded-sm flex items-center justify-center">
                <div className="w-2 h-2 bg-white transform rotate-45"></div>
              </div>
            </div>
            <div className="text-teal-700 text-xs font-bold text-center leading-none">
              <div>VERIFIED</div>
              <div>VENDOR-ID</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const CardBack = () => (
    <div className="relative w-[340px] h-[215px] bg-white rounded-lg border-4 border-green-500 overflow-hidden shadow-2xl">
      <CircuitryPattern />
      <WatermarkText />
      
      {/* Repeating border text */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-4 bg-green-500 flex items-center justify-center">
          <div className="text-white text-xs font-semibold tracking-widest overflow-hidden whitespace-nowrap">
            VENDOR-ID VENDOR-ID VENDOR-ID VENDOR-ID VENDOR-ID
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-4 bg-green-500 flex items-center justify-center">
          <div className="text-white text-xs font-semibold tracking-widest overflow-hidden whitespace-nowrap">
            VENDOR-ID VENDOR-ID VENDOR-ID VENDOR-ID VENDOR-ID
          </div>
        </div>
        <div className="absolute left-0 top-0 bottom-0 w-4 bg-green-500 flex items-center justify-center">
          <div className="text-white text-xs font-semibold tracking-widest transform -rotate-90 whitespace-nowrap">
            VENDOR-ID
          </div>
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-4 bg-green-500 flex items-center justify-center">
          <div className="text-white text-xs font-semibold tracking-widest transform rotate-90 whitespace-nowrap">
            VENDOR-ID
          </div>
        </div>
      </div>

      <div className="relative z-10 p-6 h-full">
        {/* Magnetic Stripe - Top */}
        <div className="absolute top-6 left-6 right-6">
          <div className="h-6 bg-black rounded flex items-center justify-center">
            <div className="text-white text-xs font-mono tracking-wider">████████████████████████</div>
          </div>
        </div>

        {/* Fingerprint Icon - Center */}
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2">
          <div className="w-16 h-20 flex items-center justify-center">
            <svg className="w-12 h-16 text-green-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C8.69 2 6 4.69 6 8c0 1.89.85 3.58 2.18 4.72L12 16.47l3.82-3.75C17.15 11.58 18 9.89 18 8c0-3.31-2.69-6-6-6zm0 8.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 5.5 12 5.5s2.5 1.12 2.5 2.5S13.38 10.5 12 10.5z"/>
            </svg>
          </div>
        </div>

        {/* QR Code - Right Side */}
        <div className="absolute top-20 right-6">
          <div className="w-16 h-16 bg-white border border-gray-300 rounded flex items-center justify-center">
            <div className="w-14 h-14 bg-black opacity-80 flex items-center justify-center text-white text-xs">
              QR
            </div>
          </div>
        </div>

        {/* Bottom Text */}
        <div className="absolute bottom-6 right-6 left-6">
          <div className="text-teal-700 text-xs leading-relaxed">
            This card is the property of Africa Digital Commerce Council (ADCC). 
            If found, please return to www.vendor-id.com. 
            Unauthorized use is prohibited.
          </div>
        </div>

        {/* Bottom Right Chip */}
        <div className="absolute bottom-6 right-6">
          <div className="w-6 h-4 bg-gradient-to-b from-yellow-300 to-yellow-500 rounded border border-yellow-600 flex items-center justify-center">
            <div className="w-4 h-2 bg-yellow-400 rounded-sm border border-yellow-600 flex">
              <div className="w-1 h-1 bg-yellow-600 m-0.5"></div>
              <div className="w-1 h-1 bg-yellow-600 m-0.5"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`relative ${className}`}>
      <div className="flex flex-col items-center space-y-4">
        <div className="flex space-x-2 mb-2">
          <Button onClick={onFlip} variant="outline" size="sm">
            <RotateCcw className="w-4 h-4 mr-2" />
            Flip Card
          </Button>
          <Button onClick={handlePrint} variant="outline" size="sm">
            <Print className="w-4 h-4 mr-2" />
            Print
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
        
        <div className="flex items-center space-x-2">
          <Badge variant={vendor.status === 'verified' ? 'default' : 'secondary'}>
            {vendor.status.toUpperCase()}
          </Badge>
          <span className="text-sm text-gray-500">ID: {vendor.id}</span>
        </div>
      </div>
    </div>
  );
};

export default VendorCard;