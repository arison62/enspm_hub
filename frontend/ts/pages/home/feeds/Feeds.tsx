import React, { useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Briefcase, ArrowRight } from "lucide-react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import AppLayout from "@/components/layouts/app-layout";
import FeedsMainContent from "../components/feeds/feeds-main-content";
import StatsCard from "../components/feeds/stats-card";

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
          <aside className="hidden lg:block lg:col-span-3 sticky top-20 space-y-6 animate-in">
            <StatsCard />
          </aside>

          {/* CONTENU CENTRAL - Seul cet élément définit le scroll principal */}
          <main className="lg:col-span-6 space-y-6">
            <FeedsMainContent />
          </main>

          {/* SIDEBAR DROITE - Masquée sur mobile, Sticky sur Desktop */}
          <aside className="hidden lg:block lg:col-span-3 sticky top-20 animate-in">
            <Card className="shadow-sm border-none">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center justify-between">
                  Opportunités
                  <Briefcase className="h-4 w-4 text-blue-600" />
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[1, 2, 3].map((_, i) => (
                  <div key={i} className="space-y-1 group cursor-pointer">
                    <h4 className="text-xs font-bold group-hover:text-blue-600 transition-colors">
                      Ingénieur Logiciel Fullstack
                    </h4>
                    <p className="text-[10px] text-muted-foreground">
                      Tech Corp • Yaoundé
                    </p>
                    <Badge variant="secondary" className="text-[9px] h-4">
                      CDI
                    </Badge>
                  </div>
                ))}
                <Separator />
                <Button
                  variant="outline"
                  className="w-full text-xs h-9 border-blue-100 text-blue-600 hover:bg-blue-50"
                >
                  Toutes les offres <ArrowRight className="ml-2 h-3 w-3" />
                </Button>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </div>
  );
};

FeedPage.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>;

export default FeedPage;
