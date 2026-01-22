import AppLayout from "@/components/layouts/app-layout";
import type { ReactNode } from "react";
import { InternalNavigator } from "@/components/internal-navigator";
import { InternalNavProvider } from "@/contexts/internal-nav-context";
import InternshipsHome from "./pages/internships-home";

function InternshipsPage() {
  return (
    <InternalNavProvider initialPage={InternshipsHome} initialTitle="Stages">
      <InternalNavigator />
    </InternalNavProvider>
  );
}

InternshipsPage.layout = (page: ReactNode) => <AppLayout>{page}</AppLayout>;

export default InternshipsPage;
