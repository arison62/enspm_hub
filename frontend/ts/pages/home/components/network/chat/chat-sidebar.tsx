import { Search, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { InfiniteScroll } from "./message-infinite-list";
import type { ChatConversationUI } from "@/types/network";
import { getAvatarFallback } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";

interface ChatSidebarProps {
  chats: ChatConversationUI[];
  selectedId?: string | number;
  onSelectChat: (chat: ChatConversationUI) => void;
  convTab: "dm" | "groups";
  onChangeConvTab: (tab: "dm" | "groups") => void;
  onSearch: (query: string) => void;
  getCurrentData: (typ: "dm" | "group") => {
    isPending: boolean;
    allItemsCount: number | null | undefined;
    currentItemsLength: number;
    loadMore: () => void;
  };
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  chats,
  convTab,
  selectedId,
  onSearch,
  onSelectChat,
  onChangeConvTab,
  getCurrentData,
}) => {
  const renderChatList = (type: "dm" | "group") => {
    const { isPending, allItemsCount, currentItemsLength, loadMore } =
      getCurrentData(type);
    const data = chats.filter((chat) => chat.type === type);

    return (
      <InfiniteScroll
        reverse={false} // ← important : on charge vers le bas
        isPending={isPending}
        currentItemsLength={currentItemsLength}
        allItemsCount={allItemsCount}
        loadMore={() => loadMore()}
        className="overflow-y-auto max-h-[calc(100vh-280px]"
      >
        {data.map((chat) => (
          <div
            key={chat.id}
            onClick={() => onSelectChat(chat)}
            className={`p-4 cursor-pointer hover:bg-accent/50 transition-colors ${
              selectedId === chat.id ? "bg-accent" : ""
            }`}
          >
            <div className="flex items-start gap-3">
              <div className="relative flex-shrink-0">
                <Avatar className="h-12 w-12">
                  <AvatarImage src={chat.avatar || undefined} />
                  <AvatarFallback>
                    {getAvatarFallback(chat.name)}
                  </AvatarFallback>
                </Avatar>
                {chat.online && (
                  <span className="absolute bottom-0 right-0 h-3 w-3 bg-green-500 rounded-full border-2 border-background" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-medium truncate text-sm">{chat.name}</h3>
                  <span className="text-xs text-muted-foreground">
                    {chat.time}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground truncate flex-1">
                    {chat.lastMessage}
                  </p>
                  {chat.unread > 0 && (
                    <Badge className="ml-2 h-5 w-5 p-0 flex items-center justify-center rounded-full bg-green-500">
                      {chat.unread}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Loader pendant le chargement de la page suivante */}
        {isPending && (
          <div className="p-4 text-center text-muted-foreground text-sm">
            <Spinner />
          </div>
        )}
      </InfiniteScroll>
    );
  };

  return (
    <div className="flex flex-col h-full border-r bg-background">
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">Messages</h1>
          <Button variant="ghost" size="icon">
            <Plus className="h-5 w-5" />
          </Button>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher..."
            className="pl-9 bg-secondary/50"
            onChange={(e) => onSearch(e.target.value)}
          />
        </div>
      </div>
      <Tabs
        value={convTab}
        onValueChange={(value) => onChangeConvTab(value as "dm" | "groups")}
        className="flex-1"
      >
        <TabsList className="w-full justify-start px-4 bg-transparent border-b rounded-none h-12">
          <TabsTrigger value="dm" className="flex-1">
            Direct
          </TabsTrigger>
          <TabsTrigger value="groups" className="flex-1">
            Groupes
          </TabsTrigger>
        </TabsList>
        <TabsContent value="dm" className="m-0">
          {renderChatList("dm")}
        </TabsContent>
        <TabsContent value="groups" className="m-0">
          {renderChatList("group")}
        </TabsContent>
      </Tabs>
    </div>
  );
};
