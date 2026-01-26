import {
  InternalNavProvider,
  useInternalNav,
} from "@/contexts/internal-nav-context";
import { PostContent } from "./post-content";
import { Button } from "@/components/ui/button";
import FormCreatePost from "./post-create";
import { InternalNavigator } from "@/components/internal-navigator";
import { Separator } from "@/components/ui/separator";
import { IconReload } from "@tabler/icons-react";
import { useQueryClient } from "@tanstack/react-query";

const FeedsContent = () => {
  const query = useQueryClient();
  const { push } = useInternalNav();
  const handleReload = () => {
    query.resetQueries({ queryKey: ["posts"] });
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-between">
        <Button onClick={handleReload} aria-label="recharger" variant={"ghost"}>
          <IconReload />
          Recharger
        </Button>
        <Button
          onClick={() => {
            push(FormCreatePost, "Poster", {
              content: "Hello world",
            });
          }}
        >
          Poster
        </Button>
      </div>
      <Separator />
      <PostContent />
    </div>
  );
};

function FeedsMainContent() {
  return (
    <InternalNavProvider initialPage={FeedsContent} initialTitle="Actualités">
      <InternalNavigator />
    </InternalNavProvider>
  );
}
export default FeedsMainContent;
