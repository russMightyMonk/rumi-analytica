import { cn } from "@/lib/utils";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

export const ChatMessage = ({ role, content }: ChatMessageProps) => {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex w-full gap-4 py-4 px-2 animate-in fade-in-50 slide-in-from-bottom-2 duration-500",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-semibold text-sm shadow-md">
          R
        </div>
      )}
      <div
        className={cn(
          "max-w-[75%] rounded-3xl px-5 py-3.5 transition-all duration-300",
          isUser
            ? "bg-primary text-primary-foreground shadow-[0_2px_8px_rgba(33,_150,_243,_0.2)]"
            : "bg-card text-card-foreground shadow-[0_2px_8px_rgba(0,_0,_0,_0.06)]"
        )}
      >
        <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{content}</p>
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-9 h-9 rounded-full bg-secondary flex items-center justify-center text-secondary-foreground font-semibold text-sm shadow-md">
          U
        </div>
      )}
    </div>
  );
};
