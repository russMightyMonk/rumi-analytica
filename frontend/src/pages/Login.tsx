import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(username, password);
      navigate("/");
    } catch (error) {
      toast({
        title: "Authentication Failed",
        description: error instanceof Error ? error.message : "Please check your credentials",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <Card className="w-full max-w-md border-border/60 shadow-[0_10px_30px_rgba(0,_0,_0,_0.08)] rounded-[28px]">
        <CardHeader className="space-y-6 pt-10 pb-6">
          <div className="flex items-center justify-center">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-semibold text-3xl shadow-[0_4px_16px_rgba(33,_150,_243,_0.3)]">
              R
            </div>
          </div>
          <div className="space-y-2">
            <CardTitle className="text-3xl text-center font-semibold tracking-tight">Welcome to Rumi Analytica</CardTitle>
            <CardDescription className="text-center text-[15px]">
              Enter your credentials to access the analytics platform
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="pb-10">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2.5">
              <Label htmlFor="username" className="text-sm font-medium">Username</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
                placeholder="Enter your username"
                className="h-12 rounded-[16px] border-border/60 shadow-[0_2px_8px_rgba(0,_0,_0,_0.04)] focus-visible:ring-2 focus-visible:ring-primary/30 transition-all"
              />
            </div>
            <div className="space-y-2.5">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                placeholder="Enter your password"
                className="h-12 rounded-[16px] border-border/60 shadow-[0_2px_8px_rgba(0,_0,_0,_0.04)] focus-visible:ring-2 focus-visible:ring-primary/30 transition-all"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full h-12 rounded-[16px] text-[15px] font-medium shadow-[0_4px_12px_rgba(33,_150,_243,_0.3)] hover:shadow-[0_6px_16px_rgba(33,_150,_243,_0.4)] transition-all mt-6" 
              disabled={isLoading}
            >
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
