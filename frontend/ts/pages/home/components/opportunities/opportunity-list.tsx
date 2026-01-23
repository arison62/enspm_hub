import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Briefcase } from "lucide-react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import type { OpportuniteAny } from "@/types/opportunities";

import { OpportuniteCard } from "./opportunity-card";
import { useRef } from "react";

gsap.registerPlugin(useGSAP)

interface OpportuniteListProps {
  items: OpportuniteAny[];
  loading: boolean;
}

export const OpportuniteList = ({ items, loading }: OpportuniteListProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      if (!loading && items.length > 0) {
        gsap.to("opp-card", {
          y: 100,
          opacity: 1,
          stagger: 0.05,
          duration: 0.4,
          ease: "power2.out",
          clearProps: "all",
        });
      }
    },
    { dependencies: [loading, items], scope: containerRef }
  );

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card
            key={i}
            className="h-[220px] flex flex-col border-none shadow-sm"
          >
            <CardHeader>
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-1/2 mt-2" />
            </CardHeader>
            <CardContent className="flex-1">
              <Skeleton className="h-20 w-full" />
            </CardContent>
            <CardFooter>
              <Skeleton className="h-8 w-full" />
            </CardFooter>
          </Card>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="col-span-full py-20 text-center bg-slate-50 dark:bg-zinc-900 rounded-lg border border-dashed">
        <Briefcase className="mx-auto h-10 w-10 text-muted-foreground opacity-50 mb-3" />
        <h3 className="text-lg font-medium">Aucune opportunité trouvée</h3>
        <p className="text-muted-foreground text-sm">
          Essayez de modifier vos filtres de recherche.
        </p>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
    >
      {items.map((opp) => (
        <OpportuniteCard key={opp.id} data={opp}/>
      ))}
     
    </div>
  );
};


