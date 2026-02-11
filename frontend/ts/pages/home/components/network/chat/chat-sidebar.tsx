import React from "react";
import { Search, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import type { ChatConversation } from "@/types/network";

interface ChatSidebarProps {
  chats: ChatConversation[];
  selectedId?: string | number;
  onSelectChat: (chat: ChatConversation) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  chats,
  selectedId,
  onSelectChat,
}) => {
  const renderChatList = (type: "dm" | "group") => (
    <ScrollArea className="h-[calc(100vh-180px)]">
      {" "}
      {/* Taille ajustée pour laisser place au header/tabs */}
      <div className="divide-y divide-border">
        {chats
          .filter((c) => c.type === type)
          .map((chat) => (
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
                      {chat.initials || chat.name.substring(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  {chat.online && (
                    <span className="absolute bottom-0 right-0 h-3 w-3 bg-green-500 rounded-full border-2 border-background" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-medium truncate text-sm">
                      {chat.name}
                    </h3>
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
      </div>
    </ScrollArea>
  );

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
          <Input placeholder="Rechercher..." className="pl-9 bg-secondary/50" />
        </div>
      </div>
      <Tabs defaultValue="dm" className="flex-1">
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
