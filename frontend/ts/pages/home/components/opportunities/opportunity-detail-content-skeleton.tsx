import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

export default function OpportunityDetailContentSkeleton() {
  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Colonne principale (8/12) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Hero Section Skeleton */}
          <Card className="border shadow-sm">
            <CardHeader className="pb-4">
              <div className="flex flex-col md:flex-row gap-6">
                {/* Logo Skeleton */}
                <Skeleton className="bg-muted rounded-lg h-24 w-24 flex-shrink-0" />

                {/* Titre et informations Skeleton */}
                <div className="flex-1">
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div className="flex-1">
                      <Skeleton className="h-9 w-3/4 mb-2" />
                      <div className="text-muted-foreground mt-2 flex flex-wrap items-center gap-2">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-4 w-48" />
                      </div>
                    </div>

                    {/* Actions Skeleton */}
                    <div className="flex flex-wrap gap-3">
                      <Skeleton className="h-10 w-32 rounded-md" />
                      <Skeleton className="h-10 w-10 rounded-md" />
                    </div>
                  </div>

                  {/* Métadonnées Skeleton */}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-4">
                    <Skeleton className="h-6 w-32 rounded-full" />
                    <Skeleton className="h-6 w-24 rounded-full" />
                  </div>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Métadonnées et expiration Skeleton */}
          <Card className="border shadow-sm">
            <CardContent className="pt-0">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Skeleton className="h-20 rounded-lg" />
                <Skeleton className="h-20 rounded-lg" />
                <Skeleton className="h-20 rounded-lg" />
                <Skeleton className="h-20 rounded-lg" />
              </div>
            </CardContent>
            {/* Expiration Alert Skeleton */}
            <div className="mt-6 p-4 border rounded-md">
              <div className="flex items-center gap-2">
                <Skeleton className="h-4 w-4 rounded-full" />
                <Skeleton className="h-5 w-24" />
              </div>
              <Skeleton className="h-4 w-full mt-2" />
            </div>
          </Card>

          {/* Description avec onglets Skeleton */}
          <Card className="border shadow-sm">
            <CardHeader>
              <div className="flex gap-4">
                <Skeleton className="h-8 w-24 rounded-md" />
                <Skeleton className="h-8 w-24 rounded-md" />
                <Skeleton className="h-8 w-24 rounded-md" />
              </div>
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-2/3" />
            </CardContent>
          </Card>
        </div>

        {/* Sidebar (4/12) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Carte du recruteur Skeleton */}
          <Card className="border shadow-sm">
            <CardHeader>
              <Skeleton className="h-4 w-32" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Skeleton className="h-14 w-14 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-5 w-48 mb-1" />
                  <Skeleton className="h-4 w-32 mb-1" />
                  <Skeleton className="h-4 w-64" />
                </div>
              </div>
              <div className="pt-3 border-t">
                <Skeleton className="h-4 w-full" />
              </div>
              <div className="flex items-center max-w-xs gap-2 pt-2">
                <Skeleton className="h-8 w-32 rounded-md" />
              </div>
            </CardContent>
          </Card>

          {/* Carte de l'entreprise Skeleton */}
          <Card className="border shadow-sm">
            <CardHeader>
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <Skeleton className="h-12 w-12 rounded-lg" />
                <div className="flex-1">
                  <Skeleton className="h-5 w-40 mb-1" />
                  <Skeleton className="h-4 w-32" />
                </div>
              </div>
              <Skeleton className="h-4 w-full mb-1" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-10 w-full rounded-md" />
            </CardContent>
          </Card>

          {/* Actions Skeleton */}
          <Card className="border shadow-sm">
            <CardHeader>
              <Skeleton className="h-6 w-24" />
            </CardHeader>
            <CardContent className="space-y-3 flex flex-col">
              <Skeleton className="h-10 w-full max-w-xs rounded-md" />
              <Skeleton className="h-10 w-full max-w-xs rounded-md" />
              <Skeleton className="h-10 w-full max-w-xs rounded-md" />
              <div className="mt-4 pt-4 border-t space-y-2">
                <Skeleton className="h-10 w-full rounded-md" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
            </CardContent>
          </Card>

          {/* Opportunités similaires Skeleton */}
          <Card className="border shadow-sm">
            <CardHeader>
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="flex gap-3 pb-3 border-b last:border-0 last:pb-0"
                  >
                    <Skeleton className="w-10 h-10 rounded" />
                    <div className="flex-1">
                      <Skeleton className="h-4 w-48 mb-1" />
                      <Skeleton className="h-3 w-32 mb-1" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="link"
                className="w-full mt-4 justify-center text-sm font-medium p-0 h-auto"
                disabled
              >
                <Skeleton className="h-4 w-48" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
