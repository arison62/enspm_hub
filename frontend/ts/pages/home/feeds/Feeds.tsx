import React, { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import AppLayout from "@/components/layouts/app-layout";
import FeedsMainContent from "../components/feeds/feeds-main-content";
import StatsCard from "../components/feeds/stats-card";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import { FloatingDrawerButton } from "../components/feeds/floating-button";
import { LatestOpportunities } from "../components/feeds/latest_opportunities";

const FeedPage = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Animation d'entrée
  useGSAP(
    () => {
      const tl = gsap.timeline();
      tl.from(".animate-in", {
        y: 30,
        opacity: 0,
        stagger: 0.1,
        duration: 0.8,
        ease: "power3.out",
      });
    },
    { scope: containerRef },
  );

  return (
    <div
      className="min-h-screen bg-slate-50/50 dark:bg-zinc-950"
      ref={containerRef}
    >
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* SIDEBAR GAUCHE - Masquée sur mobile, Sticky sur Desktop */}
          <aside className="lg:col-span-3 sticky top-20 space-y-6 animate-in">
            <div className="hidden lg:block">
              <StatsCard />
            </div>
            <Drawer direction="left">
              <DrawerTrigger asChild>
                <FloatingDrawerButton
                  
                  fadeOnScroll={true}
                  sensitivity={0.09}
                  className="block lg:hidden"
                />
              </DrawerTrigger>
              <DrawerContent>
                <DrawerHeader>
                  <DrawerTitle>Statistiques</DrawerTitle>
                  <StatsCard />
                </DrawerHeader>
              </DrawerContent>
            </Drawer>
          </aside>

          {/* CONTENU CENTRAL - Seul cet élément définit le scroll principal */}
          <main className="lg:col-span-6 space-y-6">
            <FeedsMainContent />
          </main>

          {/* SIDEBAR DROITE - Masquée sur mobile, Sticky sur Desktop */}
          <aside className="hidden lg:block lg:col-span-3 sticky top-20 animate-in">
            <LatestOpportunities />
          </aside>
        </div>
      </div>
    </div>
  );
};

FeedPage.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>;

export default FeedPage;
