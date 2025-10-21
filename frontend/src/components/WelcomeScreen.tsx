import { MessageSquare, TrendingUp, Zap, Brain } from "lucide-react";

const features = [
  {
    icon: MessageSquare,
    title: "Natural Language Queries",
    description: "Ask questions about your analytics in plain English",
  },
  {
    icon: TrendingUp,
    title: "Real-time Insights",
    description: "Get instant answers powered by Google Analytics data",
  },
  {
    icon: Zap,
    title: "AI-Powered Analysis",
    description: "Leverage Gemini for intelligent data interpretation",
  },
  {
    icon: Brain,
    title: "Multi-Agent Intelligence",
    description: "Advanced analytics through collaborative AI agents",
  },
];

export const WelcomeScreen = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center animate-in fade-in-50 duration-700">
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent animate-in slide-in-from-bottom-4 duration-700">
            Welcome to Rumi-Analytica
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto animate-in slide-in-from-bottom-5 duration-700 delay-100">
            Your intelligent analytics companion. Ask questions, get insights, and make data-driven decisions with ease.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12 animate-in slide-in-from-bottom-6 duration-700 delay-200">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-card border border-border rounded-xl p-6 hover:shadow-lg transition-all hover:scale-105 group"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gradient-to-br from-primary/10 to-accent/10 rounded-lg group-hover:from-primary/20 group-hover:to-accent/20 transition-colors">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <div className="text-left flex-1">
                  <h3 className="font-semibold text-foreground mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 p-6 bg-gradient-to-r from-primary/5 to-accent/5 rounded-xl border border-primary/20 animate-in slide-in-from-bottom-7 duration-700 delay-300">
          <p className="text-sm text-muted-foreground">
            💡 <span className="font-semibold">Pro tip:</span> Try asking "What was my traffic last month?" or "Show me top performing pages"
          </p>
        </div>
      </div>
    </div>
  );
};
