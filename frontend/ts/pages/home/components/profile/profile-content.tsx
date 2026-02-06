import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProfileHeader } from "./profile-header";
import { ProfileSidebar } from "./profile-sidebar";
import { useAuthStore } from "@/stores/authStore";
import type { UserComplete } from "@/types/user";
import ExperiencesTab from "./experiences-tab-content";

export const ProfileContent = ({ user }: { user: UserComplete }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const isOwner = useAuthStore((state) => state.user?.id == user.id);
  const profil = user.profil;

  useGSAP(
    () => {
      gsap.from(".animate-fade", {
        opacity: 0,
        y: 20,
        stagger: 0.1,
        duration: 0.8,
        ease: "power3.out",
      });
    },
    { scope: containerRef }
  );

  return (
    <div ref={containerRef} className="bg-background pb-12">
      <ProfileHeader profil={profil} isOwner={isOwner}/>

      <div className="container mx-auto px-4 mt-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <ProfileSidebar profil={profil} />

          <div className="lg:col-span-8 animate-fade">
            <Tabs defaultValue="experiences" className="w-full">
              <TabsList className="w-full md:w-fit inline-flex justify-start bg-transparent border-b rounded-none h-auto p-0 gap-6">
                <TabsTrigger
                  value="experiences"
                  className="data-[state=active]:border-primary border-b-2 border-transparent rounded-none shadow-none py-2"
                >
                  Expériences
                </TabsTrigger>
                <TabsTrigger
                  value="education"
                  className="data-[state=active]:border-primary border-b-2 border-transparent rounded-none shadow-none py-2"
                >
                  Éducation
                </TabsTrigger>
              </TabsList>

              <TabsContent value="experiences" className="mt-6">
                <ExperiencesTab experiences={user.profil.experiences} isOwnProfile={isOwner} />
              </TabsContent>
              {/* Autres TabsContent... */}
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};
