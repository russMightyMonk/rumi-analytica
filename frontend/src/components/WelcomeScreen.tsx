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
    <div className="flex flex-col items-center justify-center min-h-[65vh] px-6 text-center animate-in fade-in-50 duration-700">
      <div className="max-w-4xl mx-auto space-y-12">
        <div className="space-y-6">
          <h2 className="text-5xl md:text-6xl font-semibold tracking-tight text-foreground animate-in slide-in-from-bottom-4 duration-700">
            Welcome to Rumi-Analytica
          </h2>
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto animate-in slide-in-from-bottom-5 duration-700 delay-100 font-light">
            Your intelligent analytics companion. Ask questions, get insights, and make data-driven decisions with ease.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-16 animate-in slide-in-from-bottom-6 duration-700 delay-200">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-card rounded-[24px] p-8 hover:shadow-[0_10px_30px_rgba(0,_0,_0,_0.08)] transition-all duration-500 hover:scale-[1.02] group"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start gap-5">
                <div className="p-4 bg-gradient-to-br from-primary/10 to-accent/10 rounded-2xl group-hover:from-primary/15 group-hover:to-accent/15 transition-colors duration-300">
                  <feature.icon className="h-7 w-7 text-primary" />
                </div>
                <div className="text-left flex-1">
                  <h3 className="font-semibold text-lg text-foreground mb-2.5">
                    {feature.title}
                  </h3>
                  <p className="text-[15px] text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-16 p-6 bg-muted/50 rounded-[20px] animate-in slide-in-from-bottom-7 duration-700 delay-300">
          <p className="text-[15px] text-muted-foreground">
            💡 <span className="font-semibold text-foreground">Pro tip:</span> Try asking "What was my traffic last month?" or "Show me top performing pages"
          </p>
        </div>
      </div>
    </div>
  );
};
