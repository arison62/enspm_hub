// frontend/ts/components/layouts/app-layout.tsx
import { type ReactNode, useEffect, useRef } from "react";
import { Link, router } from "@inertiajs/react";
import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";
import {
  Home,
  Briefcase,
  MessageSquare,
  Menu,
  GraduationCap,
  Users2,
} from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import enspmLogo from "@/assets/enspm-logo.png";
import { useAuthStore } from "@/stores/authStore";
import BottomNavigationBarMobile from "../bottom-navigation-bar-mobile";
import DesktopNavLinks from "@/components/desktop-nav-links";
import GlobalSearch from "@/components/global-search";
import { NavUser } from "@/components/nav-user";
import { getAvatarFallback } from "@/lib/utils";

gsap.registerPlugin(useGSAP);

const NAVIGATION_ITEMS = [
  {
    icon: Home,
    label: "Accueil",
    href: "/feeds",
    badge: false,
  },
  {
    icon: Users2,
    label: "Réseau",
    href: "/network",
    badge: false,
  },
  {
    icon: Briefcase,
    label: "Opportunités",
    href: "/opportunities",
    badge: false,
  },
  {
    icon: MessageSquare,
    label: "Messages",
    href: "/chat",
    badge: false,
  },
  {
    icon: GraduationCap,
    label: "Stages",
    href: "/internships",
    badge: false,
  },
];

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { user } = useAuthStore();
  const isAuthenticated = user !== null;

  const containerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!isAuthenticated) {
      router.visit("/login");
    }
  }, [isAuthenticated]);

  useGSAP(() => {
    gsap.from(containerRef.current, {
      opacity: 0,
      y: 20,
      duration: 0.6,
      ease: "power2.out",
    });
  }, []);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between px-1">
          {/* Logo */}
          <Link
            href="/feeds"
            className="flex items-center gap-2 font-bold text-lg"
          >
            <div className="flex size-8 items-center justify-center rounded-md">
              <img src={enspmLogo} alt="" />
            </div>
            <span>
              ENSPM <span className="text-primary">Hub</span>
            </span>
          </Link>

          {/* Desktop Actions */}
          <GlobalSearch />
          <DesktopNavLinks
            items={NAVIGATION_ITEMS}
            className="hidden lg:flex"
          />

          {/* User Menu */}
          <div className="flex items-center gap-3">
            <NavUser />

            {/* Tablet Menu */}
            <Sheet>
              <SheetTrigger
                asChild
                className="max-sm:hidden max-lg:block lg:hidden"
              >
                <Button variant="ghost" size="icon">
                  <Menu className="size-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <div className="flex flex-col gap-6 mt-8">
                  <Link
                    href={`/profile/${user?.profil?.slug}`}
                    className="flex items-center gap-3 text-lg"
                  >
                    <Avatar className="size-10">
                      <AvatarImage
                        src={user?.profil?.photo_profil || undefined}
                      />
                      <AvatarFallback>
                         {getAvatarFallback(user?.profil.nom_complet)}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{user?.profil?.nom_complet}</p>
                      <p className="text-sm text-muted-foreground">
                        {user?.email}
                      </p>
                    </div>
                  </Link>
                  <Separator />
                  <nav className="flex flex-col gap-4 px-4">
                    {NAVIGATION_ITEMS.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className="flex items-center gap-3 text-muted-foreground hover:text-foreground"
                      >
                        <item.icon className="size-5" />
                        {item.label}
                      </Link>
                    ))}
                  </nav>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main
        ref={containerRef}
        className="flex-1 container max-w-8xl mx-auto"
      >
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="sm:hidden sticky bottom-0 z-50 border-t bg-background/95 backdrop-blur">
        <BottomNavigationBarMobile items={NAVIGATION_ITEMS} />
      </nav>
    </div>
  );
}
