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
import type { Post } from "@/types/feeds";
import { useState } from "react";
import type { Pagination } from "@/api/feeds";

const FeedsContent = () => {
  const query = useQueryClient();
  const { push } = useInternalNav();
  const [posts, setPost] = useState<Post[]>([]);
  const [pagination, setPagination] = useState<Pagination>({
    pageIndex: 1,
    pageSize: 2,
    totalItems: 0,
  })
  const handleReload = () => {
    query.invalidateQueries({ queryKey: ["posts"] });
    setPost([]);
    setPagination({
      pageIndex: 1,
      pageSize: 2,
      totalItems: 0
    })
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
      <PostContent 
      posts={posts}
      setPost={setPost} 
      pagination = {pagination}
      setPagination = {setPagination}
      />
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
