"use client";
import { Button } from "@/components/ui/button"; 
import { Provider } from "@supabase/supabase-js";
import { Github, Google } from "lucide-react";
import { supabase } from "../../utils/supabase"; 

type OAuthProvider = {
  name: Provider;
  displayName: string;
  icon?: JSX.Element;
};

export function OAuthButtons() {
  const oAuthProviders: OAuthProvider[] = [
    {
      name: "github",
      displayName: "GitHub",
      icon: <Github className="size-5" />,
    },
    {
        name: "google", 
        displayName: "Google",
        icon: <Google className="size-5" />,
      },
  ];

  const handleOAuthSignIn = async (provider: Provider) => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: window.location.origin + '/auth/callback', // Redirect after auth
      },
    });

    if (error) {
      console.error("Error signing in with OAuth:", error);
      // Handle error, e.g., display an error message to the user.
    }
  };

  return (
    <>
      {oAuthProviders.map((provider) => (
        <Button
          key={provider.name}
          className="w-full flex items-center justify-center gap-2"
          variant="outline"
          onClick={() => handleOAuthSignIn(provider.name)}
        >
          {provider.icon}
          Login with {provider.displayName}
        </Button>
      ))}
    </>
  );
}