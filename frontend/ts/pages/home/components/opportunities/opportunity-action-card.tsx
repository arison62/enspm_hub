import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Share2, LinkIcon, BookmarkPlusIcon, ViewIcon } from "lucide-react";
import type { OpportuniteAny } from "@/types/opportunities";

type OpportunityCommonProps = {
  opportunity: OpportuniteAny;
};

export const OpportunityActionsCard = ({
  opportunity,
  isOwner = false,
}: OpportunityCommonProps & { isOwner?: boolean }) => {
  const handleShare = async () => {
    console.log("share")
    try {
      const isShared = navigator.canShare();
      if (!isShared) return;
      const desciption = opportunity.description;
      const descriptionSanitized = desciption.replace(/<[^>]+>/g, "");
      console.log("share", descriptionSanitized);
      await navigator.share({
        title: opportunity.titre,
        text: descriptionSanitized.slice(0, 100),
        url: window.location.href,
      });
    } catch (error) {
      console.error(error);
    }
  };
  return (
    <Card className="border shadow-sm">
      <CardHeader>
        <CardTitle>Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 flex flex-col">
        <Button
          className="w-full max-w-xs"
          variant="outline"
          onClick={handleShare}
        >
          <Share2 className="mr-2 h-4 w-4" />
          Partager l'opportunité
        </Button>

        {opportunity &&
          "lien_offre_original" in opportunity &&
          opportunity.lien_offre_original && (
            <Button className="w-full max-w-xs" variant="outline" asChild>
              <a
                href={opportunity.lien_offre_original}
                target="_blank"
                rel="noopener noreferrer"
              >
                <LinkIcon className="mr-2 h-4 w-4" />
                Voir l'offre originale
              </a>
            </Button>
          )}
        {opportunity &&
          "lien_inscription" in opportunity &&
          opportunity.lien_inscription && (
            <Button className="w-full max-w-xs" variant="outline" asChild>
              <a
                href={opportunity.lien_inscription}
                target="_blank"
                rel="noopener noreferrer"
              >
                <BookmarkPlusIcon className="mr-2 h-4 w-4" />
                S'inscrire
              </a>
            </Button>
          )}
        {opportunity &&
          "lien_formation" in opportunity &&
          opportunity.lien_formation && (
            <Button className="w-full max-w-xs" variant="outline" asChild>
              <a
                href={opportunity.lien_formation}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ViewIcon className="mr-2 h-4 w-4" />
                Voir la formation
              </a>
            </Button>
          )}
        {isOwner && (
          <div className="mt-4 pt-4 border-t space-y-2 space-x-2">
            <Button className="w-full max-w-xs" variant="secondary">
              Modifier l'offre
            </Button>
            <Button className="w-full max-w-xs" variant="destructive">
              Supprimer l'offre
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
