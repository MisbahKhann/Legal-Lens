'use client';

import React, { useEffect, useRef, useCallback } from 'react';

const TOTAL_FRAMES = 150;

function getFrameUrl(index: number): string {
  const paddedIndex = String(index).padStart(3, '0');
  return `/frames/frame_${paddedIndex}.jpg`;
}

interface ScrollCanvasSequenceProps {
  children?: React.ReactNode;
}

export const ScrollCanvasSequence: React.FC<ScrollCanvasSequenceProps> = ({ children }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<(HTMLImageElement | null)[]>([]);
  const targetFrameRef = useRef<number>(1);
  const currentFrameRef = useRef<number>(1);
  const lastDrawnFrameRef = useRef<number>(-1);
  const animFrameIdRef = useRef<number | null>(null);
  const isReducedMotionRef = useRef<boolean>(false);
  const progressRef = useRef<number>(0);

  // Nearest available frame helper
  const getClosestFrame = useCallback((targetIdx: number): HTMLImageElement | null => {
    const images = imagesRef.current;
    if (images[targetIdx - 1] && images[targetIdx - 1]?.complete && images[targetIdx - 1]?.naturalWidth !== 0) {
      return images[targetIdx - 1];
    }
    // Search backward
    for (let i = targetIdx - 1; i >= 1; i--) {
      if (images[i - 1] && images[i - 1]?.complete && images[i - 1]?.naturalWidth !== 0) {
        return images[i - 1];
      }
    }
    // Search forward
    for (let i = targetIdx + 1; i <= TOTAL_FRAMES; i++) {
      if (images[i - 1] && images[i - 1]?.complete && images[i - 1]?.naturalWidth !== 0) {
        return images[i - 1];
      }
    }
    return null;
  }, []);

  const drawFrame = useCallback((frameIndex: number, currentProgress: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = getClosestFrame(frameIndex);
    if (!img) return;

    const dpr = typeof window !== 'undefined' ? (window.devicePixelRatio || 1) : 1;
    const width = window.innerWidth;
    const height = window.innerHeight;

    if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
      canvas.width = width * dpr;
      canvas.height = height * dpr;
    }

    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Aspect ratio preserving cover math
    const imgRatio = img.naturalWidth / img.naturalHeight;
    const canvasRatio = width / height;
    let drawWidth = width;
    let drawHeight = height;
    let offsetX = 0;
    let offsetY = 0;

    if (canvasRatio > imgRatio) {
      drawHeight = width / imgRatio;
      offsetY = (height - drawHeight) / 2;
    } else {
      drawWidth = height * imgRatio;
      offsetX = (width - drawWidth) / 2;
    }

    // Render image frame cleanly
    ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);

    // Progressive visual fading: As user scrolls down, opacity of warm overlay increases to keep text/cards high contrast
    const fadeFactor = Math.min(1, Math.max(0, (currentProgress - 0.15) / 0.7));
    const centerAlpha = 0.22 + fadeFactor * 0.55;
    const outerAlpha = 0.65 + fadeFactor * 0.25;

    const overlayGradient = ctx.createRadialGradient(
      width * 0.5, height * 0.5, width * 0.2,
      width * 0.5, height * 0.5, width * 0.85
    );
    overlayGradient.addColorStop(0, `rgba(20, 13, 14, ${centerAlpha.toFixed(2)})`);
    overlayGradient.addColorStop(0.7, `rgba(20, 13, 14, ${(centerAlpha + 0.12).toFixed(2)})`);
    overlayGradient.addColorStop(1, `rgba(20, 13, 14, ${outerAlpha.toFixed(2)})`);

    ctx.fillStyle = overlayGradient;
    ctx.fillRect(0, 0, width, height);

    ctx.restore();
    lastDrawnFrameRef.current = frameIndex;
  }, [getClosestFrame]);

  // Progressive image preloading
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      isReducedMotionRef.current = mediaQuery.matches;
    }

    const images: (HTMLImageElement | null)[] = new Array(TOTAL_FRAMES).fill(null);
    imagesRef.current = images;

    // Load Frame 1 first to draw immediately
    const img1 = new Image();
    img1.src = getFrameUrl(1);
    img1.onload = () => {
      images[0] = img1;
      drawFrame(1, 0);
    };

    // Load next 20 frames as priority batch
    for (let i = 2; i <= 20; i++) {
      const img = new Image();
      img.src = getFrameUrl(i);
      const frameIdx = i;
      img.onload = () => {
        images[frameIdx - 1] = img;
      };
    }

    // Load remaining frames progressively
    for (let i = 21; i <= TOTAL_FRAMES; i++) {
      const img = new Image();
      img.src = getFrameUrl(i);
      const frameIdx = i;
      img.onload = () => {
        images[frameIdx - 1] = img;
      };
    }
  }, [drawFrame]);

  // Scroll mapping across entire page document
  useEffect(() => {
    const updateTargetFrame = () => {
      if (isReducedMotionRef.current) {
        targetFrameRef.current = 1;
        progressRef.current = 0;
        return;
      }

      if (typeof window === 'undefined') return;

      const scrollY = window.scrollY;
      const docHeight = document.documentElement.scrollHeight;
      const winHeight = window.innerHeight;
      const maxScroll = Math.max(1, docHeight - winHeight);
      
      const rawProgress = scrollY / maxScroll;
      const progress = Math.max(0, Math.min(1, rawProgress));
      progressRef.current = progress;

      // Map progress 0..1 smoothly across all 150 frames
      targetFrameRef.current = 1 + progress * (TOTAL_FRAMES - 1);
    };

    const renderLoop = () => {
      updateTargetFrame();

      // Smooth lerp interpolation towards target frame
      const diff = targetFrameRef.current - currentFrameRef.current;
      if (Math.abs(diff) > 0.001) {
        currentFrameRef.current += diff * 0.15;
      } else {
        currentFrameRef.current = targetFrameRef.current;
      }

      const targetFrameRound = Math.round(currentFrameRef.current);
      if (targetFrameRound !== lastDrawnFrameRef.current) {
        drawFrame(targetFrameRound, progressRef.current);
      }

      animFrameIdRef.current = requestAnimationFrame(renderLoop);
    };

    const handleResize = () => {
      drawFrame(Math.round(currentFrameRef.current), progressRef.current);
    };

    window.addEventListener('scroll', updateTargetFrame, { passive: true });
    window.addEventListener('resize', handleResize);

    animFrameIdRef.current = requestAnimationFrame(renderLoop);

    return () => {
      window.removeEventListener('scroll', updateTargetFrame);
      window.removeEventListener('resize', handleResize);
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [drawFrame]);

  return (
    <div className="scroll-sequence-wrapper">
      {/* Persistent Fullscreen Canvas Background */}
      <div className="fixed-canvas-background">
        <canvas ref={canvasRef} className="sequence-canvas" />
      </div>

      {/* Page Content Overlay */}
      <div className="page-content-layer">
        {children}
      </div>

      <style jsx>{`
        .scroll-sequence-wrapper {
          position: relative;
          width: 100%;
          min-height: 100vh;
          background: #140d0e;
        }

        .fixed-canvas-background {
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          overflow: hidden;
          pointer-events: none;
          z-index: 0;
        }

        .sequence-canvas {
          width: 100%;
          height: 100%;
          display: block;
        }

        .page-content-layer {
          position: relative;
          z-index: 10;
          width: 100%;
          pointer-events: auto;
        }
      `}</style>
    </div>
  );
};
