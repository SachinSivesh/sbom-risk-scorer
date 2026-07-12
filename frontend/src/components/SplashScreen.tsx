import { useState, useEffect } from 'react';

interface SplashScreenProps {
  onComplete: () => void;
}

export default function SplashScreen({ onComplete }: SplashScreenProps) {
  const [phase, setPhase] = useState<'preload' | 'fade-in' | 'active' | 'exiting'>('preload');
  const [imgLoaded, setImgLoaded] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Detect prefers-reduced-motion user agent settings
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    // Preload startup image asset
    const img = new Image();
    img.src = '/startup_screen.jpeg';
    img.onload = () => {
      setImgLoaded(true);
      setPhase('fade-in');
    };
  }, []);

  useEffect(() => {
    if (phase === 'fade-in') {
      // 1. Transition from initial load/fade to active hold
      const timer = setTimeout(() => {
        setPhase('active');
      }, 400); // 400ms fade-in window
      return () => clearTimeout(timer);
    }

    if (phase === 'active') {
      // 2. Hold active branding visual state
      const timer = setTimeout(() => {
        setPhase('exiting');
      }, 1500); // 1.5s active visual hold
      return () => clearTimeout(timer);
    }

    if (phase === 'exiting') {
      // 3. Slide screen upwards and fade out
      const timer = setTimeout(() => {
        onComplete();
      }, 600); // 600ms exit transition
      return () => clearTimeout(timer);
    }
  }, [phase, onComplete]);

  if (phase === 'preload' && !imgLoaded) {
    // Initial empty wrapper to avoid layout jumps
    return <div className="fixed inset-0 z-50 bg-white" />;
  }

  // Full screen overlay styling
  const overlayStyle: React.CSSProperties = {
    position: 'fixed',
    inset: 0,
    zIndex: 99999, // Overlay all components (nav, sidebar, graph layers)
    backgroundColor: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'transform 600ms cubic-bezier(0.16, 1, 0.3, 1), opacity 600ms ease',
    transform: phase === 'exiting' ? 'translateY(-100%)' : 'translateY(0%)',
    opacity: phase === 'exiting' ? 0 : 1,
    pointerEvents: phase === 'exiting' ? 'none' : 'auto',
  };

  const containerStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  };

  const imageStyle: React.CSSProperties = {
    maxWidth: '100%',
    maxHeight: '100%',
    objectFit: 'contain',
    transition: prefersReducedMotion
      ? 'opacity 400ms ease'
      : 'opacity 400ms ease, transform 1900ms cubic-bezier(0.16, 1, 0.3, 1)',
    opacity: phase === 'preload' ? 0 : 1,
    transform: prefersReducedMotion
      ? 'none'
      : phase === 'fade-in'
      ? 'scale(0.98)'
      : 'scale(1)',
  };

  return (
    <div style={overlayStyle}>
      <div style={containerStyle}>
        <img
          src="/startup_screen.jpeg"
          alt="Nexora Secure Platform Startup"
          style={imageStyle}
        />
      </div>
    </div>
  );
}
