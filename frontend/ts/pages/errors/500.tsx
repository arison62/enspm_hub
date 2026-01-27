// frontend/ts/pages/errors/500.tsx

import ErrorLayout from "@/components/layouts/error-layout";
import { Button } from "@/components/ui/button";
import { Link } from "@inertiajs/react";
import { AlertCircle, RefreshCw } from "lucide-react";

export default function ServerError() {
  return (
    <ErrorLayout title="500 - Erreur serveur">
      <div className="space-y-6">
        <div className="flex justify-center">
          <div className="size-24 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertCircle className="size-12 text-destructive" />
          </div>
        </div>

        <h1 className="text-6xl font-bold text-foreground">500</h1>
        <h2 className="text-2xl font-semibold text-foreground">
          Erreur interne du serveur
        </h2>
        <p className="text-muted-foreground">
          Quelque chose s'est mal passé de notre côté. Nous travaillons pour
          résoudre le problème.
        </p>

        <div className="flex flex-col gap-4">
          <Button size="lg" onClick={() => window.location.reload()}>
            <RefreshCw className="mr-2 size-4" />
            Réessayer
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/home">Retour à l'accueil</Link>
          </Button>
        </div>
      </div>
    </ErrorLayout>
  );
}
