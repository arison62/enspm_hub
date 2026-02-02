// frontend/ts/pages/errors/404.tsx

import ErrorLayout from "@/components/layouts/error-layout";
import { Button } from "@/components/ui/button";
import { Link } from "@inertiajs/react";
import { Home } from "lucide-react";

export default function NotFound() {
  return (
    <ErrorLayout title="404 - Page non trouvée">
      <div className="space-y-6">
        <h1 className="text-8xl font-bold text-primary">404</h1>
        <h2 className="text-2xl font-semibold text-foreground">
          Oups ! Page introuvable
        </h2>
        <p className="text-muted-foreground">
          La page que vous recherchez semble ne pas exister ou a été déplacée.
        </p>

        <Button asChild size="lg" className="mt-6">
          <Link href="/feeds">
            <Home className="mr-2 size-4" />
            Retour à l'accueil
          </Link>
        </Button>
      </div>
    </ErrorLayout>
  );
}
