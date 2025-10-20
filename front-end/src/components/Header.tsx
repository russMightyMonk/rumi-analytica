import rumiLogo from "@/assets/rumi-logo.png";
import { BarChart3 } from "lucide-react";

export const Header = () => {
  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src={rumiLogo} alt="Rumi-Analytica Logo" className="h-12 w-auto" />
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Rumi-Analytica
            </h1>
            <p className="text-xs text-muted-foreground">
              Rumi's Unicorn Makes Insights
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <BarChart3 className="h-5 w-5 text-accent" />
          <span className="text-sm font-medium hidden sm:inline">Analytics Assistant</span>
        </div>
      </div>
    </header>
  );
};
