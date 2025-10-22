import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput = ({ onSend, disabled }: ChatInputProps) => {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end">
      <div className="flex-1 relative">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Rumi about your analytics data..."
          disabled={disabled}
          className="min-h-[56px] max-h-[200px] resize-none rounded-[20px] border-border/60 bg-card shadow-[0_2px_8px_rgba(0,_0,_0,_0.06)] focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:border-primary transition-all px-5 py-4 text-[15px]"
          rows={1}
        />
      </div>
      <Button
        type="submit"
        size="icon"
        disabled={!message.trim() || disabled}
        className="h-[56px] w-[56px] flex-shrink-0 rounded-full shadow-[0_4px_12px_rgba(33,_150,_243,_0.3)] hover:shadow-[0_6px_16px_rgba(33,_150,_243,_0.4)] transition-all"
      >
        <Send className="h-5 w-5" />
      </Button>
    </form>
  );
};
