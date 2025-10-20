import { useState } from "react";
import { Header } from "@/components/Header";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = { role: "user", content };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Placeholder for backend integration
      // This will be replaced with actual API call to FastAPI backend or Lovable Cloud Edge Function
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const assistantMessage: Message = {
        role: "assistant",
        content:
          "I'm ready to help you analyze your Google Analytics data! However, the backend integration is not yet configured. Please connect the FastAPI backend or set up Lovable Cloud Edge Functions to enable full functionality.",
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header />

      <div className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1">
          <div className="container mx-auto px-4 py-6">
            {messages.length === 0 ? (
              <WelcomeScreen />
            ) : (
              <div className="space-y-4 max-w-4xl mx-auto">
                {messages.map((message, index) => (
                  <ChatMessage
                    key={index}
                    role={message.role}
                    content={message.content}
                  />
                ))}
                {isLoading && (
                  <div className="flex justify-start gap-3 p-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-sm">
                      R
                    </div>
                    <div className="bg-card border border-border rounded-2xl px-4 py-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="border-t border-border bg-card/50 backdrop-blur-sm">
          <div className="container mx-auto px-4 py-4 max-w-4xl">
            <ChatInput onSend={handleSendMessage} disabled={isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
