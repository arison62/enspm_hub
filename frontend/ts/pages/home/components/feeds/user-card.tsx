import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { type ReactNode } from "react";

interface UserCardProps {
  user: {
    name?: string;
    headline?: string;
    photo_url?: string;
    avatarInitials?: string;
    posts?: number | string;
    views?: number | string;
    likes?: number | string;
    comments?: number | string;
  };
  alert?: ReactNode;
}

export function UserCard({ user = {}, alert }: UserCardProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      gsap.from(containerRef.current, {
        opacity: 0,
        y: 20,
        duration: 0.5,
        ease: "power2.out",
      });
    },
    { scope: containerRef },
  );

  return (
    <Card ref={containerRef} className="overflow-hidden shadow-sm border-none">
      <div className="h-16 bg-gradient-to-r from-blue-600 to-indigo-600" />
      <CardContent className="relative pt-0">
        <Avatar className="absolute top-[-2rem] left-4 size-16 border-4 border-white dark:border-zinc-900 shadow-sm">
          <AvatarFallback className="bg-blue-100 text-blue-700 font-bold">
            <AvatarImage src={user.photo_url} />
            {user.avatarInitials ?? "N/A"}
          </AvatarFallback>
        </Avatar>
        <div className="pt-10 space-y-1">
          <h2 className="font-bold text-base">{user.name ?? "N/A"}</h2>
          <p className="text-xs text-muted-foreground leading-tight">
            {user.headline ?? "N/A"}
          </p>
        </div>
        <Separator className="my-4" />
        {alert ? (
          <> {alert}</>
        ) : (
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Nombres posts</span>
              <span className="font-medium text-blue-600">
                {user.posts ?? "N/A"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Nombres likes</span>
              <span className="font-medium text-blue-600">
                {user.likes ?? "N/A"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Nombres vues</span>
              <span className="font-medium text-blue-600">
                {user.views ?? "N/A"}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
