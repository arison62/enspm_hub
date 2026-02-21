import AppLayout from "@/components/layouts/app-layout";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { getAvatarFallback } from "@/lib/utils";
import { ArrowLeft, MoreVertical } from "lucide-react";

import { ChatInput } from "../components/network/chat/chat-input";
import { ChatMessageList } from "../components/network/chat/chat-message-list";
import { ChatSidebar } from "../components/network/chat/chat-sidebar";
import { useChatPage } from "./hooks/use-chat-page";

// ============================================
// PAGE
// ============================================

export default function ChatPage() {
  const {
    selectedTab,
    setSelectedTab,
    selectedChat,
    setSelectedChat,
    selectedMessage,
    setSelectedMessage,
    conversations,
    messages,
    messagesPending,
    messagesTotalItems,
    handleSearchChange,
    loadMoreMessages,
    sendMessage,
    deleteMessage,
    getConversationPaginationData,
    conversationId,
  } = useChatPage();

  return (
    <div className="flex h-[calc(100vh-64px)] w-full overflow-hidden bg-background border">
      {/* Sidebar */}
      <div
        className={`${selectedChat ? "hidden lg:flex" : "flex"} w-full lg:w-80 flex-col`}
      >
        <ChatSidebar
          chats={conversations}
          onSearch={handleSearchChange}
          selectedId={selectedChat?.id}
          onSelectChat={setSelectedChat}
          getCurrentData={getConversationPaginationData}
          convTab={selectedTab}
          onChangeConvTab={setSelectedTab}
        />
      </div>

      {/* Main chat window */}
      <div
        className={`${!selectedChat ? "hidden lg:flex" : "flex"} flex-1 flex-col overflow-hidden`}
      >
        {selectedChat ? (
          <>
            {/* Fixed header */}
            <div className="h-16 flex items-center justify-between px-4 bg-background">
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="icon"
                  className="lg:hidden"
                  onClick={() => setSelectedChat(null)}
                >
                  <ArrowLeft />
                </Button>
                <Avatar>
                  <AvatarImage src={selectedChat.avatar ?? ""} />
                  <AvatarFallback>
                    {getAvatarFallback(selectedChat.name)}
                  </AvatarFallback>
                </Avatar>
                <h2 className="text-sm font-bold">{selectedChat.name}</h2>
              </div>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </div>

            {/* Scrollable message list */}
            <ChatMessageList
              messages={messages}
              onSelectMessageChange={setSelectedMessage}
              onLoadMore={loadMoreMessages}
              isPending={messagesPending}
              allItemsCount={messagesTotalItems}
              onDeleteMessage={deleteMessage}
              currentChatId={conversationId}
            />

            {/* Fixed input */}
            <ChatInput
              selectedMessage={selectedMessage}
              onSelectedMessageChange={setSelectedMessage}
              onSendMessage={(msg) =>
                sendMessage(msg.text || undefined, msg.media || undefined)
              }
            />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            Sélectionnez une discussion pour commencer
          </div>
        )}
      </div>
    </div>
  );
}

ChatPage.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>;
