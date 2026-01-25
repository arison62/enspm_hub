import {
  LogOut,
  Settings,
  User,
  Bell,
  AlignEndHorizontal
} from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/stores/authStore";
import { Link } from "@inertiajs/react";
import { getAvatarFallback } from "@/lib/utils";


export function NavUser() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout)

  if (!user) {
    return null;
  }
  const isAdmin = user.role_systeme === "admin_site" || user.role_systeme === "super_admin";
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        asChild
        className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
      >
        <Avatar className="h-8 w-8">
          <AvatarImage
            src={user.profil.photo_profil ?? ""}
            alt={user.profil.nom_complet}
          />
          <AvatarFallback className="rounded-lg bg-primary text-white">
            {getAvatarFallback(user.profil.nom_complet)}
          </AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
        side="bottom"
        align="end"
        sideOffset={4}
      >
        <DropdownMenuLabel className="p-0 font-normal">
          <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
            <Avatar className="h-8 w-8">
              <AvatarImage
                src={user.profil.photo_profil ?? ""}
                alt={user.profil.nom_complet}
              />
              <AvatarFallback className="rounded-lg bg-primary text-white">
                {getAvatarFallback(user.profil.nom_complet)}
              </AvatarFallback>
            </Avatar>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium">
                {user.profil.nom_complet}
              </span>
              <span className="text-muted-foreground truncate text-xs">
                {user.email}
              </span>
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem>
            <User />
            <Link href={`/profile/${user.profil.slug}`}>Mon profile</Link>
          </DropdownMenuItem>
          {isAdmin && (
            <DropdownMenuItem>
              <AlignEndHorizontal />
              <a href="/admin">Administration</a>
            </DropdownMenuItem>
          )}
          <DropdownMenuItem>
            <Bell />
            Notifications
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Settings />
            Parametres
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={logout}>
          <LogOut />
          Deconnexion
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
