"use client";
import { Spinner } from "@/components/ui/spinner";
import React, { useCallback, useEffect, useLayoutEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { motion, type UseInViewOptions } from "motion/react";




interface InfiniteScrollCellProps extends React.ComponentPropsWithRef<"div"> {
  skelton?: React.ReactNode;
  amount?: UseInViewOptions["amount"];
}

export function InfiniteScrollCell({
  children,
  ...props
}: InfiniteScrollCellProps) {
  const ref = React.useRef<HTMLDivElement>(null);


  return (
    <div ref={ref} {...props}>
      
          <motion.div
            key="content"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ease: "easeOut" }}
          >
            {children}
          </motion.div>
      
    </div>
  );
}

interface InfiniteScrollProps extends React.ComponentPropsWithRef<"div"> {
  isPending: boolean;
  currentItemsLength: number;
  allItemsCount: number | null | undefined;
  loadMore: () => void;
  reverse?: boolean;
  isFirstLoad?: boolean;
}

export function InfiniteScroll({
  currentItemsLength,
  isPending,
  allItemsCount,
  loadMore,
  reverse = false,
  children,
  className,
  ...props
}: InfiniteScrollProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const observer = useRef<IntersectionObserver | null>(null);
  const prevScrollHeightRef = useRef(0);
  const isFirstLoad = useRef(true);

  // Correction de la logique hasMore : 
  // S'il n'y a pas encore de messages, on considère qu'il y en a potentiellement à charger.
  const hasMore = allItemsCount === undefined || allItemsCount === null
      ? true
      : currentItemsLength < allItemsCount;

  // Utilisation d'une Callback Ref au lieu d'un useEffect + useRef
  // Cela garantit que l'observer est attaché dès que le div entre dans le DOM
  const sentinelRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (observer.current) observer.current.disconnect();
    
      if (!node || isPending || !hasMore) return;

      observer.current = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && !isPending && hasMore) {
            console.log("Intersection détectée, loadMore lancé");
            if (containerRef.current && reverse) {
              prevScrollHeightRef.current = containerRef.current.scrollHeight;
            }
            loadMore();
          }
        },
        {
          root: containerRef.current,
          rootMargin: reverse ? "200px 0px 0px 0px" : "0px 0px 200px 0px",
          threshold: 0,
        }
      );
      observer.current.observe(node);
    },
    [isPending, hasMore, loadMore, reverse]
  );

  // Nettoyage de l'observer au démontage
  useEffect(() => {
    return () => observer.current?.disconnect();
  }, []);

  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container || !reverse) return;

    if (isFirstLoad.current && currentItemsLength > 0) {
      container.scrollTop = container.scrollHeight;
      isFirstLoad.current = false;
      return;
    }

    if (!isPending && prevScrollHeightRef.current > 0) {
      const heightDifference = container.scrollHeight - prevScrollHeightRef.current;
      if (heightDifference > 0) {
        container.scrollTop = heightDifference;
      }
      prevScrollHeightRef.current = 0;
    }
  }, [currentItemsLength, isPending, reverse]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "flex flex-1 flex-col overflow-y-auto [overflow-anchor:auto]",
        className
      )}
      {...props}
    >
      {/* 
         IMPORTANT : On rend le Sentinel même si hasMore est faux ? 
         Non, mais on s'assure que la condition hasMore est correcte.
      */}
      {reverse && hasMore && (
        <div
          ref={sentinelRef}
          className="flex justify-center py-4 [overflow-anchor:none] min-h-[20px]"
        >
          {isPending && <Spinner />}
        </div>
      )}

      <div className="flex flex-col gap-4">
        {children}
      </div>

      {!reverse && hasMore && (
        <div
          ref={sentinelRef}
          className="flex justify-center py-4 min-h-[20px]"
        >
          {isPending && <Spinner />}
        </div>
      )}
    </div>
  );
}