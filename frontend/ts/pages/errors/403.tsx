// frontend/ts/pages/errors/403.tsx

import ErrorLayout from "@/components/layouts/error-layout";
import { Button } from "@/components/ui/button";
import { Link } from "@inertiajs/react";
import { Lock } from "lucide-react";

export default function Forbidden() {
  return (
    <ErrorLayout title="403 - Accès interdit">
      <div className="space-y-6">
        <div className="flex justify-center">
          <div className="size-24 rounded-full bg-destructive/10 flex items-center justify-center">
            <Lock className="size-12 text-destructive" />
          </div>
        </div>

        <h1 className="text-6xl font-bold text-foreground">403</h1>
        <h2 className="text-2xl font-semibold text-foreground">
          Accès interdit
        </h2>
        <p className="text-muted-foreground">
          Vous n'avez pas les permissions nécessaires pour accéder à cette page.
        </p>

        <div className="flex flex-col gap-4">
          <Button asChild variant="default" size="lg">
            <Link href="/feeds">Retour à l'accueil</Link>
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={() => window.history.back()}
          >
            Retour en arrière
          </Button>
        </div>
      </div>
    </ErrorLayout>
  );
}
