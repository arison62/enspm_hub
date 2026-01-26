"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";
import { cn } from "@/lib/utils";

interface FloatingDrawerButtonProps {
  onClick?: () => void;
  className?: string;
  /**
   * Position verticale du bouton (en pourcentage de la hauteur de la fenêtre)
   * @default 50 (centre)
   */
  verticalPosition?: number;
  /**
   * Distance du bord gauche (en pixels)
   * @default 0
   */
  leftOffset?: number;
  /**
   * Si true, le bouton devient transparent au scroll
   * @default true
   */
  fadeOnScroll?: boolean;
  /**
   * Sensibilité de la transparence (plus la valeur est élevée, plus le bouton devient transparent rapidement)
   * @default 0.05
   */
  sensitivity?: number;
}

export function FloatingDrawerButton({
  onClick,
  className,
  verticalPosition = 50,
  leftOffset = 0,
  fadeOnScroll = true,
  sensitivity = 0.05,
}: FloatingDrawerButtonProps) {
  const [scrollVelocity, setScrollVelocity] = useState(0);
  const [opacity, setOpacity] = useState(1);
  const [isVisible, setIsVisible] = useState(true);
  const [isHovered, setIsHovered] = useState(false);
  const [windowHeight, setWindowHeight] = useState(0);
  const [mounted, setMounted] = useState(false);

  // Références pour le calcul de la vitesse
  const lastScrollPosition = useRef(0);
  const lastScrollTime = useRef(0);
  const scrollTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const animationFrameId = useRef<number | null>(null);

  useEffect(() => {
    setMounted(true);
    setWindowHeight(window.innerHeight);
  }, []);

  // Mettre à jour la hauteur de la fenêtre
  useEffect(() => {
    const updateWindowHeight = () => {
      setWindowHeight(window.innerHeight);
    };
    window.addEventListener("resize", updateWindowHeight);
    return () => window.removeEventListener("resize", updateWindowHeight);
  }, []);

  // Calculer la position verticale en pixels
  const topPosition = (windowHeight * verticalPosition) / 100;

  // Gestion du scroll pour l'effet de transparence basé sur la vitesse
  useEffect(() => {
    if (!fadeOnScroll) {
      setOpacity(1);
      setIsVisible(true);
      return;
    }

    const handleScroll = () => {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }

      animationFrameId.current = requestAnimationFrame(() => {
        const currentTime = Date.now();
        const currentScroll = window.scrollY;

        // Calculer la vitesse de défilement
        const timeDiff = currentTime - lastScrollTime.current;
        const positionDiff = currentScroll - lastScrollPosition.current;

        // Vitesse en pixels par milliseconde
        const velocity = timeDiff > 0 ? Math.abs(positionDiff) / timeDiff : 0;

        // Mettre à jour les références
        lastScrollPosition.current = currentScroll;
        lastScrollTime.current = currentTime;

        // Mettre à jour la vitesse
        setScrollVelocity(velocity);

        // Calculer l'opacité basée sur la vitesse
        const maxVelocity = 5; // Vitesse maximale considérée (pixels/ms)
        const normalizedVelocity =
          Math.min(velocity, maxVelocity) / maxVelocity;

        // Plus la vitesse est élevée, plus l'opacité diminue
        const newOpacity = Math.max(
          0.2,
          1 - normalizedVelocity * sensitivity * 20,
        );
        const newVisible = newOpacity > 0.2;

        setOpacity(newOpacity);
        setIsVisible(newVisible);

        // Réinitialiser après un délai d'inactivité
        if (scrollTimeout.current) {
          clearTimeout(scrollTimeout.current);
        }

        scrollTimeout.current = setTimeout(() => {
          setScrollVelocity(0);
          if (currentScroll < 100) {
            setOpacity(1);
            setIsVisible(true);
          }
        }, 2000);
      });
    };

    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      window.removeEventListener("scroll", handleScroll);
      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, [fadeOnScroll, sensitivity]);

  // Calcul de l'échelle
  const calculateScale = useCallback(() => {
    if (isHovered) return 1.1;
    return 1;
  }, [isHovered]);

  const scale = calculateScale();

  // Si nous ne sommes pas encore monté, ne rien rendre
  if (!mounted) return null;

  return (
    <Button
      variant="outline"
      size="icon"
      className={cn(
        "fixed z-100",
        "rounded-l-none rounded-r-lg shadow-lg",
        "transition-all duration-300 ease-out",
        "bg-background backdrop-blur supports-[backdrop-filter]:bg-background/60",
        "border border-border hover:border-primary hover:shadow-xl",
        "hover:bg-background",
        !isVisible && "opacity-0 pointer-events-none",
        className,
      )}
      style={{
        top: `${topPosition * 0.8}px`,
        left: `${leftOffset}px`,
        opacity: isHovered ? 1 : opacity,
        transform: `translateY(-50%) scale(${scale})`,
        transformOrigin: "left center",
      }}
      onClick={onClick}
      onMouseEnter={() => {
        setIsHovered(true);
        setOpacity(1);
      }}
      onMouseLeave={() => {
        setIsHovered(false);

        const maxVelocity = 5;
        const normalizedVelocity =
          Math.min(scrollVelocity, maxVelocity) / maxVelocity;
        const newOpacity = Math.max(
          0.2,
          1 - normalizedVelocity * sensitivity * 20,
        );
        setOpacity(newOpacity);
      }}
      aria-label="Ouvrir le menu de navigation"
    >
      <Menu className="h-5 w-5 transition-transform duration-300 group-hover:rotate-90" />
    </Button>
  );
}
