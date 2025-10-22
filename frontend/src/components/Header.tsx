import rumiLogo from "@/assets/rumi-logo.png";
import { BarChart3, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

export const Header = () => {
  const { logout, username } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="border-b border-border/50 bg-card/80 backdrop-blur-xl sticky top-0 z-50 shadow-[0_1px_3px_rgba(0,_0,_0,_0.05)]">
      <div className="container mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <img src={rumiLogo} alt="Rumi-Analytica Logo" className="h-11 w-auto" />
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-foreground">
              Rumi-Analytica
            </h1>
            <p className="text-xs text-muted-foreground font-medium">
              Rumi's Unicorn Makes Insights
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2.5 px-4 py-2 rounded-full bg-muted">
            <BarChart3 className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium text-foreground">{username}</span>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleLogout}
            className="rounded-full hover:bg-muted"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </div>
    </header>
  );
};
